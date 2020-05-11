# ==============================================================================
# About runner.py
# ==============================================================================
#
# This program uses mixer_scraper.py to run its various scraping procedures.
# - it is multithreaded
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
from mixer_scraper import *


# Hyper Parameters -------------------------------------------------------------

# lookup table indicating how many 30 second sleep sessions a thread should take before starting work again
__sleep_period = 30
__sleep = {
    'scrape-livestreams': 2 * 15,   # <- run every 15 minutes
    'scrape-recordings':  2 * 5     # <- run every 5 minutes
}


# Threading Related Variables --------------------------------------------------

worker_threads   = {}     # <- lookup table of {thread_id: thread}
thread_functions = {}     # <- lookup table of {thread_id: function to run for thread }
thread_status    = {}     # <- lookup table of {thread_id: status}, if status == 'end', then the thread is flagged to terminate
__thread_id_livestreams = 'Scrape Livestreams'
__thread_id_recordings  = 'Scrape Recordings'


# Scraper Health Variables -----------------------------------------------------

# for keeping track of process IDs so only 1 version of the scraper can ever run
__pid_filepath = "./tmp/mixer_scraper.pid"

sms = TwilioSMS()


# ==============================================================================
# Scraping Procedures
# ==============================================================================

def thread_scrape_livestreams(thread_id):
    mixer_scraper = MixerScraper()
    while(True):
        print_from_thread(thread_id, "starting work")
        mixer_scraper.procedure_scrape_livestreams()
        print_from_thread(thread_id, "sleeping")
        for i in range(__sleep['scrape-livestreams']):
            if (thread_status[thread_id] == 'end'):
                return
            time.sleep(__sleep_period)


def thread_scrape_recordings(thread_id):
    mixer_scraper = MixerScraper()
    while(True):
        print_from_thread(thread_id, "starting work")
        mixer_scraper.procedure_scrape_recordings()
        print_from_thread(thread_id, "sleeping")
        for i in range(__sleep['scrape-recordings']):
            if (thread_status[thread_id] == 'end'):
                return
            time.sleep(__sleep_period)

# ==============================================================================
# Main
# ==============================================================================

# prints a message with a standardized date-value formatting
def print_from_thread(thread_id, message):
    print('{} [ {:18} ] : {}'.format(datetime.datetime.now().time(), thread_id, message))


def create_worker_thread(thread_id):

    # only allow a thread to start if it is valid
    if (thread_id not in thread_functions):
        return

    # run the thread
    worker_threads[thread_id] = threading.Thread(target=thread_functions[thread_id], args=(thread_id, ))
    thread_status[thread_id]  = 'live'
    worker_threads[thread_id].start()
    return



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
    # remove the ./tmp/mixer_scraper.pid so other programs can restart it
    os.unlink(__pid_filepath)
    print('removed ./tmp/mixer_scraper.pid')

    # let developer know the scraper stopped
    message = 'IndieOutreach Mixer Scraper stopped running at {} on {}'.format(datetime.datetime.now().time(), datetime.date.today())
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



# main function
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
    mixer_db = MixerDB()
    mixer_db.create_tables()

    # start threads on scraping procedures
    create_worker_thread(__thread_id_livestreams)
    create_worker_thread(__thread_id_recordings)

    # send message to developer telling them server has started
    message = "IndieOutreach Mixer Scraper started running at {} on {}".format(datetime.datetime.now().time(), datetime.date.today())
    sms.send(message)

    # set main thread to wait for termination
    signal.signal(signal.SIGINT, stop_scraper)
    signal.signal(signal.SIGTERM, stop_scraper)
    signal.pause()


# Run --------------------------------------------------------------------------

# initialize thread starting functions
thread_functions[__thread_id_recordings]  = thread_scrape_recordings
thread_functions[__thread_id_livestreams] = thread_scrape_livestreams


if (__name__ == '__main__'):
    run()
