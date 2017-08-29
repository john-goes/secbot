import re
from handlers.base import BaseHandler
import traceback

class Handler(BaseHandler):

    name = 'Authorizer'

    patterns = [
        'auth add .* to users .*',
        'auth del .* to users .*',
        'auth list'
    ]

    def __init__(self, bot, slack):
        super().__init__(bot, slack)

        self.directed = True

        #self.job_id = '0'

    def process(self, channel, user, ts, message, at_bot, extra):
        try:
            if at_bot:
                self.set_job_status('Processing')
                handle = self.get_user_handle(user)
                text = None

                if self.authorized(handle, 'Authorizer'):
                    if message.startswith('auth add '):
                        text = message.replace('auth add ', '')
                        sections = text.split('to users')[0].strip().split()
                        users = text.split('to users')[1].strip().split()

                        for section in sections:
                            cur = self.bot.get_config(section, 'allowedusers').split()
                            for u in users:
                                if u not in cur:
                                    cur.append(u)
                            self.bot.write_config(section, 'allowedusers', ' '.join(cur))

                        self.post_message(channel=channel, text='@{} Users {} have been added to sections {}'.format(handle, users, section))

                    elif message.startswith('auth del '):
                        text = message.replace('auth del ', '')
                        sections = text.split('to users')[0].strip().split()
                        users = text.split('to users')[1].strip().split()


                        for section in sections:
                            cur = self.bot.get_config(section, 'allowedusers').split()
                            for u in users:
                                if u in cur:
                                    cur.remove(u)
                            self.bot.write_config(section, 'allowedusers', ' '.join(cur))

                        self.post_message(channel=channel, text='@{} Users {} have been removed from sections {}'.format(handle, users, section))

                    elif message.startswith('auth list'):
                        text = '@{}'.format(handle)
                        for section in self.bot.config.keys():
                            if section != 'DEFAULT' and 'allowedusers' in self.bot.config[section]:
                                try:
                                    text += '\n[{}] AllowedUsers: {}'.format(section, ', '.join(self.bot.config[section]['AllowedUsers'].split()))
                                except:
                                    self.log(traceback.format_exc())
                                    continue

                        self.post_message(channel=channel, text=text)
                else:
                    self.set_job_status('Unauthorized')
                    self.post_message(channel=channel, text='@{} Unauthorized'.format(handle))

            self.set_job_status('Finished')
        except:
            self.log(traceback.format_exc())

