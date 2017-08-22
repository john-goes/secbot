import re
from github import Github
import requests
import traceback
import os

from datetime import datetime

from handlers.base import BaseHandler

class Handler(BaseHandler):

    name = 'GitHub Terminator'

    patterns = [
        'desligar .*',
        'terminate .*'
    ]

    def __init__(self, bot, slack, login=None, password=None):

        super().__init__(bot, slack)

        self.directed = True

        if not login:
            login = os.environ.get('GITHUB_LOGIN')
        if not password:
            password = os.environ.get('GITHUB_PASSWORD')

        self.client = Github(login, password)

        self.set_job_status('Initialized')


    def process(self, channel, user, ts, message, at_bot, extra=None):
        if at_bot:
            self.set_job_status('Processing')

            to_remove = message.replace('desligar ', '').replace('terminate ', '').split()

            user_handle = self.get_user_handle(user)

            if not self.authorized(user_handle, 'Terminator'):
                self.set_job_status('Unauthorized')
                self.post_message(channel=channel, text='@{} Unauthorized'.format(user_handle))
                return False

            self.log('Got request: {}'.format(message))

            self.post_message(channel=channel, text='@{} Removendo usuários: {}'.format(user_handle, ', '.join(to_remove)))

            org = self.client.get_organization('pagarme')

            for username in to_remove:
                try:
                    try:
                        m = self.client.get_user(username)
                    except:
                        self.post_message(channel,  '@{} User {} doesn\'t exists'.format(user_handle, username))
                        continue

                    try:
                        org.remove_from_members(m)
                    except:
                        self.post_message(channel, '@{} User {} not in organization {}'.format(user_handle, username, org.name))
                        continue

                    text = '@{} User {} removed from organization {}'.format(user_handle, username, org.name)

                    self.post_message(channel, text)
                except:
                    self.log(traceback.format_exc())
                    continue

            self.set_job_status('Finished')
            self.set_job_end(datetime.now())


