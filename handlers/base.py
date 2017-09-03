import os
import re
import traceback
import uuid
from datetime import datetime

class BaseHandler(object):

    name = 'Handler'

    patterns = []

    def __init__(self, bot, slack):
        self.job_id = str(uuid.uuid4())[:8]
        self.bot = bot
        self.slack = slack

        self.directed = False

        self.master = os.environ.get('MASTER_USER', 'kamushadenes')

        self.patterns.append((['{prefix} help'], 'Ajuda'))

    def authorized(self, handle, section):
        if handle == self.master:
            return True
        else:
            authorized = self.bot.get_config(section.lower(), 'allowedusers').split()
            if handle in authorized:
                return True
        return False

    def set_job_handler(self, job_handler=None):
        self.bot.jobs[self.job_id]['handler'] = job_handler if job_handler else self.name

    def set_job_status(self, status):
        try:
            self.bot.jobs[self.job_id]['status'] = status
            self.add_job_log(status)
        except:
            pass

    def set_job_end(self, date):
        self.bot.jobs[self.job_id]['end'] = date

    def add_job_log(self, date, log):
        obj = {'date': date, 'text': log}
        self.bot.jobs[self.job_id]['log'].append(obj)


    def process(self, channel, user, ts, message, at_bot, extra=None):
        raise NotImplemented

    def pre_process(self, channel, user, ts, message, at_bot, extra=None):
        if hasattr(self, 'prefix'):
            if message == '{prefix} help'.format(prefix=self.prefix):
                self.help(channel, user, ts, message, at_bot, extra)
        else:
            self.process(channel, user, ts, message, at_bot, extra)

    def help(self, channel, user, ts, message, at_bot, extra=None):
        handle = self.get_user_handle(user)
        text = '@{} '.format(handle)
        for ptrc in self.patterns:
            if type(ptrc) == tuple:
                text += '\n`{} - {}`'.format([x.format(prefix=self.prefix).replace('*', '*') for x in ptrc[0]], ptrc[1])
        self.post_message(channel, text)

    def delete(self, channel, ts):
        if self.bot.mode == 'slacker':
            self.slack.chat.delete(channel=channel, ts=ts, as_user=True)
        elif self.bot.mode == 'slackclient':
            self.slack.api_call('chat.delete', channel=channel, ts=ts, as_user=True)

    def post_ephemeral(self, channel, user, text):
        if self.bot.mode == 'slacker':
            self.slack.chat.post_ephemeral(channel=channel, as_user=True, user=user, text=text, link_names=True)
        elif self.bot.mode == 'slackclient':
            self.slack.api_call('chat.postEphemeral', channel=channel, as_user=True, user=user, text=text, link_names=True)

    def post_message(self, channel, text):
        text = '[{}#{}] {}'.format(self.name, self.job_id, text)
        if self.bot.mode == 'slacker':
            self.slack.chat.post_message(channel=channel, text=text, as_user=True, link_names=True)
        elif self.bot.mode == 'slackclient':
            self.slack.api_call('chat.postMessage', channel=channel, text=text, as_user=True, link_names=True)

    def get_user_handle(self, user):
        username = None
        try:
            if self.bot.mode == 'slacker':
                username = self.slack.users.info(user=user).body['user']['name']
            elif self.bot.mode == 'slackclient':
                username = self.slack.api_call('users.info', user=user)['user']['name']
        except:
            pass

        return username

    def log(self, text):
        date = datetime.now()
        text = '[{}#{}] {}'.format(self.name, self.job_id, text)
        if self.job_id != '0':
            self.add_job_log(date, text)
        print(date, text)


    def eligible(self, text):
        matches = set()
        try:
            start = datetime.now()
            matched = False
            for ptrc in self.patterns:
                if type(ptrc) == tuple:
                    ptrl = ptrc[0]
                else:
                    ptrl = [ptrc]
                for ptr in ptrl:
                    ptr = ptr.format(prefix=self.prefix)
                    m = re.findall(ptr, text)
                    if m:
                        for g in m:
                            if isinstance(g, tuple):
                                for x in g:
                                    if bool(x):
                                        #print('[+] {} matched with {}'.format(x, self.name))
                                        matches.add(x)
                                        matched = True
                            else:
                                print('[+] {} matched with {}'.format(g, self.name))
                                matches.add(g)
                                matched = True
            if matched and self.job_id != '0':
                self.bot.jobs[self.job_id] = {'id': self.job_id, 'status': 'Initializing', 'log': [], 'handler': 'Generic', 'start': start, 'end': None}
                self.set_job_handler()
            return matched, matches
        except:
            traceback.print_exc()
            return False, None
