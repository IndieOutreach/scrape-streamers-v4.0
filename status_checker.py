# ==============================================================================
# About: status_checker.py
# ==============================================================================
# status_checker.py will check log files in ./data/twitch.db to determine the health of the various scraping procedure threads
# If a procedure hasn't logged a result in too long, it will send a text message to the admin
#   -> this program is run on a cron job
#   -> it terminates after starting

# Imports ----------------------------------------------------------------------

import sys
import time

from db_manager import *
from twilio_sms import *

# Main -------------------------------------------------------------------------

def run():

    # get most recent logs
    db = TwitchDB()
    conn = db.get_connection()
    logs = db.get_most_recent_logs(conn)
    conn.close()

    needs_attention = []
    current_time = int(time.time())
    for log_id, log_time in logs.items():
        if (current_time - log_time > 1 * 60 * 60 * 2):
            needs_attention.append(log_id)

    # only send a text if necessary
    if (len(needs_attention) > 0):
        sms = TwilioSMS()
        sms.set_mode(True)
        message = f"The following Twitch scraping procedures have not logged their results in the last 2 hours: {needs_attention}"
        sms.send(message)
        print(message)

# Run --------------------------------------------------------------------------

if (__name__ == '__main__'):
    run()
