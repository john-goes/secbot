import re
from handlers.base import BaseHandler
import boto3
import os

class Handler(BaseHandler):

    name = 'AWS'

    prefix = 'aws'

    patterns = [
        (['{prefix} (?P<command>list instances)'], 'Obtém a lista das instâncias e suas roles'),
        (['{prefix} (?P<command>whoisip) (?P<address>\S+)'], 'Obtém a role da máquina <address>'),
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

            obj = self.client.describe_instances()

            instances = {}
            instances_reverse = {}

            for res in obj['Reservations']:
                for instance in res['Instances']:
                    name = [x.get('Value') for x in instance.get('Tags', []) if x.get('Key') == 'Name']
                    for net in instance['NetworkInterfaces']:
                        try:
                            if name:
                                if not name[0] in instances_reverse:
                                    instances_reverse[name[0]] = []
                                instances_reverse[name[0]].append(net['PrivateIpAddress'])
                            if name:
                                instances[net['PrivateIpAddress']] = name[0]
                            else:
                                instances[net['PrivateIpAddress']] = 'UNNAMED'
                        except:
                            continue

            if command == 'list instances':
                msg = '@{}\n'.format(handle)
                for instance in instances.keys():
                    msg += '{} - {}\n'.format(instance, instances[instance])
                self.post_message(channel, text=msg)
            elif command == 'whoisip':
                if 'address' in kwargs:
                    for addr in kwargs['address'].split():
                        if addr in instances:
                            self.post_message(channel, text='@{} A máquina {} possui a role {}'.format(handle, addr, instances[addr]))
                        else:
                            self.post_message(channel, text='@{} Máquina desconhecida: {}'.format(handle, addr))
            elif command == 'whois':
                if 'name' in kwargs:
                    found = False
                    for name in kwargs['name'].split():
                        for key in instances_reverse.keys():
                            if name in key:
                                self.post_message(channel, text='@{} A role {} possui os IPs {}'.format(handle, key, instances_reverse[key]))
                                found = True
                        if not found:
                            self.post_message(channel, text='@{} Role desconhecida: {}'.format(handle, name))
