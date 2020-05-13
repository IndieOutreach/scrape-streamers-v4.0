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


    # Get ----------------------------------------------------------------------

    def get(self, id):
        if (id in self.livestreams):
            return self.livestreams[id]
        elif (id in self.livestreams_no_viewers):
            return self.livestreams_no_viewers[id]
        return False

    def get_num_livestreams(self):
        return len(self.livestreams) + len(self.livestreams_no_viewers)

    def get_livestream_ids_with_more_than_n_views(self, n):
        ids = []
        for id, livestream in self.livestreams.items():
            if (livestream.viewer_count > n):
                ids.append(id)
        return ids

    def get_streamer_ids_with_more_than_n_views(self, n):
        ids = []
        for id, livestream in self.livestreams.items():
            if (livestream.viewer_count > n):
                ids.append(livestream.user_id)
        return ids

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

    # returns all game_ids in livestreams as a list
    def get_all_game_ids(self):
        ids = {}
        def add_games_from_livestreams(lookup, livestreams):
            for livestream_id, livestream in livestreams.items():
                game_id = livestream.game_id
                if ((game_id != -1) and (game_id not in lookup)):
                    lookup[game_id] = True
            return lookup
        ids = add_games_from_livestreams(ids, self.livestreams)
        ids = add_games_from_livestreams(ids, self.livestreams_no_viewers)
        return list(ids.keys())

    # Insert -------------------------------------------------------------------

    def add_from_api(self, obj):
        livestream = TwitchLivestream(obj, 'api/livestreams')
        if (livestream.is_valid()):
            if (livestream.viewer_count > 0):
                self.livestreams[livestream.id] = livestream
            else:
                self.livestreams_no_viewers[livestream.id] = livestream
        return


# Twitch Game ------------------------------------------------------------------

class TwitchGame():

    def __init__(self, data, source):
        if (source == 'api/games'):
            self.__load_from_api_games_object(data)
            self.valid = True
        else:
            self.valid = False
        return

    def is_valid(self):
        return self.valid == True

    def __load_from_api_games_object(self, data):
        self.id          = data['id']
        self.name        = data['name']
        self.box_art_url = data['box_art_url']
        return

# TwitchGames ------------------------------------------------------------------

class TwitchGames():

    def __init__(self):
        self.games = {}
        return

    def add_from_api(self, obj):
        game = TwitchGame(obj, 'api/games')
        if (game.is_valid()):
            self.games[game.id] = game


# TwitchTag --------------------------------------------------------------------

class TwitchTag():

    def __init__(self, data, source):
        if (source == 'api/tags'):
            self.__load_from_api_tags_object(data)
            self.valid = True
        else:
            self.valid = False
        return

    def is_valid(self):
        return self.valid

    def __load_from_api_tags_object(self, obj):
        self.id                        = obj['tag_id']
        self.is_auto                   = obj['is_auto']
        self.localization_names        = obj['localization_names']
        self.localization_descriptions = obj['localization_descriptions']
        return


# TwitchTags -------------------------------------------------------------------

class TwitchTags():

    def __init__(self):
        self.tags = {}
        return

    def add_from_api(self, obj):
        tag = TwitchTag(obj, 'api/tags')
        if (tag.is_valid()):
            self.tags[tag.id] = tag


# TwitchStreamer ---------------------------------------------------------------

class TwitchStreamer():

    def __init__(self, data, source):
        if (source == 'api/users'):
            self.__load_from_api_users_object(data)
            self.valid = True
        else:
            self.valid = False
        return

    def is_valid(self):
        return self.valid == True

    def __load_from_api_users_object(self, obj):
        self.id                = int(obj['id'])
        self.login             = obj['login']
        self.display_name      = obj['display_name']
        self.admin_type        = obj['type']             # <- staff, admin, global_mod, or ""
        self.broadcaster_type  = obj['broadcaster_type'] # <- partner, affiliate, or ""
        self.description       = obj['description']
        self.view_count        = int(obj['view_count'])
        self.profile_image_url = obj['profile_image_url']
        self.offline_image_url = obj['offline_image_url']
        return

# TwitchStreamers --------------------------------------------------------------

class TwitchStreamers():

    def __init__(self):
        self.streamers = {}
        return

    def add_from_api(self, obj):
        streamer = TwitchStreamer(obj, 'api/users')
        if (streamer.is_valid()):
            self.streamers[streamer.id] = streamer

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


    # takes in a list of items and converts them into a list of tuples
    # [v1, v2, ... ] -> [(key, v1), (key, v2), ... ]
    # this is useful for passing in batches of info through headers
    def __format_tuple_params(self, items, key):
        params = []
        for v in items:
            params.append((key, v))
        return params

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

    # given an array of game_ids, return a TwitchGames object with games
    def scrape_games(self, game_ids, games, timelogs):
        params = self.__format_tuple_params(game_ids, 'id')
        r, timelogs = self.__get('https://api.twitch.tv/helix/games', params, self.__get_helix_headers(), timelogs, 'get_games')
        if (r.status_code == 200):
            results = r.json()
            for row in results['data']:
                games.add_from_api(row)
        self.__sleep(r.headers)
        return games, timelogs

    # given an array of tag_ids, return a TwitchTags object with tags
    def scrape_tags(self, tag_ids, tags, timelogs):
        params = self.__format_tuple_params(tag_ids, 'tag_id')
        r, timelogs = self.__get('https://api.twitch.tv/helix/tags/streams', params, self.__get_helix_headers(), timelogs, 'get_tags')
        if (r.status_code == 200):
            results = r.json()
            for row in results['data']:
                tags.add_from_api(row)
        self.__sleep(r.headers)
        return tags, timelogs


    # given an array of user_ids, return a TwitchStreamers object with streamer profiles
    def scrape_users(self, user_ids, users, timelogs):
        params = self.__format_tuple_params(user_ids, 'id')
        r, timelogs = self.__get('https://api.twitch.tv/helix/users', params, self.__get_helix_headers(), timelogs, 'get_users')
        if (r.status_code == 200):
            results = r.json()
            for row in results['data']:
                users.add_from_api(row)
        self.__sleep(r.headers)
        return users, timelogs

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
            break
        self.__print('Scraping Livestreams complete!\n')


        # 2.b) Scrape for all *new* games
        new_game_ids = []
        for game_id in livestreams.get_all_game_ids():
            if (game_id not in known_game_ids):
                new_game_ids.append(game_id)

        new_games = TwitchGames()
        for batch_of_ids in self.__break_list_into_batches(new_game_ids, 100):
            new_games, timelogs = self.twitch.scrape_games(batch_of_ids, new_games, timelogs)

        # 2.c) Scrape for all *new* twitch tags
        new_tag_ids = []
        for tag_id in livestreams.get_all_tag_ids():
            if (tag_id not in known_tag_ids):
                new_tag_ids.append(tag_id)

        new_tags = TwitchTags()
        for batch_of_ids in self.__break_list_into_batches(new_tag_ids, 100):
            new_tags, timelogs = self.twitch.scrape_tags(batch_of_ids, new_tags, timelogs)


        # 2.d) Scrape all user profiles for streamers that have enough viewers
        streamers = TwitchStreamers()
        for batch_of_ids in self.__break_list_into_batches(livestreams.get_streamer_ids_with_more_than_n_views(3), 100):
            streamers, timelogs = self.twitch.scrape_users(batch_of_ids, streamers, timelogs)

        # Phase 3: Calculate Stats about Games on Twitch -----------------------

        # for each game,
        # - num_channels, num_zero, total_viewers, min_viewers, max_viewers, median_viewers, mean_viewers, std_dev_viewers


        # Phase 4: Commit everything to the database ---------------------------

        # Phase 5: Save logs to the database -----------------------------------

        return



    # takes in a list of datapoints and breaks it into a list of lists, each size <= batch_size
    def __break_list_into_batches(self, list_of_data, batch_size):
        batches = []
        for i, v in enumerate(list_of_data):
            batch_index = int(i / batch_size)
            if (batch_index >= len(batches)):
                batches.append([])
            batches[batch_index].append(v)
        return batches
