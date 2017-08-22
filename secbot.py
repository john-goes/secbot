import os
import time
import re
from requests import Session
from utils import setInterval

from concurrent.futures import ThreadPoolExecutor, ProcessPoolExecutor

from datetime import datetime

import traceback

from importlib import import_module

import handlers
import configparser

# slacker | slackclient
mode = 'slackclient'

if mode == 'slacker':
    from slacker import Slacker
    from websocket import create_connection

elif mode == 'slackclient':
    from slackclient import SlackClient


class SecBot(object):

    def __init__(self, name='secbot', token=None, websocket_delay=0.5, config_path='config.ini'):
        self.name = name
        self.mode = mode
        self.websocket_delay = websocket_delay


        self.config = configparser.ConfigParser()
        self.config_path = config_path
        self.config.read(self.config_path)

        if not token:
            token = os.environ.get('SLACK_BOT_TOKEN')

        if self.mode == 'slacker':
            self.session = Session()
            self.slack = Slacker(token, session=self.session)
        elif self.mode == 'slackclient':
            self.slack = SlackClient(token)

        self.id = self.get_id()

        self.at_bot = "<@{}>".format(self.id)

        self.handlers = self.get_handlers()

        self.jobs = {}

        self.executor = ThreadPoolExecutor()
        #self.executor = ProcessPoolExecutor()

    def write_config(self):
        with open(self.config_path, 'w') as f:
            self.config.write(f)

    def get_job_status(self, job_id):
        if job_id in self.jobs:
            return self.jobs[job_id]['status']
        else:
            return 'Job not found'

    def get_job_log(self, job_id, size=0):
        if job_id in self.jobs:
            logs = self.jobs[job_id]['log']
            if size == 0:
                if len(logs) >= 10:
                    return logs[:10]
                else:
                    return logs[:len(logs)]
            else:
                if len(logs) >= size:
                    return logs[:size]
                else:
                    return logs[:len(logs)]
        else:
            return []

    def get_jobs(self):
        return self.jobs

    def get_handlers(self):
        hl = []
        for mod in handlers.__all__:
            try:
                start = datetime.now()
                m = import_module('handlers.{}'.format(mod))
                c = getattr(m, 'Handler')

                h = c(self, self.slack)

                hl.append(h)

                end = datetime.now()

                print('[*] Initialized handler {} in {} seconds'.format(h.name, (end - start).total_seconds()))
            except:
                traceback.print_exc()

        return hl

    def start(self):
        if self.mode == 'slacker':
            exit('Slacker mode is missing websocket for reading events... sorry!')
            if self.slack.rtm.connect().body.get('ok'):
                print("[+] SecBot connected and running!")
                ch_joiner = self.join_channels()
                while True:
                    channel, user, ts, message, at_bot = self.parse_slack_output(self.slack.rtm.read())
                    if message and channel:
                        self.executor.submit(self.handle_command, channel, user, ts, message, at_bot)
                        #self.handle_command(channel, user, ts, message)
                    time.sleep(self.websocket_delay)



        if self.mode == 'slackclient':
            if self.slack.rtm_connect(no_latest=True, no_unreads=True, presence_sub=True):
                print("[+] SecBot connected and running!")
                ch_joiner = self.join_channels()
                while True:
                    channel, user, ts, message, at_bot = self.parse_slack_output(self.slack.rtm_read())
                    if message and channel:
                        #self.executor.submit(self.handle_command, channel, user, ts, message, at_bot)
                        self.handle_command(channel, user, ts, message, at_bot)
                    time.sleep(self.websocket_delay)
            else:
                print("[!] Connection failed. Invalid Slack token or bot ID?")


    def get_id(self):
        if self.mode == 'slacker':
            api_call = self.slack.users.list().body
        elif self.mode == 'slackclient':
            api_call = self.slack.api_call("users.list")
        if api_call.get('ok'):
            # retrieve all users so we can find our bot
            users = api_call.get('members')
            for user in users:
                if user.get('name') == self.name:
                    return user.get('id')
        else:
            return None

    def handle_command(self, channel, user, ts, message, at_bot):
        """
            Receives commands directed at the bot and determines if they
            are valid commands. If so, then acts on the commands. If not,
            returns back what it needs for clarification.
        """
        for h in self.handlers:
            try:
                if at_bot:
                    if h.directed:
                        eligible, matches = h.eligible(message)
                        if eligible:
                            self.executor.submit(h.process, channel, user, ts, message, at_bot, extra=list(matches))
                            #h.process(channel, user, ts, message, at_bot, extra=list(matches))
                else:
                    if not h.directed:
                        eligible, matches = h.eligible(message)
                        if eligible:
                            self.executor.submit(h.process, channel, user, ts, message, at_bot, extra=list(matches))
                            #h.process(channel, user, ts, message, at_bot, extra=list(matches))
            except:
                h.log(traceback.format_exc())
                h.set_job_status('Failed')
                traceback.print_exc()
                continue

    def parse_slack_output(self, slack_rtm_output):
        """
            The Slack Real Time Messaging API is an events firehose.
            this parsing function returns None unless a message is
            directed at the Bot, based on its ID.
        """
        output_list = slack_rtm_output
        if output_list and len(output_list) > 0:
            for output in output_list:
                #if output and 'text' in output and AT_BOT in output['text']:
                    # return text after the @ mention, whitespace removed
                if output and 'text' in output and 'user' in output and output['user'] != self.id:
                    if self.at_bot in output['text']:
                        return output['channel'], output['user'], output['ts'], output['text'].split(self.at_bot)[1].strip().lower(), True
                    else:
                        return output['channel'], output['user'], output['ts'], output['text'].strip().lower(), False
                elif output and 'subtype' in output and output['subtype'] == 'message_changed':
                    if self.at_bot in output['message']['text']:
                        return output['channel'], output['message']['user'], output['message']['ts'], output['message']['text'].split(self.at_bot)[1].strip().lower(), True
                    else:
                        return output['channel'], output['message']['user'], output['message']['ts'], output['message']['text'].strip().lower(), False
        return None, None, None, None, None

    @setInterval(10)
    def join_channels(self):
        if self.mode == 'slacker':
            channels = self.slack.channels.list(exclude_members=True, exclue_archived=True).body
        elif self.mode == 'slackclient':
            channels = self.slack.api_call("channels.list", exclude_members=True, exclude_archived=True)
        for ch in channels['channels']:
            if not ch['is_member']:
                print('[*] Joining #{}'.format(ch['name']))
                if self.mode == 'slacker':
                    self.slack.channels.join(name=ch['name'])
                    self.slack.chat.post_message(channel=ch['id'], text="Every move you make\nEvery step you take\nI'll be watching you", as_user=True)
                if self.mode == 'slackclient':
                    self.slack.api_call("channels.join", name=ch['name'], validate=True)
                    self.slack.api_call("chat.postMessage", channel=ch['id'], text="Every move you make\nEvery step you take\nI'll be watching you", as_user=True)


if __name__ == "__main__":
    secbot = SecBot()
    secbot.start()
