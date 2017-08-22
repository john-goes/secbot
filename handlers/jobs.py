import re
from handlers.base import BaseHandler

class Handler(BaseHandler):

    name = 'Jobs'

    patterns = [
        'job status .*',
        'job logs .*',
        'job list'
    ]

    def __init__(self, bot, slack):
        super().__init__(bot, slack)

        self.directed = True

        self.job_id = '0'

    def process(self, channel, user, ts, message, at_bot, extra):
        if at_bot:
            handle = self.get_user_handle(user)
            text = None

            if self.authorized(handle, 'jobs'):
                if message.startswith('job status'):
                    ids = message.replace('job status ', '').split()
                    text = ''
                    for job in ids:
                        text += '\n#{} status: {}'.format(job, self.bot.get_job_status(job))
                elif message.startswith('job logs'):
                    try:
                        ids = message.replace('job logs ', '').split()
                        text = ''
                        for job in ids:
                            try:
                                logs = self.bot.get_job_log(job)
                                if not logs:
                                    text += '\n#{} logs: Job not found'.format(job)
                                else:
                                    for log in logs:
                                        text += '\n#{} logs: [{}] {}'.format(job, log['date'], log['text'])
                            except:
                                continue
                    except:
                        traceback.print_exc()
                elif message.startswith('job list'):
                    text = ''
                    d = self.bot.get_jobs()
                    for job in d:
                        if d[job]['end']:
                            text += '\nJob #{} ({}), started at {} and ended at {}. Status: {}'.format(d[job]['id'], d[job]['handler'], d[job]['start'], d[job]['end'], d[job]['status'])
                        else:
                            text += '\nJob #{} ({}), started at {}. Status: {}'.format(d[job]['id'], d[job]['handler'], d[job]['start'], d[job]['status'])
                    if text == '':
                        text = 'There are no jobs in the history'

                if text:
                    self.post_message(channel=channel, text=text)
            else:
                self.post_message(channel=channel, text='@{} Unauthorized'.format(handle))
