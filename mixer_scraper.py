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
import requests



# ==============================================================================
# Data Classes
# ==============================================================================

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
        self.channel_id = data['id']
        self.current_viewers = data['viewersCurrent']
        self.game_id = data['type']['id']
        self.game_name = data['type']['name']
        self.total_viewers_of_game = data['type']['viewersCurrent']
        self.total_streamers_of_game = data['type']['online']
        self.date = int(time.time())

    def get_game_id(self):
        if (self.is_valid()):
            return self.game_id
        return False


# MixerChannel -----------------------------------------------------------------

# an object representing a single Mixer Channel
class MixerChannel():

    def __init__(self, data, source):
        if (source == 'api/channels'):
            self.__load_from_api_channels_object(data)
        else:
            self.valid = False
        self.valid = True


    def is_valid(self):
        return self.valid


    def __load_from_api_channels_object(self, obj):
        self.id                  = obj['id']                   # <- ID of the channel
        self.user_id             = obj['userId']               # <- ID of the user that owns this channel
        self.token               = obj['token']
        self.audience            = obj['audience']
        self.viewers_total       = obj['viewersTotal']
        self.num_followers       = obj['numFollowers']
        self.description         = obj['description']
        self.partnered           = obj['partnered']
        self.has_videos          = obj['hasVod']
        self.vods_enabled        = obj['vodsEnabled']
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



    def get_current_game_id(self):
        return self.current_stream_info.get_game_id()

    def get_num_current_viewers(self):
        if (self.current_stream_info.is_valid()):
            return self.current_stream_info.current_viewers
        return False


    # dumps info about this channel into format for streamers_n.db.channel object
    def to_db_object(self):
        obj = {}
        obj['channel_id']      = self.id
        obj['user_id']         = self.user_id
        obj['token']           = self.token
        obj['user_avatar_url'] = self.user_avatar_url
        obj['banner_url']      = self.banner_url
        obj['vods_enabled']    = self.vods_enabled
        obj['description']     = self.description
        obj['language']        = self.language
        obj['date_joined']     = self.created_at
        obj['social']          = self.socials
        obj['verified']        = self.user_verified
        obj['audience']        = self.audience
        return obj

# MixerChannels ----------------------------------------------------------------

# a collection of MixerChannel objects
class MixerChannels():

    def __init__(self):
        self.channels = {}

    # creates a new MixerChannel object, given a dict from Mixer's API
    def add_from_api(self, info):
        channel = MixerChannel(info, 'api/channels')
        if (channel.is_valid()):
            self.channels[channel.id] = channel

    def get(self, channel_id):
        if (channel_id in self.channels):
            return self.channels[channel_id]
        return False

    def get_channel_ids(self):
        return self.channels.keys()

    # returns channel IDs as grouped by scraper_id
    def get_ids_in_batches(self, db_manager, id_manager):
        batches = []

        # initialize batch arrays
        for i in range(db_manager.get_batch_from_scraper_id(id_manager.largest_scraper_id)):
            batches.append([])

        # add IDs to batches
        for channel_id, channel_object in self.channels.items():
            scraper_id = id_manager.get_scraper_id(channel_id)
            batch_id = db_manager.get_batch_from_scraper_id(scraper_id)
            batches[batch_id - 1].append(channel_id)

        return batches





# ==============================================================================
# Class MixerAPI
# ==============================================================================

class MixerAPI():

    def __init__(self, credentials):
        self.client_id = credentials['client_id']
        self.rate_limit_bucket = {
            'channel-search': 20
        }
        self.rate_limit_times = {
            'channel-search': 5 / 20 # 20 requests per 5 seconds -> allowed 1 every 0.25 seconds
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
        params['where'] = 'viewersCurrent:gt:2'
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


# ==============================================================================
# Class: MixerScraper
# ==============================================================================


class MixerScraper():

    def __init__(self):
        return
