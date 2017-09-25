import traceback
import re
from utils import setInterval
from handlers.base import BaseHandler
import boto3
import os
import requests
import tinyapi

class Handler(BaseHandler):

    name = 'TinyLetter'

    prefix = 'tinyletter'

    patterns = [
        (['{prefix} (?P<command>list subscribers) (?P<username>\S+)'], 'Obtém a lista de subscribers de <username>'),
    ]

    def __init__(self, bot, slack, combolist=None):
        super().__init__(bot, slack)

        self.directed = True

        if not combolist:
            self.combolist = os.environ['TINYLETTER_COMBOLIST']
        else:
            self.combolist = combolist

        self.sessions = {}

        for combo in self.combolist.split():
            u = combo.split(':')[0]
            p = combo.split(':')[1]
            allowed_domains = combo.split(':')[2].split(',')
            self.sessions[u] = {'session': tinyapi.Session(username=u, password=p), 'allowed_domains': allowed_domains}

        self.config_section = 'tinyletter'

        self.monitor_changes()

    @setInterval(60)
    def monitor_changes(self):
        for username in self.sessions:
            try:
                section = '{}_{}'.format(self.config_section, username)
                try:
                    self.bot.get_config(section)
                except KeyError:
                    self.bot.create_config_section(section)


                try:
                    subscribers = self.bot.get_config(section, 'subscribers').split()
                except:
                    self.bot.write_config(section, 'subscribers', '')
                    subscribers = self.bot.get_config(section, 'subscribers').split()

                added = []
                removed = []
                denied = []
                cur_subscribers_full = self.sessions[username]['session'].get_subscribers()
                cur_subscribers = [x['email'] for x in cur_subscribers_full]
                for sub in cur_subscribers_full:
                    if sub['email'].split('@')[1] not in self.sessions[username]['allowed_domains']:
                        denied.append(sub)
                    else:
                        if sub['email'] not in subscribers:
                            added.append(sub['email'])

                for sub in subscribers:
                    if sub not in cur_subscribers:
                        removed.append(sub)

                if denied:
                    try:
                        self.sessions[username]['session'].request('delete:Contact', [x['__id'] for x in denied])
                    except:
                        pass

                self.bot.write_config(section, 'subscribers', ' '.join(cur_subscribers))

                if added:
                    self.post_message('#security_logs', 'Inscritos adicionados à newsletter `{}`: {}'.format(username, ', '.join(added)))
                if removed:
                    self.post_message('#security_logs', 'Inscritos removidos da newsletter `{}`: {}'.format(username, ', '.join(removed)))
                if denied:
                    self.post_message('#security_logs', 'Inscritos removidos da newsletter `{}` por não estarem nos domínios permitidos: {}'.format(username, ', '.join([x['email'] for x in denied])))
            except:
                traceback.print_exc()
                continue

    def process(self, channel, user, ts, message, at_bot, command, **kwargs):
        if at_bot:
            handle = self.get_user_handle(user)
            text = None

            if command == 'list subscribers':
                username = kwargs['username']

                subscribers = [x['email'] for x in self.sessions[username]['session'].get_subscribers()]

                self.post_message(channel, text='@{} Subscribers for username {}: {}'.format(handle, username, ', '.join(subscribers)))
