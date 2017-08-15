import os
import time
from slackclient import SlackClient
import re
from credit_card import check, patterns
from utils import setInterval


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

# starterbot's ID as an environment variable
BOT_ID = get_id()

# constants
AT_BOT = "<@" + BOT_ID + ">"

# instantiate Slack & Twilio clients

def handle_command(command, channel, ts, user):
    """
        Receives commands directed at the bot and determines if they
        are valid commands. If so, then acts on the commands. If not,
        returns back what it needs for clarification.
    """
    response = None
    for ptr in patterns:
        m = re.findall(ptr, command.replace(' ', ''))
        if m:
            for g in m:
                c = check(g)
                if c:
                    print('[!] Card posted on {}'.format(channel))
                    slack_client.api_call("chat.delete", channel=channel, ts=ts, as_user=True)

                    slack_client.api_call("chat.postEphemeral", channel=channel,
                      text="O PCI determina que dados sensíveis de cartão (PAN e CVV) não devem ser compartilhados em mídias como email, SMS, Slack, Telegram, Whatsapp e outros IMs. Por favor, respeite essa regra.", as_user=True, user=user)

                    try:
                        user_handler = slack_client.api_call("users.info", user=user)['user']['name']
                        response = '@{} DONT POST CREDIT CARDS!!!!11!!!!!!ELEVENTh!!'.format(user_handler)
                    except:
                        response = 'DONT POST CREDIT CARDS!!!!11!!!!!!ELEVENTh!!'

    if response:
        slack_client.api_call("chat.postMessage", channel=channel,
                          text=response, as_user=True, link_names=True)


def parse_slack_output(slack_rtm_output):
    """
        The Slack Real Time Messaging API is an events firehose.
        this parsing function returns None unless a message is
        directed at the Bot, based on its ID.
    """
    output_list = slack_rtm_output
    if output_list and len(output_list) > 0:
        for output in output_list:
            #if output and 'text' in output and AT_BOT in output['text']:
                # return text after the @ mention, whitespace removed
            if output and 'text' in output and output.get('user') and output['user'] != BOT_ID:
                if AT_BOT in output['text']:
                    return output['text'].split(AT_BOT)[1].strip().lower(), \
                       output['channel'], output['ts'], output['user']
                else:
                    return output['text'].strip().lower(), \
                       output['channel'], output['ts'], output['user']
    return None, None, None, None

@setInterval(10)
def join_channels():
    channels = slack_client.api_call("channels.list", exclude_members=True, exclude_archived=True)
    for ch in channels['channels']:
        if not ch['is_member']:
            print('[*] Joining #{}'.format(ch['name']))
            slack_client.api_call("channels.join", name=ch['name'], validate=True)


if __name__ == "__main__":
    READ_WEBSOCKET_DELAY = 1 # 1 second delay between reading from firehose
    if slack_client.rtm_connect():
        print("StarterBot connected and running!")
        ch_joiner = join_channels()
        while True:
            command, channel, ts, user = parse_slack_output(slack_client.rtm_read())
            if command and channel:
                handle_command(command, channel, ts, user)
            time.sleep(READ_WEBSOCKET_DELAY)
    else:
        print("Connection failed. Invalid Slack token or bot ID?")
