import re
from trello import TrelloClient
from trello.card import Card
from trello.trellolist import List
from trello.board import Board
from trello.organization import Organization
import requests
import traceback
import os

from datetime import datetime

from handlers.base import BaseHandler

class Handler(BaseHandler):

    name = 'Trello'

    prefix = 'trello'

    patterns = [
        (['(?P<command>desligar) (?P<users>.*)', '(?P<command>terminate) (?P<users>.*)', '{prefix} (?P<command>terminate) (?P<users>.*)'], 'Desliga um funcionário'),
    ]

    def __init__(self, bot, slack, api_key=None, api_secret=None, oauth_token=None, oauth_secret=None):

        super().__init__(bot, slack)

        self.directed = True

        if not api_key:
            api_key = os.environ.get('TRELLO_API_KEY')
        if not api_secret:
            api_secret = os.environ.get('TRELLO_API_SECRET')
        if not oauth_token:
            oauth_token = os.environ.get('TRELLO_OAUTH_TOKEN')
        if not oauth_secret:
            oauth_secret = os.environ.get('TRELLO_OAUTH_SECRET')

        self.client = TrelloClient(api_key=api_key, api_secret=api_secret,
                token=oauth_token, token_secret=oauth_secret)

        self.org_name = os.environ.get('TRELLO_ORGANIZATION', 'pagarmeoficial')

        self.org_id = self.get_org_id(self.org_name)

        self.org = self.client.get_organization(self.org_id)

        self.set_job_status('Initialized')

    def get_org_id(self, name):
        orgs = self.client.list_organizations()
        for org in orgs:
            if org.name == name:
                return org.id


    def process(self, channel, user, ts, message, at_bot, command, **kwargs):
        if at_bot:
            if command in ['desligar', 'terminate']:
                user_handle = self.get_user_handle(user)
                self.log('@{}: {}'.format(user_handle, message))

                self.set_job_status('Processing')

                if not self.authorized(user_handle, 'Terminator'):
                    self.set_job_status('Unauthorized')
                    self.post_message(channel=channel, text='@{} Unauthorized'.format(user_handle))
                    return False


                to_remove = [x for x in kwargs['users'].split() if '@' not in x]

                for r in to_remove:
                    try:
                        c = self.bot.get_config('alias_reverse', r)
                        if c:
                            if c not in to_remove:
                                to_remove.append(c)
                    except:
                        continue

                for r in to_remove:
                    try:
                        c = self.bot.get_config('alias', r).split()
                        for x in c:
                            if x not in to_remove:
                                to_remove.append(x)
                    except:
                        continue

                print(to_remove)
                if len(to_remove) == 0:
                    self.log('No valid usernames')
                    self.set_job_status('Finished')
                    return


                self.post_message(channel=channel, text='@{} Removendo usuários: {}'.format(user_handle, ', '.join(to_remove)))

                all_boards = self.org.get_boards({'fields': 'id'})
                members = {board.id: board.all_members() for board in all_boards}

                members_username = {board.id: [x.username for x in members[board.id]] for board in all_boards}


                for username in to_remove:
                    response = '@{} User {} not found at any boards'.format(user_handle, username)
                    removed = False
                    removed_boards = []

                    m = None
                    for mm in members:
                        if isinstance(members[mm], list):
                            for member in members[mm]:
                                if member.username == username:
                                    m = member
                                    break
                        else:
                            if members[mm].username == username:
                                m = mm
                                break

                    if m == None:
                        self.log('User {} doesn\'t exists'.format(username))
                        continue

                    try:
                        self.client.fetch_json('/organizations/{}/members/{}'.format(self.org_id, m.id), http_method='DELETE')
                    except:
                        traceback.print_exc()

                    for board in all_boards:
                        if username in members_username[board.id]:
                            try:
                                self.log('Found {} at board {}'.format(username, board.name))
                                removed = True
                                removed_boards.append('"{}"'.format(board.name))
                                board.remove_member(m)
                                self.log('User {} removed from board {}'.format(username, board.name))
                            except:
                                self.post_message(channel, 'Failed to remove {} from board {}'.format(username, board.name))
                                self.log(traceback.format_exc())

                    if removed:
                        response = '@{} User {} removed from boards {}'.format(user_handle, username, ', '.join(removed_boards))

                    if response:
                        self.post_message(channel, response)
                    else:
                        self.log('User {} not found in any boards'.format(username))
                        self.post_message(channel, '@{} User {} not found in any boards'.format(user_handle, username))

            self.set_job_status('Finished')
            self.set_job_end(datetime.now())
