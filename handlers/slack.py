import re
import requests
import traceback
import os
from utils import setInterval

from datetime import datetime

from handlers.base import BaseHandler

class Handler(BaseHandler):

    name = 'Slack'

    prefix = 'slack'

    patterns = [
        (['(?P<command>desligar) (?P<users>.*)', '(?P<command>terminate) (?P<users>.*)', '{prefix} (?P<command>terminate) (?P<users>.*)'], 'Desliga um funcionário'),
        (['{prefix} (?P<command>allow nomfa) (?P<users>.*)'], 'Permite que um usuário não tenha MFA habilitado'),
        (['{prefix} (?P<command>allow nomfa) (?P<users>.*)'], 'Permite que um usuário não tenha MFA habilitado'),
        (['{prefix} (?P<command>allow nomfa) (?P<users>.*)'], 'Permite que um usuário não tenha MFA habilitado'),
        (['{prefix} (?P<command>deny nomfa) (?P<users>.*)'], 'Nega que um usuário não tenha MFA habilitado'),
        (['{prefix} (?P<command>list nomfa)'], 'Lista os usuários sem MFA'),
    ]

    def __init__(self, bot, slack):

        super().__init__(bot, slack)

        self.directed = True

        self.org = self.slack.api_call('team.info')

        self.config_section = 'slack_{}'.format(self.org['team']['domain'])

        self.get_members()

        self.set_job_status('Initialized')

    @setInterval(30)
    def get_members(self):

        m = self.slack.api_call('users.list')

        try:
            members = m['members']
        except:
            print(m)
        # == False prevents None from matching with "not x"
        nomfa = [(x['id'], x['name']) for x in members if x.get('has_2fa') == False]

        owners_list = [x['name'] for x in members if x.get('is_owner')]
        admins_list = [x['name'] for x in members if x.get('is_admin')]
        members_list = [x['name'] for x in members]

        added_owners = []
        removed_owners = [x for x in self.bot.get_config(self.config_section, 'owners').split() if x not in owners_list]

        added_admins = []
        removed_admins = [x for x in self.bot.get_config(self.config_section, 'admins').split() if x not in admins_list]

        added_members = []
        removed_members = [x for x in self.bot.get_config(self.config_section, 'members').split() if x not in members_list]

        for p in owners_list:
            if p not in self.bot.get_config(self.config_section, 'owners').split():
                added_owners.append(p)
        if added_owners:
            self.post_message('#security_logs', '@here Usuários adicionados como OWNER na org {}: {}'.format(self.org['team']['name'], ', '.join(added_owners)))
            self.bot.write_config(self.config_section, 'owners', ' '.join(owners_list))
        if removed_owners:
            self.post_message('#security_logs', '@here Usuários removidos como OWNER da org {}: {}'.format(self.org['team']['name'], ', '.join(removed_owners)))
            self.bot.write_config(self.config_section, 'owners', ' '.join(owners_list))

        for p in admins_list:
            if p not in self.bot.get_config(self.config_section, 'admins').split():
                added_admins.append(p)
        if added_admins:
            self.post_message('#security_logs', '@here Usuários adicionados como OWNER na org {}: {}'.format(self.org['team']['name'], ', '.join(added_admins)))
            self.bot.write_config(self.config_section, 'admins', ' '.join(admins_list))
        if removed_admins:
            self.post_message('#security_logs', '@here Usuários removidos como OWNER da org {}: {}'.format(self.org['team']['name'], ', '.join(removed_admins)))
            self.bot.write_config(self.config_section, 'admins', ' '.join(admins_list))

        for p in members_list:
            if p not in self.bot.get_config(self.config_section, 'members').split():
                added_members.append(p)
        if added_members:
            self.bot.write_config(self.config_section, 'members', ' '.join(members_list))
            self.post_message('#security_logs', 'Usuários adicionados na org {}: {}'.format(self.org['team']['name'], ', '.join(added_members)))
        if removed_members:
            self.post_message('#security_logs', 'Usuários removidos da org {}: {}'.format(self.org['team']['name'], ', '.join(removed_members)))


        nomfa_list = []
        for p in nomfa:
            if p[1] not in self.bot.get_config(self.config_section, 'nomfa').split():
                nomfa_list.append(p[1])
        #self.post_message('#security_logs', 'Os seguintes usuários não possuem MFA habiltiado. Infelizmente, não posso removê-los por limitações da API free.\n{}'.format(', '.join(nomfa_list)))


    def process(self, channel, user, ts, message, at_bot, command, **kwargs):
        print(command)
        try:
            if at_bot:
                user_handle = self.get_user_handle(user)
                if command in ['desligar', 'terminate']:
                    self.set_job_status('Processing')

                    user_handle = self.get_user_handle(user)

                    self.log('@{}: {}'.format(user_handle, message))

                    to_remove = [x for x in kwargs['users'] if '@' not in x]

                    if len(to_remove) == 0:
                        self.log('No valid usernames')
                        self.set_job_status('Finished')
                        return

                    if not self.authorized(user_handle, 'Terminator'):
                        self.set_job_status('Unauthorized')
                        self.post_message(channel=channel, text='@{} Unauthorized'.format(user_handle))
                        return False

                    self.post_message(channel=channel, text='@{} Não posso remover usuários no Slack devido à limitações da API free'.format(user_handle))

                elif command == 'allow nomfa':
                    to_allow = [x for x in kwargs['users'] if '@' not in x]

                    tpl = self.bot.get_config(self.config_section, 'nomfa').split()

                    for p in to_allow:
                        if p not in tpl:
                            tpl.append(p)
                    self.bot.write_config(self.config_section, 'nomfa', ' '.join(tpl))

                    self.post_message(channel, '@{} usuários adicionados à lista de exclusões de MFA: {}'.format(user_handle, ' '.join(to_allow)))

                elif command == 'deny nomfa':
                    to_deny = [x for x in kwargs['users'] if '@' not in x]

                    tpl = [x for x in self.bot.get_config(self.config_section, 'nomfa').split() if x not in to_deny]

                    self.bot.write_config(self.config_section, 'nomfa', ' '.join(tpl))

                    self.post_message(channel, '@{} usuários removidos da lista de exclusões de MFA: {}'.format(user_handle, ' '.join(to_deny)))
                elif command == 'list nomfa':
                    members = self.slack.api_call('users.list')['members']
                    nomfa = [x['name'] for x in members if x.get('has_2fa') == False]
                    self.post_message(channel, '@{} Usuários sem MFA: {}\nUsuários com permissão de não ter MFA: {}'.format(user_handle, ', '.join(nomfa), ', '.join(self.bot.get_config(self.config_section, 'nomfa').split())))

                self.set_job_status('Finished')
                self.set_job_end(datetime.now())
        except:
            self.log(traceback.format_exc())


