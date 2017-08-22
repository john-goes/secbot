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

    name = 'Trello Terminator'

    patterns = [
        'desligar .*',
        'terminate .*'
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


    def process(self, channel, user, ts, message, at_bot, extra=None):
        if at_bot:
            self.set_job_status('Processing')

            user_handle = self.get_user_handle(user)
            self.log('@{}: {}'.format(user_handle, message))

            to_remove = [x for x in message.replace('desligar ', '').replace('terminate ', '').split() if '@' not in x]

            if len(to_remove) == 0:
                self.log('No valid usernames')
                self.set_job_status('Finished')
                return


            if not self.authorized(user_handle, 'Terminator'):
                self.set_job_status('Unauthorized')
                self.post_message(channel=channel, text='@{} Unauthorized'.format(user_handle))
                return False

            self.post_message(channel=channel, text='@{} Removendo usuários: {}'.format(user_handle, ', '.join(to_remove)))

            all_boards = self.org.get_boards({'fields': 'id'})
            members = {board.id: board.all_members() for board in all_boards}

            members_username = {board.id: [x.username for x in members[board.id]] for board in all_boards}

            for username in to_remove:
                if '@' in username:
                    continue
                response = '@{} User {} not found at any boards'.format(user_handle, username)
                removed = False
                removed_boards = []

                m = None
                for mm in members:
                    if members[mm].username == username:
                        m = mm
                        break

                if m == None:
                    self.log('User {} doesn\'t exists'.format(username))
                    continue

                for board in all_boards:
                    if username in members_username[board.id]:
                        try:
                            self.log('Found {} at board {}'.format(username, board.name))
                            removed = True
                            removed_boards.append('"{}"'.format(board.name))
                            board.remove_member(m)
                            self.log('User {} removed from board {}'.format(username, board.name))
                        except:
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
