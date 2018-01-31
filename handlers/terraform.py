import re
from github import Github
import requests
import traceback
import os
from utils import setInterval

from python_terraform import *

from datetime import datetime

from handlers.base import BaseHandler

class Handler(BaseHandler):

    name = 'Terraform'

    prefix = 'terraform'

    patterns = [
        (['{prefix} (?P<command>plan) (?P<repo>.*) (?P<path>.)'], 'Plans a Terraform setup'),
    ]

    def __init__(self, bot, slack, working_directory='/tmp':

        super().__init__(bot, slack)

        self.directed = True

        self.working_directory = '/tmp'

    def process(self, channel, user, ts, message, at_bot, command=None, **kwargs):
        try:
            if at_bot:
                user_handle = self.get_user_handle(user)
                if command in ['plan']:
                    self.set_job_status('Processing')

                    self.log('@{}: {}'.format(user_handle, message))


                self.set_job_status('Finished')
                self.set_job_end(datetime.now())
        except:
            self.log(traceback.format_exc())


