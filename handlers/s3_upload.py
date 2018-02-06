import re
from handlers.base import BaseHandler
import boto3
import os
from io import BytesIO

class Handler(BaseHandler):

    name = 'S3 Upload'

    prefix = 'upload'

    patterns = [
        (['<upload>'], 'Envie um arquivo no privado para fazer o upload e receber um link público'),
    ]


    def __init__(self, bot, slack):
        super().__init__(bot, slack)

        self.directed = True

        os.environ['AWS_DEFAULT_REGION'] = 'us-east-1'
        os.environ['AWS_DEFAULT_PROFILE'] = 'test'

        self.credentials = boto3.Session().available_profiles
        self.regions = boto3.Session().get_available_regions('s3')

        self.client = boto3.Session(profile_name='test')

        self.s3 = self.client.resource('s3')


    def process(self, channel, user, ts, message, at_bot, command, **kwargs):
        print(at_bot)
        print(kwargs)

        name, f = self.download_file(kwargs['file_id'])

        file_name = '{}_{}'.format(kwargs['file_id'], name)

        self.s3.Object('pagarme-public-files', file_name).put(Body=BytesIO(f))

        self.post_message(user, 'https://s3.amazonaws.com/pagarme-public-files/{}'.format(file_name))
