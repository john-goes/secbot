import re
from utils import setInterval
from handlers.base import BaseHandler
import boto3
import os
import requests

class Handler(BaseHandler):

    name = 'Readme.io'

    prefix = 'readmeio'

    patterns = [
        (['{prefix} (?P<command>list pages)'], 'Obtém a lista de páginas'),
        (['{prefix} (?P<command>list changes) (?P<slug>\S+)'], 'Obtém lista de mudanças da <slug>'),
    ]

    def __init__(self, bot, slack, username=None, password=None):
        super().__init__(bot, slack)

        self.directed = True

        if not username:
            self.username = os.environ['READMEIO_USERNAME']
        else:
            self.username = username

        if not password:
            self.password = os.environ['READMEIO_PASSWORD']
        else:
            self.password = password

        self.config_section = 'readmeio'

        self.login()
        self.monitor_changes()

    @setInterval(60)
    def monitor_changes(self):
        session = self.login()

        project_list = self.get_projects(session)

        for project in project_list:
            section = '{}_{}'.format(self.config_section, project['subdomain'])

            try:
                self.bot.get_config(section)
            except KeyError:
                self.bot.create_config_section(section)

            url = 'https://dash.readme.io/api/projects/{subdomain}/v{version}/data'.format(subdomain=project['subdomain'], version=project['stable']['version'])

            r = session.get(url)
            obj = r.json()

            for version in obj['$$versions']:
                ver = version['version']

                url = 'https://dash.readme.io/api/projects/{subdomain}/v{version}/data'.format(subdomain=project['subdomain'], version=ver)

                r = session.get(url)
                obj = r.json()

                for doc in obj['$$docs']:
                    for page in doc['pages']:

                        r = session.get('https://dash.readme.io/api/projects/pagarme/history/{}'.format(page['_id']))

                        pobj = r.json()

                        try:
                            slug_changes = self.bot.get_config(section, page['_id']).split()
                        except:
                            self.bot.write_config(section, page['_id'], '')
                            slug_changes = self.bot.get_config(section, page['_id']).split()

                        for change in pobj:
                            if change['_id'] not in slug_changes:
                                try:
                                    page_url = 'https://dash.readme.io/project/{subdomain}/v{version}/docs/{slug}'.format(subdomain=project['subdomain'], version=ver, slug=page['slug'])
                                    self.post_message('#security_logs', text='Alteração na Documentação: Página `{}` ({}) editada por `{}` ({}) @ {}'.format(page['title'], page_url, change['user']['name'], change['user']['email'], change['createdAt']))
                                except:
                                    traceback.print_exc()
                                finally:
                                    slug_changes.append(change['_id'])
                        self.bot.write_config(section, page['_id'], ' '.join(slug_changes))


    def login(self):
        session = requests.Session()

        payload = {'_csrf': 'undefined', 'email': self.username, 'password': self.password}

        session.get('https://dash.readme.io')

        session.post('https://dash.readme.io/users/session', data=payload)

        return session

    def get_projects(self, session):

        r = session.get('https://dash.readme.io/api/projects')

        return r.json()

    def process(self, channel, user, ts, message, at_bot, command, **kwargs):
        if at_bot:
            handle = self.get_user_handle(user)
            text = None

            session = self.login()
            obj = self.get_projects(session)

            if command == 'list pages':
                msg = '@{}\n'.format(handle)
                for project in obj:
                    msg += '```Project {}```\n'.format(project['subdomain'])

                    url = 'https://dash.readme.io/api/projects/{subdomain}/v{version}/data'.format(subdomain=project['subdomain'], version=project['stable']['version'])

                    r = session.get(url)
                    obj = r.json()

                    for doc in obj['$$docs']:
                        for page in doc['pages']:
                            msg += '{} {} {}\n'.format(page['_id'], page['slug'], page['title'])

                self.post_message(channel, text=msg)

            elif command == 'list changes':
                slug = kwargs['slug']
                r = session.get('https://dash.readme.io/api/projects/pagarme/history/{}'.format(slug))

                pobj = r.json()

                msg = '@{}\n'.format(handle)
                msg += "```Slug {}```\n".format(slug)

                for change in pobj:
                    msg += "[{}] Página atualizada por {} ({})\n".format(change['createdAt'], change['user']['name'], change['user']['email'])

                self.post_message(channel, text=msg)

