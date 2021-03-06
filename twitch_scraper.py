# ==============================================================================
# About: twitch_scraper.py
# ==============================================================================
#
# twitch_scraper.py contains all of the classes involved with scraping the Twitch API
# - TwitchAPI       - a wrapper for the Twitch API
# - TwitchScraper   - implements the scraping procedures using TwitchAPI
# - Twitch<Object>s - various objects from Twitch's API that are held in memory and then dumped to the db
#
# Scraping Procedures in TwitchScraper
# - Livestreams
# - Recordings
# - Followers
# - Inactive
#

# Imports ----------------------------------------------------------------------

import sys
import json
import time
import requests

from logs import *
from db_manager import *
from stats_objects import *

# ==============================================================================
# Classes: Twitch<Objects>
# ==============================================================================

# TwitchLivestreamSnapshot -----------------------------------------------------
# -> This represents a single snapshot of a livestream taken by the API
# -> It will later be used and aggregated into a TwitchLivestream object

class TwitchLivestreamSnapshot():

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
        self.id           = int(obj['id'])
        self.user_id      = int(obj['user_id'])
        self.user_name    = obj['user_name']
        self.game_id      = int(obj['game_id']) if (obj['game_id'] != '') else -1
        self.viewer_count = int(obj['viewer_count'])
        self.language     = obj['language']
        self.started_at   = obj['started_at']
        self.tag_ids      = obj['tag_ids']
        self.date_scraped = int(time.time())


    # returns a list of tag ids and an empty list if there are none
    def get_tag_ids(self):
        if (isinstance(self.tag_ids, list)):
            return self.tag_ids
        return []

    def to_db_tuple(self):
        return (
            self.id,
            self.user_id,
            self.game_id,
            self.viewer_count,
            self.started_at,
            self.date_scraped,
            json.dumps(self.tag_ids),
            self.language
        )


# TwitchLivestreamSnapshots ----------------------------------------------------
# -> This is a collection of TwitchLivestreamSnapshot objects


class TwitchLivestreamSnapshots():

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

    def get_all_livestream_ids(self):
        ids = []
        for id in self.livestreams:
            ids.append(id)
        for id in self.livestreams_no_viewers:
            ids.append(id)
        return ids

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

    def get_livestream_ids_with_no_viewers(self):
        return list(self.livestreams_no_viewers.keys())

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
        livestream = TwitchLivestreamSnapshot(obj, 'api/livestreams')
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

    def to_db_tuple(self):
        return (
            self.id,
            self.name,
            self.box_art_url
        )

# TwitchGames ------------------------------------------------------------------

class TwitchGames():

    def __init__(self):
        self.games = {}
        return

    def get(self, game_id):
        if (game_id in self.games):
            return self.games[game_id]
        return False

    def add_from_api(self, obj):
        game = TwitchGame(obj, 'api/games')
        if (game.is_valid()):
            self.games[game.id] = game

    def get_game_ids(self):
        return list(self.games.keys())


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
        self.english_name              = "" if ('en-us' not in obj['localization_names']) else obj['localization_names']['en-us']
        self.english_description       = "" if ('en-us' not in obj['localization_descriptions']) else obj['localization_descriptions']['en-us']
        return

    def to_db_tuple(self):
        return (
            self.id,
            self.is_auto,
            self.english_name,
            json.dumps(self.localization_names),
            self.english_description,
            json.dumps(self.localization_descriptions)
        )


# TwitchTags -------------------------------------------------------------------

class TwitchTags():

    def __init__(self):
        self.tags = {}
        return

    def add_from_api(self, obj):
        tag = TwitchTag(obj, 'api/tags')
        if (tag.is_valid()):
            self.tags[tag.id] = tag

    def get_tag_ids(self):
        return list(self.tags.keys())

    def get(self, tag_id):
        if (tag_id in self.tags):
            return self.tags[tag_id]
        return False

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
        self.date_scraped      = int(time.time())
        return



    def to_db_tuple(self, object_type):
        if (object_type == 'insert'):
            return (
                self.id,
                self.login,
                self.display_name,
                self.description,
                self.profile_image_url,
                self.offline_image_url,
                self.date_scraped,
                self.date_scraped
            )
        elif (object_type == 'update'):
            return (
                self.login,
                self.display_name,
                self.description,
                self.profile_image_url,
                self.offline_image_url,
                self.date_scraped
            )
        elif (object_type == 'total_views'):
            return (
                self.id,
                self.date_scraped,
                self.view_count
            )
        elif (object_type == 'broadcaster_type'):
            return (
                self.id,
                self.date_scraped,
                self.broadcaster_type
            )

# TwitchStreamers --------------------------------------------------------------

class TwitchStreamers():

    def __init__(self):
        self.streamers = {}
        return

    def add_from_api(self, obj):
        streamer = TwitchStreamer(obj, 'api/users')
        if (streamer.is_valid()):
            self.streamers[streamer.id] = streamer

    def get_streamer_ids(self):
        return list(self.streamers.keys())

    def get(self, streamer_id):
        if (streamer_id in self.streamers):
            return self.streamers[streamer_id]
        return False

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

    # for a given streamer, get the number of users following them
    def scrape_num_followers(self, streamer_id, timelogs):
        num_followers = -1
        params = {'to_id': streamer_id}
        r, timelogs = self.__get('https://api.twitch.tv/helix/users/follows', params, self.__get_helix_headers(), timelogs, 'get_followers')
        if (r.status_code == 200):
            results = r.json()
            num_followers = results['total']
        return num_followers, timelogs


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

    def procedure_scrape_livestream_snapshots(self):

        time_started = int(time.time())
        stats = {
            'num_livestreams':             0,
            'num_livestreams_inserted':    0,
            'num_livestreams_no_viewers':  0,
            'num_streamers_inserted':      0,
            'num_streamers_updated':       0,
            'num_game_snapshots_inserted': 0,
            'num_games_inserted':          0,
            'num_tags_inserted':           0
        }

        # Phase 1: check what resources the db already has ---------------------

        conn = self.db.get_connection()
        known_game_ids     = self.db.get_all_game_ids(conn)
        known_tag_ids      = self.db.get_all_tag_ids(conn)
        known_streamer_ids = self.db.get_all_streamer_ids(conn)
        conn.close()


        # Phase 2: Scrape Twitch API for livestreams and related resources -----

        self.__print('\nScraping Data ----------------------------------------')

        # 2.a) Scrape for all livestreams
        livestreams, cursor, timelogs = TwitchLivestreamSnapshots(), False, TimeLogs(self.timelog_actions)
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
        new_game_ids = []
        for game_id in livestreams.get_all_game_ids():
            if (game_id not in known_game_ids):
                new_game_ids.append(game_id)

        self.__print('Scraping ' + str(len(new_game_ids)) + ' new games...')
        new_games = TwitchGames()
        for batch_of_ids in self.__break_list_into_batches(new_game_ids, 100):
            new_games, timelogs = self.twitch.scrape_games(batch_of_ids, new_games, timelogs)
        self.__print('Scraping games complete!\n')

        # get stats about all games
        game_platform_stats = self.get_platform_stats_for_games(livestreams)

        # 2.c) Scrape for all *new* twitch tags
        new_tag_ids = []
        for tag_id in livestreams.get_all_tag_ids():
            if (tag_id not in known_tag_ids):
                new_tag_ids.append(tag_id)

        self.__print('Scraping ' + str(len(new_tag_ids)) + ' new tags...')
        new_tags = TwitchTags()
        for batch_of_ids in self.__break_list_into_batches(new_tag_ids, 100):
            new_tags, timelogs = self.twitch.scrape_tags(batch_of_ids, new_tags, timelogs)
        self.__print('Scraping tags complete\n')

        # 2.d) Scrape all user profiles for streamers that have enough viewers
        streamers = TwitchStreamers()
        streamer_ids_to_scrape  = livestreams.get_streamer_ids_with_more_than_n_views(3)
        streamer_ids_in_batches = self.__break_list_into_batches(streamer_ids_to_scrape, 100)
        self.__print('Scraping ' + str(len(streamer_ids_to_scrape)) + ' streamer profiles in ' + str(len(streamer_ids_in_batches)) + ' batches...')
        for i, batch_of_ids in enumerate(streamer_ids_in_batches):
            self.__print('batch: ' + str(i))
            streamers, timelogs = self.twitch.scrape_users(batch_of_ids, streamers, timelogs)
        self.__print('Scraping streamer profiles complete')


        # Phase 3: Commit everything to the database ---------------------------

        self.__print('\nSaving Data ------------------------------------------')
        conn = self.db.get_connection()

        # save streamer profiles
        self.__print('Inserting streamers into db...')
        for streamer_id in streamers.get_streamer_ids():
            streamer = streamers.get(streamer_id)
            if (streamer_id not in known_streamer_ids):
                self.db.insert_new_streamer(conn, streamer)
                stats['num_streamers_inserted'] += 1
            else:
                self.db.update_streamer(conn, streamer)
                stats['num_streamers_updated'] += 1

            # add time-series data for streamers
            self.db.insert_total_views_for_streamer(conn, streamer)
            self.db.insert_broadcaster_type_for_streamer(conn, streamer)

        # save games
        self.__print('Inserting games into db...')
        for game_id in new_games.get_game_ids():
            game = new_games.get(game_id)
            self.db.insert_game(conn, game)
            stats['num_games_inserted'] += 1


        # save platform stats
        self.__print('Inserting game snapshots into db...')
        for game_id, game in game_platform_stats.items():
            self.db.insert_game_snapshot(conn, game)
            stats['num_game_snapshots_inserted'] += 1

        # save twitch tags
        self.__print('Inserting twitch tags into db...')
        for tag_id in new_tags.get_tag_ids():
            tag = new_tags.get(tag_id)
            self.db.insert_tag(conn, tag)
            stats['num_tags_inserted'] += 1


        # save livestreams
        self.__print('Inserting livestreams into db...')
        for livestream_id in livestreams.get_livestream_ids_with_more_than_n_views(3):
            livestream = livestreams.get(livestream_id)
            self.db.insert_livestream_snapshot(conn, livestream)
            stats['num_livestreams_inserted'] += 1


        # Phase 4: Save logs to the database -----------------------------------

        self.__print('\nSaving Logs ------------------------------------------')
        stats['num_livestreams']            = livestreams.get_num_livestreams()
        stats['num_livestreams_no_viewers'] = len(livestreams.get_livestream_ids_with_no_viewers())

        self.__print('Inserting scraping logs into db...')
        timelog_str = json.dumps(timelogs.get_stats_from_logs())
        stats_str   = json.dumps(stats)
        self.db.insert_logs(conn, 'scrape-livestreams', time_started, timelog_str, stats_str)

        conn.commit()
        conn.close()

        self.__print('\nStats:')
        for k, v in stats.items():
            self.__print(k + ': ' + str(v))
        self.__print('\nScrape Livestreams Procedure completed!\n')
        return


    # get viewership statistics about games on Twitch
    # creates a lookup {game_id -> StatsBucket }
    def get_platform_stats_for_games(self, livestreams):
        stats = {}
        for livestream_id in livestreams.get_all_livestream_ids():
            livestream = livestreams.get(livestream_id)
            game_id = livestream.game_id
            if (game_id != -1):
                if (game_id not in stats):
                    stats[game_id] = StatsBucket(game_id)
                num_viewers = max(0, livestream.viewer_count)
                stats[game_id].add(num_viewers)
        return stats

    # takes in a list of datapoints and breaks it into a list of lists, each size <= batch_size
    def __break_list_into_batches(self, list_of_data, batch_size):
        batches = []
        for i, v in enumerate(list_of_data):
            batch_index = int(i / batch_size)
            if (batch_index >= len(batches)):
                batches.append([])
            batches[batch_index].append(v)
        return batches


    # Procedure: Scrape Inactive -----------------------------------------------

    def procedure_scrape_inactive(self):

        self.__print('Starting Scrape Inactive procedure!')
        time_started = int(time.time())
        stats = {'num_streamers_updated': 0}
        timelogs = TimeLogs(self.timelog_actions)

        # Phase 1: Get a list of streamers that are "inactive" -----------------

        conn = self.db.get_connection()
        streamer_ids = self.db.get_inactive_streamer_ids(conn)
        conn.close()

        # Phase 2: Scrape info for each streamer in our list -------------------

        streamers = TwitchStreamers()
        self.__print('Scraping ' + str(len(streamer_ids)) + ' streamer profiles in batches of size <= 100')
        for i, batch_of_ids in enumerate(self.__break_list_into_batches(streamer_ids, 100)):
            self.__print('batch: ' + str(i))
            streamers, timelogs = self.twitch.scrape_users(batch_of_ids, streamers, timelogs)
        self.__print('Finished scraping streamer profiles')


        # Phase 3: Save streamer info to the database --------------------------

        conn = self.db.get_connection()
        # save streamer profiles
        self.__print('Inserting streamers into db...')
        for streamer_id in streamers.get_streamer_ids():
            streamer = streamers.get(streamer_id)
            self.db.update_streamer(conn, streamer)
            stats['num_streamers_updated'] += 1

            # add time-series data for streamers
            self.db.insert_total_views_for_streamer(conn, streamer)
            self.db.insert_broadcaster_type_for_streamer(conn, streamer)


        # Phase 4: Log this scraping procedure to database ---------------------

        self.__print('Inserting scraping logs into db...')
        timelog_str = json.dumps(timelogs.get_stats_from_logs())
        stats_str   = json.dumps(stats)
        self.db.insert_logs(conn, 'scrape-inactive', time_started, timelog_str, stats_str)

        conn.commit()
        conn.close()
        self.__print('Scrape Inactive procedure finished!')
        return

    # Procedure: Scrape Followers ----------------------------------------------


    def procedure_scrape_followers(self):

        self.__print('Starting Scrape Followers procedure!')
        time_started = int(time.time())
        stats = {'num_streamers_inserted': 0}
        timelogs = TimeLogs(self.timelog_actions)

        # Phase 1: Get a list of streamers that need follower counts -----------

        conn = self.db.get_connection()
        streamer_ids = self.db.get_streamer_ids_that_need_follower_data(conn, 750)
        conn.close()

        # Phase 2: Scrape followers from API -----------------------------------

        self.__print('Scraping follower counts for ' + str(len(streamer_ids)) + ' streamers...')
        followers_lookup = {} # <- {streamer_id -> num_followers}
        for i, streamer_id in enumerate(streamer_ids):
            num_followers, timelogs = self.twitch.scrape_num_followers(streamer_id, timelogs)
            followers_lookup[streamer_id] = num_followers
            if (i % 25 == 0):
                self.__print('scraped ' + str(i) + ' out of ' + str(len(streamer_ids)))

        # Phase 3: Commit follower counts to the database ----------------------

        self.__print('Commiting follower counts to database...')
        conn = self.db.get_connection()
        for streamer_id, num_followers in followers_lookup.items():
            self.db.insert_followers_count(conn, streamer_id, num_followers)
            stats['num_streamers_inserted'] += 1

        # Phase 4: Save logs to the database -----------------------------------

        self.__print('Inserting scraping logs into db...')
        timelog_str = json.dumps(timelogs.get_stats_from_logs())
        stats_str   = json.dumps(stats)
        self.db.insert_logs(conn, 'scrape-followers', time_started, timelog_str, stats_str)

        conn.commit()
        conn.close()

        self.__print('Scrape Followers Procedure complete!')
        return


    # Procedure: Compress Livestreams ------------------------------------------

    def procedure_compress_livestreams(self):

        self.__print('Starting Compress Livestreams procedure!')
        time_started = int(time.time())
        stats = {'num_snapshots': 0, 'num_livestream_ids': 0, 'num_livestream_objs': 0}
        timelogs = TimeLogs(self.timelog_actions)


        # Phase 1: Get list of livestream_snapshots to be processed ------------

        conn = self.db.get_connection()
        livestream_snapshots = {}
        for livestream_id in self.db.get_livestream_snapshot_ids_to_compress(conn, 5000):
            snapshots = self.db.get_all_livestream_snapshots_with_id(conn, livestream_id)
            livestream_snapshots[livestream_id] = snapshots
            stats['num_snapshots'] += len(snapshots)
        conn.close()


        # Phase 2: Compress snapshots ------------------------------------------

        compressed_livestreams = []
        livestream_ids         = []
        for id, snapshots in livestream_snapshots.items():
            for compressed_obj in self.__compress_snapshots(snapshots):
                db_obj = self.__compressed_livestream_to_db_tuple(compressed_obj)
                compressed_livestreams.append(db_obj)
            livestream_ids.append(id)

        stats['num_livestream_ids']  = len(livestream_ids)
        stats['num_livestream_objs'] = len(compressed_livestreams)

        # Phase 3: Modify database (Delete/Insert) -----------------------------

        conn = self.db.get_connection()
        for db_tuple in compressed_livestreams:
            self.db.insert_livestream(conn, db_tuple)
        for livestream_id in livestream_ids:
            self.db.delete_livestream_snapshots(conn, livestream_id)

        # Phase 4: Save Logs to Database ---------------------------------------

        self.__print('Inserting scraping logs into db...')
        timelog_str = json.dumps(timelogs.get_stats_from_logs())
        stats_str   = json.dumps(stats)
        self.db.insert_logs(conn, 'compress-livestreams', time_started, timelog_str, stats_str)

        conn.commit()
        conn.close()
        return


    # given a list of snapshots from db.get_all_livestream_snapshots_with_id(),
    # compresses snapshots into individual livestream objects based on (livestream_id, game_id, date_started)
    # -> this means that if a streamer played games [A, B, A]
    def __compress_snapshots(self, snapshots):

        # 1) sort snapshots by date_scraped value
        sorted_snapshots = sorted(snapshots, key=lambda k: k['date_scraped'])

        # 2) Break snapshots list into sublists by game_id
        sublists = []
        current_game_id = None
        for snapshot in sorted_snapshots:
            if (current_game_id is None or snapshot['game_id'] != current_game_id):
                current_game_id = snapshot['game_id']
                sublists.append([])
            sublists[-1].append(snapshot)

        # 3) Compress each sublist
        compressed_livestreams = []
        for sublist in sublists:
            id           = sublist[0]['livestream_id']
            date_started = sublist[0]['date_scraped']
            date_ended   = sublist[-1]['date_scraped']
            min_views    = None
            max_views    = None
            views        = []
            for snapshot in sublist:
                views.append(snapshot['viewers'])
                if (max_views is None or snapshot['viewers'] > max_views):
                    max_views = snapshot['viewers']
                if (min_views is None or snapshot['viewers'] < min_views):
                    min_views = snapshot['viewers']

            compressed_livestreams.append({
                'livestream_id': sublist[0]['livestream_id'],
                'streamer_id'  : sublist[0]['streamer_id'],
                'game_id'      : sublist[0]['game_id'],
                'date_started' : date_started,
                'date_ended'   : date_ended,
                'tag_ids'      : sublist[0]['tag_ids'],
                'language'     : sublist[0]['language'],
                'max_viewers'  : max_views,
                'min_viewers'  : min_views,
                'viewer_counts': views
            })
        return compressed_livestreams

    # takes a dict representing a compressed livestream (from .__compress_snapshots())
    # converts it into a tuple for inserting into the 'livestreams' table
    def __compressed_livestream_to_db_tuple(self, c):
        return (
            c['livestream_id'],
            c['streamer_id'],
            c['game_id'],
            c['date_started'],
            c['date_ended'],
            json.dumps(c['tag_ids']),
            c['language'],
            c['max_viewers'],
            c['min_viewers'],
            json.dumps(c['viewer_counts'])
        )
