import re
from github import Github
import requests
import traceback
import os
from utils import setInterval

from datetime import datetime

from handlers.base import BaseHandler

class Handler(BaseHandler):

    name = 'GitHub'

    patterns = [
        'desligar .*',
        'terminate .*',
        'github terminate .*',
        'github allow nomfa .*',
        'github deny nomfa .*',
        'github list nomfa',
    ]

    def __init__(self, bot, slack, login=None, password=None, org=None):

        super().__init__(bot, slack)

        self.directed = True

        if not login:
            login = os.environ.get('GITHUB_LOGIN')
        if not password:
            password = os.environ.get('GITHUB_PASSWORD')
        if not org:
            org = os.environ.get('GITHUB_ORGANIZATION')

        self.client = Github(login, password)

        self.org = self.client.get_organization(org)

        self.config_section = 'github_{}'.format(self.org.login)

        self.get_members()

        self.set_job_status('Initialized')

    @setInterval(30)
    def get_members(self):

        owners = self.org.get_members(role='admin')
        members = self.org.get_members(role='all')
        nomfa = self.org.get_members(filter_='2fa_disabled')

        owners_list = [x.login for x in owners]
        members_list = [x.login for x in members]

        added_owners = []
        removed_owners = [x for x in self.bot.get_config(self.config_section, 'owners').split() if x not in owners_list]

        for p in owners_list:
            if p not in self.bot.get_config(self.config_section, 'owners').split():
                added_owners.append(p)
        if added_owners:
            self.post_message('#seguranca', '@here Usuários adicionados como OWNER na org {}: {}'.format(self.org.name, ', '.join(added_owners)))
            self.bot.write_config(self.config_section, 'owners', ' '.join(owners_list))
        if removed_owners:
            self.post_message('#seguranca', '@here Usuários removidos como OWNER da org {}: {}'.format(self.org.name, ', '.join(removed_owners)))
            self.bot.write_config(self.config_section, 'owners', ' '.join(owners_list))

        added_members = []
        removed_members = [x for x in self.bot.get_config(self.config_section, 'members').split() if x not in members_list]

        for p in members:
            if p.login not in self.bot.get_config(self.config_section, 'members').split():
                added_members.append(p.login)
        if added_members:
            self.bot.write_config(self.config_section, 'members', ' '.join(members_list))
            self.post_message('#seguranca', 'Usuários adicionados na org {}: {}'.format(self.org.name, ', '.join(added_members)))
        if removed_members:
            self.post_message('#seguranca', 'Usuários removidos da org {}: {}'.format(self.org.name, ', '.join(removed_members)))

        for p in nomfa:
            if p.login not in self.bot.get_config(self.config_section, 'nomfa').split():
                try:
                    self.org.remove_from_members(p)
                    self.post_message('#seguranca', 'Usuário {} foi removido da org {} por não ter 2FA habilitado!'.format(p.login, self.org.name))
                except:
                    self.post_message('#seguranca', 'Tentei remover o usuário {} da org {} por não ter 2FA habilitado, mas deu ruim!'.format(p.login, self.org.name))


    def process(self, channel, user, ts, message, at_bot, extra=None):
        try:
            if at_bot:
                user_handle = self.get_user_handle(user)
                if message.startswith('desligar ') or message.startswith('terminate ') or message.startswith('github terminate '):
                    self.set_job_status('Processing')

                    user_handle = self.get_user_handle(user)

                    self.log('@{}: {}'.format(user_handle, message))

                    to_remove = [x for x in message.replace('desligar ', '').replace('github terminate ', '').replace('terminate ', '').split() if '@' not in x]

                    if len(to_remove) == 0:
                        self.log('No valid usernames')
                        self.set_job_status('Finished')
                        return

                    if not self.authorized(user_handle, 'Terminator'):
                        self.set_job_status('Unauthorized')
                        self.post_message(channel=channel, text='@{} Unauthorized'.format(user_handle))
                        return False

                    self.post_message(channel=channel, text='@{} Removendo usuários: {}'.format(user_handle, ', '.join(to_remove)))

                    for username in to_remove:
                        try:
                            try:
                                m = self.client.get_user(username)
                            except:
                                self.log('User {} doesn\'t exists'.format(username))
                                self.post_message(channel,  '@{} User {} doesn\'t exists'.format(user_handle, username))
                                continue

                            try:
                                self.org.remove_from_members(m)
                                self.log('User {} removed'.format(username))

                                text = '@{} User {} removed from organization {}'.format(user_handle, username, self.org.name)

                                self.post_message(channel, text)
                            except:
                                self.log('User {} not in organization {}'.format(username, self.org.name))
                                self.post_message(channel, '@{} User {} not in organization {}'.format(user_handle, username, self.org.name))
                                continue

                        except:
                            self.log(traceback.format_exc())
                            continue
                elif message.startswith('github allow nomfa '):
                    to_allow = message.replace('github allow nomfa ', '').split()

                    tpl = self.bot.get_config(self.config_section, 'nomfa').split()

                    for p in to_allow:
                        if p not in tpl:
                            tpl.append(p)
                    self.bot.write_config(self.config_section, 'nomfa', ' '.join(tpl))

                    self.post_message(channel, '@{} usuários adicionados à lista de exclusões de MFA: {}'.format(user_handle, ' '.join(to_allow)))

                elif message.startswith('github deny nomfa '):
                    to_deny = message.replace('github deny nomfa ', '').split()

                    tpl = [x for x in self.bot.get_config(self.config_section, 'nomfa').split() if x not in to_deny]

                    self.bot.write_config(self.config_section, 'nomfa', ' '.join(tpl))

                    self.post_message(channel, '@{} usuários removidos da lista de exclusões de MFA: {}'.format(user_handle, ' '.join(to_deny)))
                elif message.startswith('github list nomfa'):
                    nomfa = [x.login for x in self.org.get_members(filter_='2fa_disabled')]
                    self.post_message(channel, '@{} Usuários sem MFA: {}\nUsuários com permissão de não ter MFA: {}'.format(user_handle, ', '.join(nomfa), ', '.join(self.bot.get_config(self.config_section, 'nomfa').split())))

                self.set_job_status('Finished')
                self.set_job_end(datetime.now())
        except:
            self.log(traceback.format_exc())


