import os
from slackclient import SlackClient


BOT_NAME = 'secbot'

slack_client = SlackClient(os.environ.get('SLACK_BOT_TOKEN'))


def get_id():
    api_call = slack_client.api_call("users.list")
    if api_call.get('ok'):
        # retrieve all users so we can find our bot
        users = api_call.get('members')
        for user in users:
            if 'name' in user and user.get('name') == BOT_NAME:
                return user.get('id')
    else:
        return None
