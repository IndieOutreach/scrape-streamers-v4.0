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

from db_manager import *
from mixer_scraper import *


# ==============================================================================
# Main
# ==============================================================================

def main():
    credentials = json.load(open('credentials.json'))
    mixer_db = MixerDB()
    mixer_db.create_tables()

# Run --------------------------------------------------------------------------

if (__name__ == '__main__'):
    main()
