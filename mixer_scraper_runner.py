# ==============================================================================
# About runner.py
# ==============================================================================
#
# This program uses mixer_scraper.py to run its various scraping procedures.
# - it is multithreaded
#

# Imports ----------------------------------------------------------------------

import sys
import json
import time
import datetime
import threading

from db_manager import *
from mixer_scraper import *


# Hyper Parameters -------------------------------------------------------------

__sleep = {
    'main_thread':        1 * 60 * 30,   # <- run every 30 minutes
    'scrape_livestreams': 1 * 60 * 1,   # <- run every 15 minutes
    'scrape_recordings':  1 * 60 * 1    # <- run every 10 minutes
}


# Threading Related Variabels --------------------------------------------------

worker_threads = {}       # <- lookup table of {thread_id: thread}
thread_functions = {}     # <- lookup table of {thread_id: function to run for thread }
__thread_id_livestreams = 'Scrape Livestreams'
__thread_id_recordings  = 'Scrape Recordings'


# ==============================================================================
# Scraping Procedures
# ==============================================================================

def thread_scrape_livestreams(thread_id):
    mixer_scraper = MixerScraper()
    while(True):
        print_from_thread(thread_id, "starting work")
        mixer_scraper.procedure_scrape_livestreams()
        print_from_thread(thread_id, "sleeping")
        time.sleep(__sleep['scrape_livestreams'])


def thread_scrape_recordings(thread_id):
    mixer_scraper = MixerScraper()
    while(True):
        print_from_thread(thread_id, "starting work")
        mixer_scraper.procedure_scrape_recordings()
        print_from_thread(thread_id, "sleeping")
        time.sleep(__sleep['scrape_recordings'])

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
    worker_threads[thread_id].start()
    return



def run():

    # initialize databases if need be
    mixer_db = MixerDB()
    mixer_db.create_tables()

    # start threads on scraping procedures
    create_worker_thread(__thread_id_livestreams)
    create_worker_thread(__thread_id_recordings)
    while(True):
        time.sleep(__sleep['main_thread'])


# Run --------------------------------------------------------------------------

# initialize thread starting functions
thread_functions[__thread_id_recordings]  = thread_scrape_recordings
thread_functions[__thread_id_livestreams] = thread_scrape_livestreams

if (__name__ == '__main__'):
    run()
