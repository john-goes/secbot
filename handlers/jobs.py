import re
from handlers.base import BaseHandler

class Handler(BaseHandler):

    name = 'Jobs'

    prefix = 'job'

    patterns = [
        (['{prefix} (?P<command>status) (?P<jobs>.*)'], 'Obtém o status das jobs .*'),
        (['{prefix} (?P<command>logs) (?P<jobs>.*)'], 'Obtém os logs das jobs .*'),
        (['{prefix} (?P<command>list)'], 'Obtém a lista de jobs .*'),
    ]

    def __init__(self, bot, slack):
        super().__init__(bot, slack)

        self.directed = True

        self.job_id = '0'

    def process(self, channel, user, ts, message, at_bot, command, **kwargs):
        if at_bot:
            handle = self.get_user_handle(user)
            text = None

            if self.authorized(handle, 'jobs'):
                if command == 'status':
                    ids = kwargs['jobs'].split()
                    text = ''
                    for job in ids:
                        text += '\n#{} status: {}'.format(job, self.bot.get_job_status(job))
                elif command == 'logs':
                    try:
                        ids = kwargs['jobs'].split()
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
                elif command == 'list':
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
