from luhn import *
import re
from handlers.base import BaseHandler
from datetime import datetime

class Handler(BaseHandler):

    name = 'Credit Card'

    patterns = [
        '4[0-9]{12}(?:[0-9]{3})?',
        '(?:5[1-5][0-9]{2}|222[1-9]|22[3-9][0-9]|2[3-6][0-9]{2}|27[01][0-9]|2720)[0-9]{12}',
        '3[47][0-9]{13}',
        '3(?:0[0-5]|[68][0-9])[0-9]{11}',
        '6(?:011|5[0-9]{2})[0-9]{12}',
        '(?:2131|1800|35\d{3})\d{11}',
     #   '\d{13,16}',
     #   '(\d{4,6}.?){4}',
    ]

    def process(self, channel, user, ts, message, at_bot, command, **kwargs):
        self.set_job_status('Processing')
        response = None

        handle = self.get_user_handle(user)

        g = message
        g = ''.join(re.findall(r'\d+', g))
        if len(g) >= 13:
            c = self.check(g)
            if c:
                self.log('Card posted on {} by {}'.format(channel, handle))
                self.delete(channel=channel, ts=ts)
                self.log('Message deleted')

                self.post_ephemeral(channel=channel, user=user,
                        text="O PCI determina que dados sensíveis de cartão (PAN e CVV) não devem ser compartilhados em mídias como email, SMS, Slack, Telegram, Whatsapp e outros IMs. Por favor, respeite essa regra.")

                response = 'Sua Violação do PCI  X  minha Regex Pica, os dois a 80 km/h, tu acha que vai ficar um do lado do outro? Creio que não.'
                try:
                    response = '@{} {}'.format(handle, response)
                except:
                    pass

            if response:
                pass
                #self.post_message(channel=channel, text=response)

        self.set_job_status('Finished')
        self.set_job_end(datetime.now())

    def check(self, card):
        return verify(card)
