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
import argparse

from db_manager import *
from twilio_sms import *


# Constants --------------------------------------------------------------------

sms = TwilioSMS()

TWITCH_TABLE_NAMES = [
    'streamers',
    'followers',
    'total_views',
    'broadcaster_type',
    'livestream_snapshots',
    'livestreams',
    'games',
    'game_snapshots',
    'tags',
    'logs'
]

# NOTE: the following tables are not included right now in the status checks because they don't have scraping procedures
# they are, however, technically instantiated tables
#   - 'videos',
#   - 'no_videos',

# Command line Arguments -------------------------------------------------------

__twilio_description = """If the -t flag is activated, status updates will be sent to the admin via SMS.  """

parser = argparse.ArgumentParser()
parser.add_argument('-t', '--twilio', dest='twilio', action='store_true', help=__twilio_description)
args = parser.parse_args()
if (args.twilio):
    #sms.set_mode(True)
    print('sms currently hardcoded to not send')


# Main -------------------------------------------------------------------------

# checks twitch.db/logs and texts the admin if a scraping procedure hasn't logged results in a certain amount of time
def handle_procedure_logs():
    # get most recent logs
    db = TwitchDB()
    conn = db.get_connection()
    logs = db.get_most_recent_logs(conn)
    conn.close()

    needs_attention = []
    current_time = int(time.time())
    for log_id, log_time in logs.items():
        if (current_time - log_time > 1 * 60 * 60 * 1):
            needs_attention.append(log_id)

    # only send a text if necessary
    if (len(needs_attention) > 0):
        message = f"The following Twitch scraping procedures have not logged their results in the last 2 hours: {needs_attention}"
        sms.send(message)
    return


# calls COUNT(*) on different tables in the twitch.db
def count_tables():

    needs_attention = []

    # Get COUNT(*) values from twitch.db
    twitch_db = TwitchDB()
    conn = twitch_db.get_connection()
    counts = {}
    for table in TWITCH_TABLE_NAMES:
        for row in conn.execute(f"SELECT COUNT(*) FROM {table};"):
            counts[table] = row[0]
    conn.close()


    # check the previous counts
    db = CountLogDB()
    prev_counts = db.get_most_recent_counts()
    for table_name in counts:
        if (table_name in prev_counts):
            value_changing = False
            for value in prev_counts[table_name]:
                if (value != counts[table_name]):
                    value_changing = True

            if (value_changing != True and len(prev_counts[table_name]) > 10):
                needs_attention.append(table_name)

    # send messages if necessary
    if (len(needs_attention) > 0):
        message = f"The following twitch.db tables have not changed COUNT(*) in a while: {needs_attention}"
        sms.send(message)


    # save counts for future
    db.insert_counts(counts)
    return

def run():
    handle_procedure_logs()
    count_tables()


# Run --------------------------------------------------------------------------

if (__name__ == '__main__'):
    run()
    #while(True):
    #    print('.')
    #    time.sleep(1 * 60 * 15) # <- 15 minutes
