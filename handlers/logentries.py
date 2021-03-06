import re
import requests
import traceback
import os
import base64
import hashlib
import hmac

from datetime import datetime

from handlers.base import BaseHandler

class Handler(BaseHandler):

    name = 'Logentries'

    prefix = 'logentries'

    patterns = [
        (['(?P<command>desligar) (?P<users>.*)', '(?P<command>)terminate (?P<users>.*)', '{prefix} (?P<command>)terminate (?P<users>.*)'], 'Desliga um funcionário'),
    ]

    def __init__(self, bot, slack, api_key=None, api_key_id=None, account_id=None):

        super().__init__(bot, slack)

        self.directed = True

        if not api_key:
            self.api_key = os.environ.get('LOGENTRIES_API_KEY')
        if not api_key_id:
            self.api_key_id = os.environ.get('LOGENTRIES_API_KEY_ID')
        if not account_id:
            self.account_id = os.environ.get('LOGENTRIES_ACCOUNT_ID')

        self.set_job_status('Initialized')

    def gensignature(self, api_key, date, content_type, request_method, query_path, request_body):
        encoded_hashed_body = base64.b64encode(hashlib.sha256(request_body.encode('utf-8')).digest())
        canonical_string = request_method + content_type + date + query_path + encoded_hashed_body.decode('utf-8')

        # Create a new hmac digester with the api key as the signing key and sha1 as the algorithm
        digest = hmac.new(api_key.encode('utf-8'), digestmod=hashlib.sha1)
        digest.update(canonical_string.encode('utf-8'))

        return digest.digest()

    def create_headers(self, uri):
        date_h = datetime.utcnow().strftime("%a, %d %b %Y %H:%M:%S GMT")
        content_type_h = "application/json"
        method = 'GET'
        action = uri
        signature = self.gensignature(self.api_key, date_h, content_type_h, method, action, '')
        headers = {
            "Date": date_h,
            "Content-Type": content_type_h,
            "authorization-api-key": '{}:{}'.format(self.api_key_id.encode('utf8'), base64.b64encode(signature))
        }
        return headers

    def request(self, method, uri):
        url = "https://rest.logentries.com/{}".format(uri)
        r = requests.request(method, url, headers=self.create_headers(uri))

        print(r.content)

        return r.json()

    def get_users(self):
        r = self.request('GET', 'management/accounts/{}/users'.format(self.account_id))

        return r['user']

    def get_user(self, email):
        ul = self.get_users()

        for u in ul:
            if u['email'] == email:
                return u

    def delete_user(self, email):
        u = self.get_user(email)

        r = self.request('DELETE', 'management/accounts/{}/user/{}'.format(self.account_id, u['id']))

        return True if r.status_code == 200 else False

    def process(self, channel, user, ts, message, at_bot, command, **kwargs):
        if at_bot:
            user_handle = self.get_user_handle(user)

            if command in ['desligar', 'terminate']:
                self.set_job_status('Processing')

                if not self.authorized(user_handle, 'Terminator'):
                    self.set_job_status('Unauthorized')
                    self.post_message(channel=channel, text='@{} Unauthorized'.format(user_handle))
                    return False

                to_remove = [x for x in kwargs['users'].split() if '@' in x]

                for r in to_remove:
                    try:
                        c = self.bot.get_config('alias_reverse', r)
                        if c:
                            if c not in to_remove:
                                to_remove.append(c)
                    except:
                        continue

                for r in to_remove:
                    try:
                        c = self.bot.get_config('alias', r).split()
                        for x in c:
                            if x not in to_remove:
                                to_remove.append(x)
                    except:
                        continue


                self.log('@{}: {}'.format(user_handle, message))

                self.post_message(channel=channel, text='@{} Removendo usuários: {}'.format(user_handle, ', '.join(to_remove)))

                for username in to_remove:
                    try:
                        self.delete_user(username)
                        self.log('Deleted user {}'.format(username))
                    except:
                        self.log(traceback.format_exc())
                        continue

            self.set_job_status('Finished')
            self.set_job_end(datetime.now())


