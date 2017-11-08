import os
import random
import re
from handlers.base import BaseHandler
import traceback

class Handler(BaseHandler):

    name = 'Suicide'

    prefix = 'suicide'

    patterns = [
        (['(?P<command>suicide)'], 'Die'),
        (['(?P<command>die)'], 'Die'),
    ]

    def __init__(self, bot, slack):
        super().__init__(bot, slack)

        self.directed = True

        #self.job_id = '0'


    phrases = [
            'That is not dead which can eternal lie, And with strange aeons even death may die.',
            'So long, and thanks for all the fish',
            'Live long and prosper!',
            'Thank Heaven! the crisis, The danger, is past, and the lingering illness, is over at last, and the fever called "Living" is conquered at last.',
            'No one is dead until the ripples they cause in the world die away.',
            'Why should I fear death? If I am, death is not. If death is, I am not. Why should I fear that which cannot exist when I do?',
            'The ones that love us never really leave.',
            'End? No, the journey doesn\'t end here. Death is just another path, one that we all must take. The grey rain-curtain of this world rolls back, and all turns to silver glass, and then you see it.',
            'It is the unknown we fear when we look upon death and darkness, nothing more.',
            'They say you die twice. One time when you stop breathing and a second time, a bit later on, when somebody says your name for the last time.',
            'Death is but a door, time is but a window. I\'ll be back!',
            'You needn\'t die happy when your time comes, but you must die satisfied, for you have lived your life from the beginning to the end...',
            'The boundaries which divide Life from Death are at best shadowy and vague. Who shall say where the one ends, and the other begins?',
            'I do not fear death. I had been dead for billions and billions of years before I was born, and had not suffered the slightest inconvenience from it.',
            'How can the dead be truly dead when they still live in the souls of those who are left behind?'
            ]

    def process(self, channel, user, ts, message, at_bot, command, **kwargs):
        try:
            if at_bot:
                handle = self.get_user_handle(user)

                if command in ['die', 'suicide']:
                    if self.authorized(handle, 'Killer'):
                        self.post_message(channel, random.choice(self.phrases))
                        os._exit(1)
        except:
            self.log(traceback.format_exc())

