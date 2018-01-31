import re
from github import Github
import requests
import traceback
import os
from utils import setInterval

from datetime import datetime

from handlers.base import BaseHandler

class Handler(BaseHandler):

    name = 'GIM'

    prefix = 'gim'

    patterns = [
        (['{prefix} (?P<application>\S+) (?P<command>recover) (?P<users>.*)'], 'Envia email de recuperação de senha para <users> da aplicação <application>'),
        (['{prefix} (?P<command>list applications)'], 'Lista as aplicações disponíveis'),
    ]

    def __init__(self, bot, slack):

        super().__init__(bot, slack)

        self.directed = True

        self.applications = {}

        for app in os.environ.get('GIM_APPLICATIONS').split():
            name = app.split(':')[0]
            key = app.split(':')[1]
            apikey = app.split(':')[2]

            self.applications[name] = {'key': key, 'api_key': apikey}

        self.set_job_status('Initialized')

        self.loop_count = 0

    def get_headers(self, api_key):
        headers = {
          'Content-Type': 'application/json',
          'Accept': 'application/json',
          'Authorization': 'Bearer {}'.format(api_key)
        }

        return headers

    def strip_mailto(self, obj):
        if ':' in obj and '|' in obj:
            return obj.split(':')[1].split('|')[0]
        else:
            return obj

    def process(self, channel, user, ts, message, at_bot, command=None, **kwargs):
        try:
            if at_bot:
                user_handle = self.get_user_handle(user)
                if command == 'list applications':
                    self.post_message(channel=channel, text='@{} Aplicações: {}'.format(user_handle, ', '.join(self.applications.keys())))
                elif command == 'recover':
                    self.set_job_status('Processing')

                    self.log('@{}: {}'.format(user_handle, message))

                    to_recover = [self.strip_mailto(x) for x in kwargs['users'].split() if '@' in x]

                    if len(to_recover) == 0:
                        self.log('No valid usernames')
                        self.set_job_status('Finished')
                        return

                    if not self.authorized(user_handle, 'GIM'):
                        self.set_job_status('Unauthorized')
                        self.post_message(channel=channel, text='@{} Unauthorized'.format(user_handle))
                        return False

                    if kwargs['application'] in self.applications:

                        self.post_message(channel=channel, text='@{} Recuperando senha de usuários: {}'.format(user_handle, ', '.join(to_recover)))

                        for username in to_recover:
                            try:
                                key = self.applications[kwargs['application']]['key']
                                api_key = self.applications[kwargs['application']]['api_key']
                                headers = self.get_headers(api_key)
                                r = requests.get('https://gim.stone.com.br/api/management/{key}/users/{username}/password'.format(key=key, username=username), headers=headers)
                                try:
                                    obj = r.json()
                                except:
                                    self.log(r.content)
                                    continue

                                if obj['Success']:
                                    self.log('Usuário {} recuperado'.format(username))

                                    text = '@{} Usuário {} recuperado, solicite que verifique o email.'.format(user_handle, username)

                                    self.post_message(channel, text)
                                else:
                                    if obj.get('OperationReport', {}).get('Message') == 'The specified user is not associated to this application.':
                                        self.post_message(channel=channel, text='@{} Usuário {} não encontrado na aplicação {}'.format(user_handle, username, kwargs['application']))
                                    else:
                                        self.log('An error occured while recovering user {} password: {}'.format(username, obj))
                            except:
                                self.log(traceback.format_exc())
                                continue
                    else:
                        self.post_message(channel=channel, text='@{} Aplicação não encontrada {}'.format(kwargs['application']))

                self.set_job_status('Finished')
                self.set_job_end(datetime.now())
        except:
            self.log(traceback.format_exc())


