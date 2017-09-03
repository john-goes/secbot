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
        '\d{13,16}',
        '(\d.?){13,16}',
        '.*\d.*',
        '.*(zero|um|dois|tres|três|quatro|cinco|seis|sete|oito|nove|dez).*',
        '.*(zero|one|two|three|four|five|six|seven|eight|nine|ten).*',
        '.*(cero|uno|dos|tres|cuatro|cinco|seis|siete|ocho|nueve|die).*',
    ]

    dall= {}
    number_portuguese = {'zero': 0, 'um': 1, 'dois': 2, 'tres': 3, 'três': 3, 'quatro': 4, 'cinco': 5, 'seis': 6, 'sete': 7, 'oito': 8, 'nove': 9, 'dez': 10}
    number_english = {'zero': 0 , 'one': 1, 'two': 2, 'three': 3, 'four': 4, 'five': 5, 'six': 6, 'seven': 7, 'eight': 8, 'nine': 9, 'ten': 10}
    number_spanish = {'cero': 0, 'uno': 1, 'dos': 2, 'tres': 3, 'cuatro': 4, 'cinco': 5, 'seis': 6, 'siete': 7, 'ocho': 8, 'nueve': 9, 'diez': 10}

    dall.update(**number_portuguese)
    dall.update(**number_english)
    dall.update(**number_spanish)

    def process(self, channel, user, ts, message, at_bot, extra):
        self.set_job_status('Processing')
        response = None

        handle = self.get_user_handle(user)

        g = message
        for k in self.dall.keys():
            g = g.replace(k, str(self.dall[k]))
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
                self.post_message(channel=channel, text=response)

        self.set_job_status('Finished')
        self.set_job_end(datetime.now())

    def check(self, card):
        return verify(card)
