# ==============================================================================
# About: twitch_scraper.py
# ==============================================================================
#
# twitch_scraper.py contains all of the classes involved with scraping the Twitch API
# - TwitchAPI       - a wrapper for the Twitch API
# - TwitchScraper   - implements the scraping procedures using TwitchAPI
# - Twitch<Object>s - various objects from Twitch's API that are held in memory and then dumped to the db
#

# Imports ----------------------------------------------------------------------

import sys
import json
import time
import requests

from logs import *
from db_manager import *

# ==============================================================================
# Classes: Twitch<Objects>
# ==============================================================================

# TwitchLivestream -------------------------------------------------------------

class TwitchLivestream():

    def __init__(self, data, source):
        if (source == 'api/livestreams'):
            self.__load_from_api_livestreams_object(data)
            self.valid = True
        else:
            self.valid = False
        return

    def is_valid(self):
        return self.valid

    def __load_from_api_livestreams_object(self, obj):
        self.id = int(obj['id'])
        self.user_id = int(obj['user_id'])
        self.user_name = obj['user_name']
        self.game_id = int(obj['game_id']) if (obj['game_id'] != '') else -1
        self.viewer_count = int(obj['viewer_count'])
        self.language = obj['language']
        self.started_at = obj['started_at']
        self.tag_ids = obj['tag_ids']


    # returns a list of tag ids and an empty list if there are none
    def get_tag_ids(self):
        if (isinstance(self.tag_ids, list)):
            return self.tag_ids
        return []

# TwitchLivestreams ------------------------------------------------------------

class TwitchLivestreams():

    def __init__(self):
        self.livestreams = {}
        self.livestreams_no_viewers = {}
        return


    def get(self, id):
        if (id in self.livestreams):
            return self.livestreams[id]
        elif (id in self.livestreams_no_viewers):
            return self.livestreams_no_viewers[id]
        return False

    def get_num_livestreams(self):
        return len(self.livestreams) + len(self.livestreams_no_viewers)


    def add_from_api(self, obj):
        livestream = TwitchLivestream(obj, 'api/livestreams')
        if (livestream.is_valid()):
            if (livestream.viewer_count > 0):
                self.livestreams[livestream.id] = livestream
            else:
                self.livestreams_no_viewers[livestream.id] = livestream
        return

    # returns all tag_ids in a list
    def get_all_tag_ids(self):
        ids_lookup = {}

        def get_tags_from_livestreams(lookup, livestreams):
            for livestream_id, livestream in livestreams.items():
                for tag in livestream.get_tag_ids():
                    if (tag not in lookup):
                        lookup[tag] = True
            return lookup

        ids_lookup = get_tags_from_livestreams(ids_lookup, self.livestreams)
        ids_lookup = get_tags_from_livestreams(ids_lookup, self.livestreams_no_viewers)
        return list(ids_lookup.keys())


# ==============================================================================
# Class: TwitchAPI
# ==============================================================================

class TwitchAPI():

    def __init__(self, credentials):
        self.helix_client_id = credentials['helix']['client_id']
        self.__set_oauth(credentials['helix'])
        return

    # OAuth2 and Headers -------------------------------------------------------

    # Twitch uses OAuth2, so we need to grab an access token
    def __set_oauth(self, credentials):
        params = {
            'client_id': credentials['client_id'],
            'client_secret': credentials['client_secret'],
            'grant_type': 'client_credentials'
        }
        r = requests.post('https://id.twitch.tv/oauth2/token', params=params)
        if (r.status_code == 200):
            data = r.json()
            self.access_token = data['access_token']
        else:
            self.access_token = False
            print('FALSE')


    def __get_helix_headers(self):
        return {'Authorization': 'Bearer ' + self.access_token, 'Client-ID': self.helix_client_id}


    # Requests and Sleeping ----------------------------------------------------

    def __get(self, url, params, headers, timelogs, request_type):
        if (timelogs != False):
            timelogs.start_action(request_type)
        r = requests.get(url, params=params, headers=headers)
        if (timelogs != False):
            timelogs.end_action(request_type)
        return r, timelogs

    def __sleep(self, header, min_sleep = 0):
        if (('ratelimit_remaining' in header) and (header['ratelimit_remaining'] <= 1)):
            print('sleeping...')
            time.sleep(1)
        elif (min_sleep > 0):
            time.sleep(min_sleep)


    # Scraping -----------------------------------------------------------------

    # scrapes Twitch for a page of 100 livestreams
    def scrape_livestreams(self, livestreams, previous_cursor, timelogs):

        cursor = False

        # prepare request headers
        params = {'first': 100}
        if (previous_cursor != False):
            params['after'] = previous_cursor

        # make request
        r, timelogs = self.__get('https://api.twitch.tv/helix/streams', params, self.__get_helix_headers(), timelogs, 'get_livestream')
        if (r.status_code == 200):
            results = r.json()

            # get cursor so we can continue where we left off next time
            if (('cursor' in results['pagination']) and (results['pagination']['cursor'] != '')):
                cursor = results['pagination']['cursor']

            # add livestreams data
            for item in results['data']:
                livestreams.add_from_api(item)

        self.__sleep(r.headers)
        return livestreams, cursor, timelogs



# ==============================================================================
# Class: TwitchScraper
# ==============================================================================

class TwitchScraper():

    def __init__(self):
        credentials = json.load(open('credentials.json'))
        self.twitch = TwitchAPI(credentials['twitch'])
        self.db = TwitchDB()
        self.print_mode_on = False
        self.timelog_actions = []
        return

    def set_print_mode(self, v):
        self.print_mode_on = v == True

    def __print(self, message):
        if (self.print_mode_on == True):
            print(message)


    # Procedure: Scrape Livestreams --------------------------------------------

    def procedure_scrape_livestreams(self):

        # Phase 1: check what resources the db already has ---------------------

        known_game_ids = {}
        known_tag_ids = {}


        # Phase 2: Scrape Twitch API for livestreams and related resources -----

        # 2.a) Scrape for all livestreams
        livestreams, cursor, timelogs = TwitchLivestreams(), False, TimeLogs(self.timelog_actions)
        num_old_livestreams, page_num = 0, 0
        self.__print('Scraping Livestreams...')
        while True:
            self.__print('Page: ' + str(page_num) + ' -> ' + str(num_old_livestreams) + ' livestreams seen')
            livestreams, cursor, timelogs = self.twitch.scrape_livestreams(livestreams, cursor, timelogs)

            num_livestreams = livestreams.get_num_livestreams()
            if ((cursor == False) or (num_old_livestreams == num_livestreams)):
                break
            num_old_livestreams = num_livestreams
            page_num += 1
        self.__print('Scraping Livestreams complete!\n')

        # 2.b) Scrape for all *new* games

        # 2.c) Scrape for all *new* twitch tags

         
        tags = livestreams.get_all_tag_ids()
        print(len(tags))
        return
