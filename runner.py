# ==============================================================================
# About runner.py
# ==============================================================================
#
# This program uses mixer_scraper.py and twitch_scraper.py to run scraping procedures.
# - it is multithreaded
#

# Imports ----------------------------------------------------------------------

import sys
import json
import time

from db_manager import *
from mixer_scraper import *


# ==============================================================================
# Main
# ==============================================================================

def main():
    # initialize databases if need be
    mixer_db = MixerDB()
    mixer_db.create_tables()

    # run scraper
    mixer_scraper = MixerScraper()
    mixer_scraper.set_print_mode(True)
    mixer_scraper.procedure_scrape_recordings()
    return
    while(True):
        mixer_scraper.procedure_scrape_livestreams()
        time.sleep(1 * 60 * 30) # <- 15 minutes

# Run --------------------------------------------------------------------------

if (__name__ == '__main__'):
    main()
