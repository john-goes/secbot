import re
from handlers.base import BaseHandler
import boto3
import os

class Handler(BaseHandler):

    name = 'AWS'

    prefix = 'aws'

    patterns = [
        (['{prefix} (?P<command>list instances)'], 'Obtém a lista das instâncias e suas roles'),
        (['{prefix} (?P<command>whois) (?P<address>\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})'], 'Obtém a role da máquina <address>'),
        (['{prefix} (?P<command>whois) (?P<name>\S+)'], 'Obtém os IPs das máquinas com a role <name>'),
    ]

    def __init__(self, bot, slack):
        super().__init__(bot, slack)

        self.directed = True

        os.environ['AWS_DEFAULT_REGION'] = 'us-east-1'
        os.environ['AWS_DEFAULT_PROFILE'] = 'pagarme-pci-secbot'

        self.client = boto3.client('ec2')

    def process(self, channel, user, ts, message, at_bot, command, **kwargs):
        if at_bot:
            handle = self.get_user_handle(user)
            text = None

            obj = client.describe_instances()

            instances = {}
            instances_reverse = {}

            for res in obj['Reservations']:
                for instance in res['Instances']:
                    name = [x.get('Value') for x in instance['Tags'] if x.get('Key') == 'Name']
                    ips = []
                    for net in instance['NetworkInterfaces']:
                        try:
                            ips.append(net['PrivateIpAddress'])
                            instances[net['PrivateIpAddress']] = name[0]
                        except:
                            continue
                    instances_reverse[name[0]] = ips

            if command == 'list instances':
                msg = '@{}'.format(handle)
                for instance in instances.keys():
                    msg += '{} - {}\n'.format(instance, instances[instance])
                self.post_message(channel, text=msg)
            elif command == 'whois':
                if 'address' in kwargs:
                    if kwargs['address'] in instances:
                        self.post_message(channel, text='@{} A máquina {} possui a role {}'.format(handle, kwargs['address'], instances[kwargs['address']]))
                    else:
                        self.post_message(channel, text='@{} Máquina desconhecida: {}'.format(handle, kwargs['address']))
                elif 'name' in kwargs:
                    found = False
                    for key in instances_reverse.keys():
                        if kwargs['name'] in key:
                            self.post_message(channel, text='@{} A role {} possui os IPs {}'.format(handle, key, instances_reverse[key]))
                            found = True
                    if not found:
                        self.post_message(channel, text='@{} Role desconhecida: {}'.format(handle, kwargs['name']))
