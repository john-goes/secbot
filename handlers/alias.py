import re
from handlers.base import BaseHandler
import traceback

class Handler(BaseHandler):

    name = 'Alias'

    prefix = 'alias'

    patterns = [
        (['{prefix} (?P<command>list)'], 'Lista os alias'),
        (['{prefix} (?P<command>list reverse)'], 'Lista os alias reversos'),
        (['{prefix} (?P<username>\S+) (?P<command>isnt) (?P<aliases>.*)'], 'Remove um alias do usuário'),
        (['{prefix} (?P<command>i aint) (?P<aliases>.*)'], 'Remove um alias de você mesmo'),
        (['{prefix} (?P<username>\S+) (?P<command>is) (?P<aliases>.*)'], 'Adiciona um alias ao usuário'),
        (['{prefix} (?P<command>i am) (?P<aliases>.*)'], 'Adiciona um alias a você mesmo'),
    ]

    def __init__(self, bot, slack):
        super().__init__(bot, slack)

        self.directed = True

        #self.job_id = '0'

    def strip_mailto(self, obj):
        if ':' in obj and '|' in obj:
            return obj.split(':')[1].split('|')[0]
        else:
            return obj

    def process(self, channel, user, ts, message, at_bot, command, **kwargs):
        try:
            if at_bot:
                self.set_job_status('Processing')
                handle = self.get_user_handle(user)

                if command == 'is':
                    if self.authorized(handle, 'Authorizer'):
                        aliases = [self.strip_mailto(x) for x in kwargs['aliases'].split()]
                        username = kwargs['username']

                        members = [x['name'] for x in self.slack.api_call('users.list')['members']]

                        try:
                            na = self.bot.get_config('alias', username).split()
                        except:
                            na = []

                        if na:
                            for alias in aliases:
                                if alias not in na and alias not in members:
                                    na.append(alias)

                        self.bot.write_config('alias', username, ' '.join(na))

                        for alias in aliases:
                            if alias in members:
                                self.post_message(channel, '@{} Unauthorized to become {} as this is an Slack username'.format(handle, alias))
                            else:
                                self.bot.write_config('alias_reverse', alias, username)

                    else:
                        self.log('Unauthorized')
                        self.post_message(channel, '@{} Unauthorized'.format(handle))

                    self.post_message(channel, '@{} {} is {}'.format(handle, username, self.bot.get_config('alias', username)))

                elif command == 'i am':
                    aliases = [self.strip_mailto(x) for x in kwargs['aliases'].split()]

                    members = [x['name'] for x in self.slack.api_call('users.list')['members']]

                    for alias in aliases:
                        if alias in members:
                            self.post_message(channel, '@{} Unauthorized to become {} as this is an Slack username'.format(handle, alias))
                        else:
                            try:
                                c = self.bot.get_config('alias_reverse', alias)
                                if c:
                                    if self.authorized(handle, 'Authorizer'):
                                        self.bot.write_config('alias_reverse', alias, handle)
                                    else:
                                        self.post_message(channel, '@{} Unauthorized to become {} as the alias already belongs to {}'.format(handle, alias, c))
                            except:
                                self.bot.write_config('alias_reverse', alias, handle)

                    try:
                        c = self.bot.get_config('alias', handle).split()
                    except:
                        c = []

                    for alias in aliases:
                        if alias in members:
                            self.post_message(channel, '@{} Unauthorized to become {} as this is an Slack username'.format(handle, alias))
                        if alias not in c:
                            c.append(alias)

                    self.bot.write_config('alias', handle, ' '.join(c))

                    self.post_message(channel, '@{} you are {}'.format(handle, self.bot.get_config('alias', handle)))
                elif command == 'i aint':
                    aliases = [self.strip_mailto(x) for x in kwargs['aliases'].split()]

                    if self.authorized(handle, 'Authorizer'):

                        for alias in aliases:
                            self.bot.write_config('alias_reverse', alias, '')

                        try:
                            c = self.bot.get_config('alias', handle).split()
                        except:
                            c = None

                        if c:
                            c = [x for x in c if x not in aliases]
                            self.bot.write_config('alias', handle, ' '.join(c))
                    else:
                        self.log('Unauthorized')
                        self.post_message(channel, '@{} Unauthorized to stop being {}'.format(handle, aliases))

                    self.post_message(channel, '@{} you are {}'.format(handle, self.bot.get_config('alias', handle)))

                elif command == 'isnt':
                    aliases = [self.strip_mailto(x) for x in kwargs['aliases'].split()]
                    username = kwargs['username']

                    if self.authorized(handle, 'Authorizer'):
                        for alias in aliases:
                            self.bot.write_config('alias_reverse', alias, '')

                        try:
                            c = self.bot.get_config('alias', handle).split()
                        except:
                            c = None

                        if c:
                            c = [x for x in c if x not in aliases]
                            self.bot.write_config('alias', username, ' '.join(c))
                    else:
                        self.log('Unauthorized')
                        self.post_message(channel, '@{} Unauthorized'.format(handle))

                    self.post_message(channel, '@{} {} is {}'.format(handle, username, self.bot.get_config('alias', username)))
                elif command == 'list':
                    text = '@{}'.format(handle)
                    c = self.bot.get_config('alias')
                    for alias in c:
                        text += '\n{}: {}'.format(alias, c[alias])
                    self.post_message(channel, text=text)

                elif command == 'list reverse':
                    text = '@{}'.format(handle)
                    c = self.bot.get_config('alias_reverse')
                    for alias in c:
                        text += '\n{}: {}'.format(alias, c[alias])
                    self.post_message(channel, text=text)


            self.set_job_status('Finished')
        except:
            self.log(traceback.format_exc())

