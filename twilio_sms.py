# ==============================================================================
# About: twilio_sms.py
# ==============================================================================
#
# twilio_sms.py contains the TwilioSMS class, a simple wrapper for sending texts using the Twilio API
# - this class can be used to send SMS updates to a specified phone number with updates about scraper status
#

# Imports ----------------------------------------------------------------------

import json
from twilio.rest import Client

# ==============================================================================
# Class: TwilioSMS
# ==============================================================================

class TwilioSMS():
    def __init__(self):
        credentials = json.load(open('credentials.json'))
        self.twilio = Client(credentials['twilio']['account_sid'], credentials['twilio']['auth_token'])
        self.user_number   = credentials['twilio']['user_number']
        self.twilio_number = credentials['twilio']['twilio_number']
        self.active = False # <- if true, will send messages as SMS, otherwise, print to stdout
        return

    def send(self, message):
        if (self.active):
            message = self.twilio.messages \
                .create(
                     body=message,
                     from_=self.twilio_number,
                     to=self.user_number
                 )
        else:
            print("[SMS]", message)

    def set_mode(self, mode):
        self.active = mode == True

# ==============================================================================
# Main
# ==============================================================================

def main():
    sms = TwilioSMS()
    sms.send("Hello from twilio_sms.py")

# Run --------------------------------------------------------------------------

if (__name__ == '__main__'):
    main()
