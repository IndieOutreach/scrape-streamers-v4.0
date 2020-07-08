# ==============================================================================
# About: twitch_scraper_runner.py
# ==============================================================================
#
# This program uses twitch_scraper.py to run its various scraping procedures
# - it is multithreaded and meant to work in production
#

# Imports ----------------------------------------------------------------------

import os
import sys
import json
import time
import signal
import atexit
import argparse
import datetime
import threading

from db_manager import *
from twilio_sms import *
from twitch_scraper import *


# Threading Related Variables --------------------------------------------------

worker_threads   = {}     # <- lookup table of {thread_id: thread}
thread_status    = {}     # <- lookup table of {thread_id: status}, if status == 'end', then the thread is flagged to terminate
__thread_id_livestream_snapshots = 'Scrape Livestreams Snapshots'
__thread_id_recordings           = 'Scrape Recordings'
__thread_id_inactive             = 'Scrape Inactive'
__thread_id_followers            = 'Scrape Followers'
__thread_id_compress_livestreams = 'Compress Livestream Snapshots'

__MAX_THREAD_ID_LENGTH = 0
for id in [
        __thread_id_inactive,
        __thread_id_followers,
        __thread_id_recordings,
        __thread_id_livestream_snapshots,
        __thread_id_compress_livestreams
    ]:
    __MAX_THREAD_ID_LENGTH = len(id) if (len(id) >  __MAX_THREAD_ID_LENGTH) else  __MAX_THREAD_ID_LENGTH


# lookup table indicating how many 30 second sleep sessions a thread should take before starting work again
__sleep_period = 30
__sleep = {
    __thread_id_livestream_snapshots: 2 * 15,   # <- run every 15 minutes
    __thread_id_recordings          : 2 * 5,    # <- run every 5 minutes
    __thread_id_inactive            : 2 * 15,   # <- run every 15 minutes,
    __thread_id_followers           : 2 * 5,    # <- run every 5 minutes
    __thread_id_compress_livestreams: 2 * 1     # <- run every minute
}


# Scraper Health Variables -----------------------------------------------------

# for keeping track of process IDs so only 1 version of the scraper can ever run
__pid_filepath = "./tmp/twitch_scraper.pid"

sms = TwilioSMS()


# ==============================================================================
# Threads: Scraping Procedures
# ==============================================================================


# Functions for Threads --------------------------------------------------------

def thread_scrape_procedure(thread_id, scraping_procedure):
    while(True):
        print_from_thread(thread_id, "starting work")
        scraping_procedure()
        print_from_thread(thread_id, "sleeping")
        for i in range(__sleep[thread_id]):
            if (thread_status[thread_id] == 'end'):
                return
            time.sleep(__sleep_period)



# prints a message with a standardized date-value formatting
def print_from_thread(thread_id, message):
    thread_id_length = '{:' + str(__MAX_THREAD_ID_LENGTH) +'}'
    thread_id = thread_id_length.format(thread_id)
    print(f'{datetime.datetime.now().time()} [ {thread_id} ] : { message}')


# creates a new worker thread
def create_worker_thread(thread_id):

    # create the scraper for this thread
    twitch_scraper = TwitchScraper()
    procedure_to_run = False
    if (thread_id == __thread_id_livestream_snapshots):
        procedure_to_run = twitch_scraper.procedure_scrape_livestream_snapshots
    elif (thread_id == __thread_id_followers):
        procedure_to_run = twitch_scraper.procedure_scrape_followers
    elif (thread_id == __thread_id_inactive):
        procedure_to_run = twitch_scraper.procedure_scrape_inactive
    elif (thread_id == __thread_id_compress_livestreams):
        procedure_to_run = twitch_scraper.procedure_compress_livestreams
    else:
        print('Invalid thread ID found: ', thread_id)
        return

    # run the thread
    worker_threads[thread_id] = threading.Thread(target=thread_scrape_procedure, args=(thread_id, procedure_to_run))
    thread_status[thread_id]  = 'live'
    worker_threads[thread_id].start()
    return


# Functions for Starting / Stopping --------------------------------------------

# function that allows all threads to terminate gracefully
def stop_scraper(sig, frame):
    print('\n-------------------------------------------------')
    print("Shutting Down")
    print('-------------------------------------------------')
    print('Please wait for all threads to finish their commits')
    print('This may take a while...\n')

    # signal for threads to terminate
    for thread_id in thread_status:
        thread_status[thread_id] = 'end'

    # wait for threads to join
    for thread_id in worker_threads:
        print_from_thread(thread_id, "waiting for thread to finish work...")
        worker_threads[thread_id].join()
        print_from_thread(thread_id, "terminated")

    print('shut down complete!\n')
    sys.exit(0)


# function that gets run on exit
def on_program_shutdown():
    # remove the ./tmp/twitch_scraper.pid so other programs can restart it
    os.unlink(__pid_filepath)
    print('removed ./tmp/twitch_scraper.pid')

    # let developer know the scraper stopped
    message = 'IndieOutreach Twitcher Scraper stopped running at {} on {}'.format(datetime.datetime.now().time(), datetime.date.today())
    sms.send(message)
    return


# checks to see if program is already running and quits if so
def check_if_program_already_running():
    pid = str(os.getpid())
    if (os.path.isfile(__pid_filepath)):
        print("The scraper is already running in another process. ")
        with open(__pid_filepath) as f:
            for line in f:
                print('pid:', line)
        return True

    f = open(__pid_filepath, 'w')
    f.write(pid)
    f.close()
    return False


# ==============================================================================
# Main
# ==============================================================================


def run():

    # get command line arguments -> production mode
    parser = argparse.ArgumentParser()
    parser.add_argument('-t', '--twilio', dest='twilio', action='store_true', help='If true, server will send text messages to the number specified in credentials on scraper start and termination.')
    args = parser.parse_args()
    if (args.twilio):
        sms.set_mode(True)

    # because this runs on a cron job, make sure two instances of the scraper can't be active at the same time
    if check_if_program_already_running():
        sys.exit(0)
    atexit.register(on_program_shutdown)

    # initialize databases if need be
    twitch_db = TwitchDB()
    twitch_db.create_tables()

    # start threads on scraping procedures
    create_worker_thread(__thread_id_livestream_snapshots)
    create_worker_thread(__thread_id_followers)
    create_worker_thread(__thread_id_inactive)
    create_worker_thread(__thread_id_compress_livestreams)

    # send message to developer telling them server has started
    message = "IndieOutreach Twitch Scraper started running at {} on {}".format(datetime.datetime.now().time(), datetime.date.today())
    sms.send(message)

    # set main thread to wait for termination
    signal.signal(signal.SIGINT, stop_scraper)
    signal.signal(signal.SIGTERM, stop_scraper)
    signal.pause()
    return


def test_run():
    twitch_scraper = TwitchScraper()
    twitch_scraper.procedure_scrape_inactive()
    print('DONE')

# Run --------------------------------------------------------------------------

if (__name__ == '__main__'):
    #test_run()
    run()
