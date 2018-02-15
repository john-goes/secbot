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

    prefix = 'github'

    patterns = [
        (['(?P<command>desligar) (?P<users>.*)', '(?P<command>terminate) (?P<users>.*)', '{prefix} (?P<command>terminate) (?P<users>.*)'], 'Desliga um funcionário'),
        (['{prefix} (?P<command>add user) (?P<users>.*)'], 'Adiciona usuários na Org'),
        (['{prefix} (?P<command>allow nomfa) (?P<users>.*)'], 'Permite que um usuário não tenha MFA habilitado'),
        (['{prefix} (?P<command>deny nomfa) (?P<users>.*)'], 'Nega que um usuário não tenha MFA habilitado'),
        (['{prefix} (?P<command>list nomfa)'], 'Lista os usuários sem MFA'),
        (['{prefix} (?P<command>list members)'], 'Lista todos os membros da org'),
        (['{prefix} (?P<command>list owners)'], 'Lista todos os owners da org'),
    ]

    def __init__(self, bot, slack, login=None, password=None, org=None):

        super().__init__(bot, slack)

        self.directed = True

        if not password:
            password = os.environ.get('GITHUB_PASSWORD', 'NOPWD')
        if not login:
            if password == 'NOPWD':
                login = os.environ.get('GITHUB_TOKEN')
            else:
                login = os.environ.get('GITHUB_LOGIN')
        if not org:
            org = os.environ.get('GITHUB_ORGANIZATION')

        if password == 'NOPWD':
            self.client = Github(login)
        else:
            self.client = Github(login, password)

        self.org = self.client.get_organization(org)

        self.config_section = 'github_{}'.format(self.org.login)

        self.get_members()

        self.set_job_status('Initialized')

        self.loop_count = 0

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
            self.post_message('#security_logs', '@here Usuários adicionados como OWNER na org {}: {}'.format(self.org.name, ', '.join(added_owners)))
            self.bot.write_config(self.config_section, 'owners', ' '.join(owners_list))
        if removed_owners:
            self.post_message('#security_logs', '@here Usuários removidos como OWNER da org {}: {}'.format(self.org.name, ', '.join(removed_owners)))
            self.bot.write_config(self.config_section, 'owners', ' '.join(owners_list))

        added_members = []
        removed_members = [x for x in self.bot.get_config(self.config_section, 'members').split() if x not in members_list]

        for p in members:
            if p.login not in self.bot.get_config(self.config_section, 'members').split():
                added_members.append(p.login)
        if added_members:
            self.post_message('#security_logs', 'Usuários adicionados na org {}: {}'.format(self.org.name, ', '.join(added_members)))
        if removed_members:
            self.post_message('#security_logs', 'Usuários removidos da org {}: {}'.format(self.org.name, ', '.join(removed_members)))
        self.bot.write_config(self.config_section, 'members', ' '.join(members_list))

        for p in nomfa:
            if p.login not in self.bot.get_config(self.config_section, 'nomfa').split():
                try:
                    self.org.remove_from_members(p)
                    self.post_message('#security_logs', 'Usuário {} foi removido da org {} por não ter 2FA habilitado!'.format(p.login, self.org.name))
                except:
                    self.post_message('#security_logs', 'Tentei remover o usuário {} da org {} por não ter 2FA habilitado, mas deu ruim!'.format(p.login, self.org.name))


    def process(self, channel, user, ts, message, at_bot, command=None, **kwargs):
        try:
            if at_bot:
                user_handle = self.get_user_handle(user)
                if command in ['desligar', 'terminate']:
                    self.set_job_status('Processing')

                    self.log('@{}: {}'.format(user_handle, message))

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
                                self.log('User {} doesn\'t exist'.format(username))
                                self.post_message(channel,  '@{} User {} doesn\'t exist'.format(user_handle, username))
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
                elif command == 'add user':
                    if not self.authorized(user_handle, 'Authorizer'):
                        self.set_job_status('Unauthorized')
                        self.post_message(channel=channel, text='@{} Unauthorized'.format(user_handle))
                        return False

                    to_allow = [x for x in kwargs['users'].split() if '@' not in x]

                    for username in to_allow:
                            try:
                                m = self.client.get_user(username)
                            except:
                                self.log('User {} doesn\'t exists'.format(username))
                                self.post_message(channel,  '@{} User {} doesn\'t exists'.format(user_handle, username))
                                continue

                            try:
                                self.org.add_membership(m)
                            except:
                                traceback.print_exc()

                    self.post_message(channel, '@{} usuários adicionados à org: {}'.format(user_handle, ' '.join(to_allow)))

                elif command == 'allow nomfa':
                    if not self.authorized(user_handle, 'Authorizer'):
                        self.set_job_status('Unauthorized')
                        self.post_message(channel=channel, text='@{} Unauthorized'.format(user_handle))
                        return False

                    to_allow = [x for x in kwargs['users'].split() if '@' not in x]

                    tpl = self.bot.get_config(self.config_section, 'nomfa').split()

                    for p in to_allow:
                        if p not in tpl:
                            tpl.append(p)
                    self.bot.write_config(self.config_section, 'nomfa', ' '.join(tpl))

                    self.post_message(channel, '@{} usuários adicionados à lista de exclusões de MFA: {}'.format(user_handle, ' '.join(to_allow)))

                elif command == 'deny nomfa':
                    if not self.authorized(user_handle, 'Authorizer'):
                        self.set_job_status('Unauthorized')
                        self.post_message(channel=channel, text='@{} Unauthorized'.format(user_handle))
                        return False

                    to_deny = [x for x in kwargs['users'].split() if '@' not in x]

                    tpl = [x for x in self.bot.get_config(self.config_section, 'nomfa').split() if x not in to_deny]

                    self.bot.write_config(self.config_section, 'nomfa', ' '.join(tpl))

                    self.post_message(channel, '@{} usuários removidos da lista de exclusões de MFA: {}'.format(user_handle, ' '.join(to_deny)))
                elif command == 'list nomfa':
                    nomfa = [x.login for x in self.org.get_members(filter_='2fa_disabled')]
                    self.post_message(channel, '@{} Usuários sem MFA: {}\nUsuários com permissão de não ter MFA: {}'.format(user_handle, ', '.join(nomfa), ', '.join(self.bot.get_config(self.config_section, 'nomfa').split())))
                elif command == 'list members':
                    try:
                        members = self.org.get_members(role='all')
                        members_list = [x.login for x in members]
                        self.post_message(channel, '@{} Membros da org {}: {}'.format(user_handle, self.org.name, ', '.join(members_list)))
                    except Exception as e:
                        print(str(e))
                elif command == 'list owners':
                    owners = self.org.get_members(role='admin')
                    owners_list = [x.login for x in owners]
                    self.post_message(channel, '@{} Owners da org {}: {}'.format(user_handle, self.org.name, ', '.join(owners_list)))

                self.set_job_status('Finished')
                self.set_job_end(datetime.now())
        except:
            self.log(traceback.format_exc())


