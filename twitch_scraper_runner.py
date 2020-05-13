# ==============================================================================
# About: twitch_scraper_runner.py
# ==============================================================================
#
# This program uses twitch_scraper.py to run its various scraping procedures
# - it is multithreaded and meant to work in production
#

# Imports ----------------------------------------------------------------------

import sys

from db_manager import *
from twitch_scraper import *

# ==============================================================================
# Main
# ==============================================================================

def run():

    twitch_db = TwitchDB()
    twitch_db.create_tables()

    scraper = TwitchScraper()
    scraper.set_print_mode(True)
    scraper.procedure_scrape_livestreams()

# Run --------------------------------------------------------------------------

if (__name__ == '__main__'):
    run()
