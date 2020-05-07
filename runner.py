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
    mixer_api = MixerAPI(credentials['mixer'])
    channels = MixerChannels()
    channels, page, timelogs = mixer_api.scrape_live_channels(MixerChannels(), 0)
    for channel in channels.channels:
        print(channel)

# Run --------------------------------------------------------------------------

if (__name__ == '__main__'):
    main()
