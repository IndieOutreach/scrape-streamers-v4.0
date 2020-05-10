# ==============================================================================
# About mixer_scraper.py
# ==============================================================================
#
# mixer_scraper.py contains classes for scraping the Mixer API
# - MixerAPI     - wrapper for accessing the MixerAPI via the requests library
# - MixerScraper - runs scraping procedures

# Imports ----------------------------------------------------------------------

import sys
import time
import json
import requests

from logs import *
from db_manager import *
from stats_objects import *

# ==============================================================================
# Data Classes
# ==============================================================================


# MixerGame --------------------------------------------------------------------

class MixerGame():

    def __init__(self, data = None, source = 'api/channels'):
        if (data == None ):
            self.valid = False
        elif (source == 'api/channels'):
            self.__load_from_api_channels_object(data)
        self.valid = True
        return

    def is_valid(self):
        return self.valid == True

    # loaded from data['type'] obj from the live channels endpoint of Mixer API
    def __load_from_api_channels_object(self, data):
        self.id             = int(data['id'])
        self.name           = data['name']
        self.parent         = data['parent'] # <- type of content this is (usually Games)
        self.cover_url      = data['coverUrl']
        self.background_url = data['backgroundUrl']
        self.description    = data['description']
        self.total_viewers  = data['viewersCurrent']

    def to_db_tuple(self):
        return (
            self.id,
            self.name,
            self.parent,
            self.description,
            self.cover_url,
            self.background_url
        )


# MixerStream ------------------------------------------------------------------

# a stream from Mixer's API. This is a stand-in for a streamer's livestream
# -> Mixer's API doesn't include unique stream IDs, so this will be a best guess
class MixerStream():

    def __init__(self, data = None, source = 'api/channels'):

        if (data == None or data['type'] == None):
            self.valid = False
            return
        elif (source == 'api/channels'):
            self.__load_from_api_channels_object(data)
        self.valid = True


    # returns true if the MixerStream is properly formatted
    def is_valid(self):
        return self.valid


    def __load_from_api_channels_object(self, data):
        self.channel_id              = int(data['id'])
        self.current_viewers         = data['viewersCurrent']
        self.game_id                 = int(data['type']['id'])
        self.game_name               = data['type']['name']
        self.total_viewers_of_game   = data['type']['viewersCurrent']
        self.total_streamers_of_game = data['type']['online']
        self.date                    = int(time.time())
        self.game                    = MixerGame(data['type'], 'api/channels')

    def get_game(self):
        if (self.is_valid() and self.game.is_valid()):
            return self.game
        return False


    def get_game_id(self):
        if (self.is_valid()):
            return self.game_id
        return -1

    def get_num_viewers(self):
        if (self.is_valid()):
            return self.current_viewers
        return -1

# MixerChannel -----------------------------------------------------------------

# an object representing a single Mixer Channel
class MixerChannel():

    def __init__(self, data, source):
        if (source == 'api/channels'):
            self.__load_from_api_channels_object(data)
            self.valid = True
        else:
            self.valid = False


    def is_valid(self):
        return self.valid


    def __load_from_api_channels_object(self, obj):
        self.id                  = int(obj['id'])                   # <- ID of the channel
        self.user_id             = int(obj['userId'])               # <- ID of the user that owns this channel
        self.token               = obj['token']
        self.audience            = obj['audience']
        self.viewers_total       = obj['viewersTotal']
        self.num_followers       = obj['numFollowers']
        self.description         = obj['description']
        self.partnered           = obj['partnered']
        self.has_videos          = obj['hasVod']
        self.vods_enabled        = obj['vodsEnabled']
        self.has_vods            = obj['hasVod']
        self.banner_url          = obj['bannerUrl']
        self.created_at          = obj['createdAt']
        self.language            = obj['languageId']
        self.featured_level      = obj['featureLevel']
        self.user_avatar_url     = obj['user']['avatarUrl']
        self.user_level          = obj['user']['level']
        self.socials             = obj['user']['social']
        self.username            = obj['user']['username']
        self.user_verified       = obj['user']['verified']
        self.user_sparks         = obj['user']['sparks']
        self.user_experience     = obj['user']['experience']
        self.current_stream_info = MixerStream(obj)
        self.date_scraped        = int(time.time())


    def get_current_game(self):
        return self.current_stream_info.get_game()

    def get_current_game_id(self):
        return self.current_stream_info.get_game_id()

    def get_num_current_viewers(self):
        return self.current_stream_info.get_num_viewers()


    def get_db_tuple(self, object_type):
        if (object_type == 'insert-channel'):
            return (
                self.id,
                self.user_id ,
                self.token,
                self.user_avatar_url,
                self.banner_url,
                self.vods_enabled,
                self.has_vods,
                self.description,
                self.language,
                self.created_at,
                self.date_scraped,
                json.dumps(self.socials),
                self.user_verified,
                self.audience
            )
        elif (object_type == 'update-channel'):
            return (
                self.token,
                self.user_avatar_url,
                self.banner_url,
                self.vods_enabled,
                self.has_vods,
                self.description,
                self.language,
                json.dumps(self.socials),
                self.user_verified,
                self.audience
            )
        elif (object_type == 'followers'):
            return (
                self.id,
                self.date_scraped,
                self.num_followers
            )
        elif (object_type == 'sparks'):
            return (
                self.id,
                self.date_scraped,
                self.user_sparks
            )
        elif (object_type == 'experience'):
            return (
                self.id,
                self.date_scraped,
                self.user_experience
            )
        elif (object_type == 'lifetime_viewers'):
            return (
                self.id,
                self.date_scraped,
                self.viewers_total
            )
        elif (object_type == 'partnered'):
            return (
                self.id,
                self.date_scraped,
                self.partnered
            )
        elif (object_type == 'livestream_snapshots'):
            return (
                self.id,
                self.get_current_game_id(),
                self.date_scraped,
                self.get_num_current_viewers()
            )


# MixerChannels ----------------------------------------------------------------

# a collection of MixerChannel objects
class MixerChannels():

    def __init__(self):
        self.channels = {}
        self.channels_with_zero_views = {}

    # creates a new MixerChannel object, given a dict from Mixer's API
    def add_from_api(self, info):
        channel = MixerChannel(info, 'api/channels')
        if (channel.is_valid()):
            if (channel.get_num_current_viewers() == 0):
                self.channels_with_zero_views[channel.id] = channel
            else:
                self.channels[channel.id] = channel

    def get(self, channel_id):
        if (channel_id in self.channels):
            return self.channels[channel_id]
        elif (channel_id in self.channels_with_zero_views):
            return self.channels_with_zero_views[channel_id]
        return False

    def get_channel_ids(self):
        ids = []
        for id in self.channels.keys():
            ids.append(id)
        for id in self.channels_with_zero_views.keys():
            ids.append(id)
        return ids

    def get_channel_ids_with_viewers(self):
        return list(self.channels.keys())

    def get_channel_ids_with_no_viewers(self):
        return list(self.channels_with_zero_views.keys())

    def get_all_games(self):
        games = {}
        for channel_id in self.get_channel_ids():
            channel = self.get(channel_id)
            game = channel.get_current_game()
            if ((game != False) and (game.id not in games)):
                games[game.id] = game
        return games



# Mixer Recording --------------------------------------------------------------

class MixerRecording():

    def __init__(self, obj, source):
        if (source == 'api/recordings'):
            self.__load_from_api_recordings_object(obj)
            self.valid = True
        else:
            self.valid = False
        return

    def is_valid(self):
        return self.valid == True

    def __load_from_api_recordings_object(self, obj):
        self.id           = int(obj['id'])
        self.name         = obj['name']
        self.game_id      = int(obj['typeId']) if (obj['typeId'] != None) else -1
        self.views        = obj['viewsTotal']
        self.duration     = obj['duration']
        self.channel_id   = int(obj['channelId'])
        self.date_created = obj['createdAt']
        self.date_scraped = int(time.time())


    # converts a recording into a tuple that can be inserted into recordings table
    def to_db_tuple(self):
        return (
            self.id,
            self.channel_id,
            self.game_id,
            self.date_scraped,
            self.date_created,
            self.views,
            self.duration
        )


# Mixer Recordings -------------------------------------------------------------

# a collection of MixerRecording objects
class MixerRecordings():

    def __init__(self):
        self.recordings = {}
        return

    def add_from_api(self, obj):
        recording = MixerRecording(obj, 'api/recordings')
        if (recording.is_valid()):
            self.recordings[recording.id] = recording

    def get_all_recording_ids(self):
        return list(self.recordings.keys())

    def get(self, recording_id):
        if (recording_id in self.recordings):
            return self.recordings[recording_id]
        return False



# ==============================================================================
# Class MixerAPI
# ==============================================================================

class MixerAPI():

    def __init__(self, credentials):
        self.client_id = credentials['client_id']
        self.rate_limit_bucket = {
            'channel-search': 20,
            'general': 1000         # <- this wasn't provided by Mixer's documentation,
        }
        self.rate_limit_times = {
            'channel-search': 5 / 20,  # 20 requests per 5 seconds -> allowed 1 every 0.25 seconds
            'general': 60 / 1000       # same as the 'Global' rate limit
        }


    # sleeps the appropriate amount to not overload the API's rate limit
    # pass in the rate-limit object given by Mixer's API request response header
    def __sleep_before_executing(self, bucket):
        if (self.rate_limit_bucket[bucket] == 0):
            time.sleep(self.rate_limit_times[bucket])

    # sleeps the appropriate amount to not overload the API's rate limit
    # uses r.headers to determine the update rate-limit left in this bucket
    def __sleep_after_executing(self, header, bucket):
        if ('X-RateLimit-Remaining' in header):
            self.rate_limit_bucket[bucket] = int(header['X-RateLimit-Remaining'])
            if (self.rate_limit_bucket[bucket] <= 1):
                time.sleep(self.rate_limit_times[bucket])


    def __get_default_headers(self):
        return {'Client-ID': self.client_id}


    # a wrapper for sending requests, wraps TimeLogs actions
    def __get(self, url, params, timelogs, request_type):
        if (timelogs != False):
            timelogs.start_action(request_type)
        r = requests.get(url, params)
        if (timelogs != False):
            timelogs.end_action(request_type)
        return r, timelogs

    # scrapes Mixer's list of live channels and returns them as a MixerChannels object
    # this endpoint can be called from different pages
    def scrape_live_channels(self, channels, page=0, timelogs=False):

        # pre-request actions
        self.__sleep_before_executing("channel-search")

        # prepare headers
        params = self.__get_default_headers()
        #params['where'] = 'viewersCurrent:gt:2'
        params['limit'] = 100
        params['order'] = 'viewersCurrent:DESC'
        params['page']  = page

        # perform request
        r, timelogs = self.__get('https://mixer.com/api/v1/channels', params, timelogs, 'get_live_channels')
        if (r.status_code == 200):
            for channel in r.json():
                channels.add_from_api(channel)

        # post-request actions
        self.__sleep_after_executing(r.headers, 'channel-search')
        return channels, page + 1, timelogs


    # scrapes a channel's recordings on Mixer
    # this endpoint can be called from different pages
    def scrape_recordings(self, channel_id, recordings, page=0, timelogs=False):

        self.__sleep_before_executing('general')

        # prepare headers
        params = self.__get_default_headers()
        params['limit'] = 100
        params['where'] = 'channelId:eq:' + str(channel_id)
        params['page']  = page

        # perform request
        r, timelogs = self.__get('https://mixer.com/api/v1/recordings', params, timelogs, 'get_recordings')
        if (r.status_code == 200):
            for row in r.json():
                recordings.add_from_api(row)

        self.__sleep_after_executing(r.headers, 'general')
        return recordings, page + 1, timelogs


    # gets a specified game
    def scrape_game(self, game_id, timelogs = False):
        self.__sleep_before_executing('general')

        # prepare headers
        game = False
        params = self.__get_default_headers()
        url = 'https://mixer.com/api/v1/types/' + str(game_id)
        r, timelogs = self.__get(url, params, timelogs, 'get_recordings')
        if (r.status_code == 200):
            game = MixerGame(r.json(), 'api/channels')

        self.__sleep_after_executing(r.headers, 'general')
        return game


# ==============================================================================
# Class: MixerScraper
# ==============================================================================


class MixerScraper():

    def __init__(self):
        credentials = json.load(open('credentials.json'))
        self.mixer = MixerAPI(credentials['mixer'])
        self.db = MixerDB()
        self.timelog_actions = ['procedure_scrape_livestreams', 'procedure_scrape_recordings']
        self.print_mode_on = False
        return

    def set_print_mode(self, v):
        self.print_mode_on = v;

    def __print(self, message):
        if (self.print_mode_on == True):
            print(message)


    # Procedure: Scrape Livestreams --------------------------------------------

    # scrapes all live channels currently on Mixer
    # Updates the following tables:
    # - channels               -> the main profile info about a streamer
    # - livestream_snapshots   -> everytime this procedure runs, it adds a new record with data about the current game/viewership of a channel
    #                             this means there will be multiple snapshots per livestream
    #                             this data will be compiled into livestreams by a different procedure
    # - followers              -> time-series data about number of followers
    # - lifetime_viewers       -> time-series data about number of viewers a streamer has had on all of Mixer
    # - sparks                 -> time-series data about the number of sparks a streamer has
    # - experience             -> time-series data about amount of experience
    # - partnered              -> time-series data about partnered status
    def procedure_scrape_livestreams(self):

        current_scrape_time = int(time.time())

        # 1) scrape all live mixer channels
        channels, page, timelogs = MixerChannels(), 0, TimeLogs(self.timelog_actions)
        old_num_channels = 0
        while(True):
            self.__print(" - page:" + str(page))
            channels, page, timelogs = self.mixer.scrape_live_channels(channels, page, timelogs)

            # if we haven't scraped any new channels this round, break from the loop
            if (old_num_channels == len(channels.get_channel_ids())):
                break
            old_num_channels = len(channels.get_channel_ids())


        # 2) connect to the database and get a list of all the channels that are already in the db
        conn = self.db.get_connection()
        existing_channel_ids = self.db.get_all_channel_ids(conn)
        existing_game_ids    = self.db.get_all_game_ids(conn)


        # 3) Insert new games
        num_new_games = 0
        live_games = channels.get_all_games()
        for game_id, game in live_games.items():
            if (game.id not in existing_game_ids):
                self.db.insert_game(conn, game)
                num_new_games += 1


        # 4) aggregate game data from all live channels and save stats about each game
        platform_stats = self.get_platform_stats_for_games(channels)
        for game_id, stats_object in platform_stats.items():
            self.db.insert_game_snapshot(conn, stats_object)

        self.__print('Games Seen: ' + str(len(platform_stats)))
        self.__print('New Games: ' + str(num_new_games))

        # 5) for each valid channel, save their info to tables
        num_inserted, num_updated = 0, 0
        for channel_id in channels.get_channel_ids_with_viewers():
            channel = channels.get(channel_id)

            # insert or update channel
            if (channel_id not in existing_channel_ids):
                self.db.insert_new_channel(conn, channel)
                num_inserted += 1
            else:
                self.db.update_channel(conn, channel)
                num_updated += 1

            # insert regular time-series data
            self.db.insert_time_series_data(conn, channel, 'followers')
            self.db.insert_time_series_data(conn, channel, 'lifetime_viewers')
            self.db.insert_time_series_data(conn, channel, 'sparks')
            self.db.insert_time_series_data(conn, channel, 'experience')

            # insert value-sensitive time-series data
            self.db.insert_time_series_data_by_value(conn, channel, 'partnered')

            # insert livestreams snapshot
            self.db.insert_livestream_snapshot(conn, channel)


        self.__print('New Channels: ' + str(num_inserted))
        self.__print('Updated Channels: ' + str(num_updated))

        conn.commit()
        conn.close()
        return


    # gets viewership statistics about games on Mixer
    def get_platform_stats_for_games(self, channels):
        stats = {}
        for channel_id in channels.get_channel_ids():
            channel = channels.get(channel_id)
            game_id = channel.get_current_game_id()
            if (game_id != -1):
                if (game_id not in stats):
                    stats[game_id] = StatsBucket(game_id)
                    {
                        'game_id': game_id,
                        'num_channels': 0,
                        'num_viewers': 0,
                        'num_zero_viewers': 0
                    }

                # add this channel to stats about game
                num_viewers = max(0, channel.get_num_current_viewers())
                stats[game_id].add(num_viewers)
        return stats



    # Procedure: Scrape Recordings ---------------------------------------------

    # gets a list of channels in the database that have recordings enabled but don't have any in the recordings table
    # This procedure is broken into 3 parts in order to minimize non-writing time spent holding the database lock
    def procedure_scrape_recordings(self):

        # Phase 1: Get info from DB about what needs to be scraped -------------

        # 1.a) get list of channels we want to grab recordings for
        #   -> reduce total sample space to a batch of 500 channels
        conn = self.db.get_connection()
        all_channel_ids = self.db.get_channel_ids_that_need_recordings(conn)
        ids_to_scrape = []
        for i in range(min(len(all_channel_ids), 100)):
            ids_to_scrape.append(all_channel_ids[i])
        self.__print('channels available: ' + str(len(all_channel_ids)))
        self.__print('channels being scraped this round: ' + str(len(ids_to_scrape)))


        # 1.b) get a lookup table of all game_ids that are already in our dataset
        #   -> we will use this so we know when to add new games found in the scraped recordings
        known_game_ids = self.db.get_all_game_ids(conn)
        conn.close()


        # Phase 2: Use API to scrape all recordings and games ------------------

        recordings_by_channels = {} # lookup table { channel_id -> MixerRecordings() }
        new_games = {}              # lookup table { game_id -> MixerGame() }

        for channel_id in ids_to_scrape:

            # Grab all the recordings for this channel
            recordings = self.get_all_recordings_for_channel(channel_id)
            recordings_by_channels[channel_id] = recordings

            # add any new games that are in these recordings
            for recording_id in recordings.get_all_recording_ids():
                recording = recordings.get(recording_id)
                if ((recording.game_id not in known_game_ids) and (recording.game_id != -1)):
                    game = self.mixer.scrape_game(recording.game_id)
                    if (game != False):
                        new_games[game.id]      = game
                        known_game_ids[game.id] = True



        # Phase 3: Write recordings and games to the database ------------------

        stats = {'num_channels_with_recordings': 0, 'num_channels_no_recordings': 0, 'num_recordings': 0, 'num_games_added': 0}

        conn = self.db.get_connection()

        # save games
        for game_id, game in new_games.items():
            stats['num_games_added'] += 1
            self.db.insert_game(conn, game)

        # save recordings
        for channel_id, recordings in recordings_by_channels.items():
            recording_ids = recordings.get_all_recording_ids()
            if (len(recording_ids) > 0):
                stats['num_channels_with_recordings'] += 1
                for id in recording_ids:
                    stats['num_recordings'] += 1
                    self.db.insert_recording_for_channel(conn, recordings.get(id))
            else:
                self.db.insert_channel_with_no_recordings(conn, channel_id)
                stats['num_channels_no_recordings'] += 1

        conn.commit()
        conn.close()

        # print stats
        for key, value in stats.items():
            self.__print(key + ": " + str(value))
        return


    # calls the MixerAPI to get a MixerRecordings object containing all the recordings for a given channel
    def get_all_recordings_for_channel(self, channel_id):

        recordings, page, timelogs = MixerRecordings(), 0, TimeLogs(self.timelog_actions)
        old_num_recordings = 0

        while(True):
            recordings, page, timelogs = self.mixer.scrape_recordings(channel_id, recordings, page, timelogs)

            # if we haven't scraped any new recordings this round, break from the loop
            if (old_num_recordings == len(recordings.get_all_recording_ids())):
                break
            old_num_recordings = len(recordings.get_all_recording_ids())

        return recordings
