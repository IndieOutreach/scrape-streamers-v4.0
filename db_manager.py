# ==============================================================================
# About: db_manager.py
# ==============================================================================
#
# db_manager.py contains the SQLiteManager classes, which is responsible for all interactions with the SQLite databases
# - MixerDB  - handles all sql interactions with mixer.db
# - TwitchDB - handles all sql interactions with twitch.db
#

# Imports ----------------------------------------------------------------------

import sys
import json
import time
import sqlite3


# ==============================================================================
# Class: MixerDBManager
# ==============================================================================

class MixerDB():
    def __init__(self):
        self.filepath = './data/mixer.db' # <- the filepath to the db file
        self.commands = self.load_commands()
        return

    def load_commands(self):

        def __load_from_file(commands, filepath):
            f = json.load(open(filepath))
            for command_name, command_list in f.items():
                if (len(command_list) > 1):
                    commands[command_name] = command_list
                else:
                    commands[command_name] = command_list[0]
            return commands

        commands = __load_from_file({}, './sql/mixer_create.json')
        commands = __load_from_file(commands, './sql/mixer_insert.json')
        commands = __load_from_file(commands, './sql/mixer_select.json')
        return commands



    # Connect ------------------------------------------------------------------

    def get_connection(self):
        return sqlite3.connect(self.filepath, timeout = 1 * 60 * 15) # <- 15 minutes

    # Create -------------------------------------------------------------------

    def create_tables(self):
        conn = sqlite3.connect(self.filepath)
        for command in self.commands['create-tables-mixer']:
            conn.execute(command)
        conn.commit()
        conn.close()


    # Insert -------------------------------------------------------------------

    # inserts a channel into the channels table
    def insert_new_channel(self, conn, channel):
        conn.execute(self.commands['insert-new-channel-mixer'], channel.get_db_tuple('insert-channel'))
        return


    # updates an existing channel entry in the data
    def update_channel(self, conn, channel):
        command = self.commands['update-channel-mixer'].replace('{channel_id}', str(channel.id))
        conn.execute(command, channel.get_db_tuple('update-channel'))
        return


    # adds data for a channel into: followers, lifetime_viewers, sparks, and experience tables
    def insert_time_series_data(self, conn, channel, data_type):
        insert_command = self.commands['insert-time-series-mixer'].replace('{table_name}', data_type)
        conn.execute(insert_command, channel.get_db_tuple(data_type))
        return


    # adds data for a channel into data_type iff the value has changed
    # -> typically used for partnered table
    def insert_time_series_data_by_value(self, conn, channel, table_name):

        if (table_name not in ['partnered']):
            return

        tuple_to_insert = channel.get_db_tuple(table_name)
        new_value = tuple_to_insert[2]

        # create sql statements
        insert_command = self.commands['insert-time-series-mixer'].replace('{table_name}', table_name)
        select_command = self.commands['get-most-recent-entry-for-channel-mixer']
        select_command = select_command.replace('{table_name}', table_name)
        select_command = select_command.replace('{date_column}', 'date_scraped')
        select_command = select_command.replace('{channel_id}', str(channel.id))

        # only insert this value if the value has changed
        c = conn.execute(select_command)
        row = c.fetchone()
        if (row is None):
            conn.execute(insert_command, tuple_to_insert)
        else:
            if (row[2] != new_value):
                conn.execute(insert_command, tuple_to_insert)


    def insert_livestream_snapshot(self, conn, channel):
        insert_command = self.commands['insert-livestream-snapshot-mixer']
        conn.execute(insert_command, channel.get_db_tuple('livestream_snapshots'))
        return

    # assumes game_stats is a StatsBucket object
    def insert_game_snapshot(self, conn, game_stats):
        insert_command = self.commands['insert-game-snapshot-mixer']
        conn.execute(insert_command, game_stats.to_db_tuple())
        return

    # assumes game is a MixerGame object
    def insert_game(self, conn, game):
        insert_command = self.commands['insert-game-mixer']
        conn.execute(insert_command, game.to_db_tuple())
        return

    # inserts a channel into no_recordings table
    def insert_channel_with_no_recordings(self, conn, channel_id):
        tuple_to_insert = (channel_id, int(time.time()))
        insert_command = self.commands['insert-channel-no-recordings-mixer']
        conn.execute(insert_command, tuple_to_insert)
        return

    def insert_recording_for_channel(self, conn, recording):
        insert_command = self.commands['insert-recording-mixer']
        conn.execute(insert_command, recording.to_db_tuple())
        return

    def insert_logs(self, conn, log_name, time_started, timelog_str, stats_str):
        insert_command = self.commands['insert-log-mixer']
        tuple_to_insert = (log_name, time_started, int(time.time()), timelog_str, stats_str, )
        conn.execute(insert_command, tuple_to_insert)
        return

    # Select -------------------------------------------------------------------

    # returns a lookup table of channel_ids for channels that are already in the database
    # needs an existing connection to run
    def get_all_channel_ids(self, conn):
        ids = {}
        for row in conn.execute(self.commands['get-all-channel-ids-mixer']):
            ids[row[0]] = True
        return ids


    # returns a lookup table of game_ids for games that are already in database
    def get_all_game_ids(self, conn):
        ids = {}
        for row in conn.execute(self.commands['get-all-game-ids-mixer']):
            ids[row[0]] = True
        return ids


    # returns a list of all channel IDs that IndieOutreach hasn't scraped for recordings yet
    def get_channel_ids_that_need_recordings(self, conn):
        ids = []
        ids_to_ignore = {}
        for row in conn.execute(self.commands['get-channel-ids-that-have-recordings-mixer']):
            ids_to_ignore[row[0]] = True
        for row in conn.execute(self.commands['get-channel-ids-with-no-recordings-mixer']):
            ids_to_ignore[row[0]] = True
        for row in conn.execute(self.commands['get-all-channel-ids-mixer']):
            if (row[0] not in ids_to_ignore):
                ids.append(row[0])
        return ids

    # returns a list of channel IDs that haven't been active in the last 24 hours
    def get_inactive_channel_ids(self, conn):
        ids = []
        time_cutoff = int(time.time()) - (1 * 60 * 60 * 24) # <- 24 hours ago
        select_command = self.commands['get-channel-ids-whose-most-recent-entry-was-before']
        select_command = select_command.replace('{table_name}', 'followers')
        select_command = select_command.replace('{date}', str(time_cutoff))
        for row in conn.execute(select_command):
            ids.append(row[0])
        return ids

# ==============================================================================
# Class: TwitchDBManager
# ==============================================================================

class TwitchDB():

    def __init__(self):
        self.filepath = './data/twitch.db' # <- the filepath to the db file
        self.commands = self.load_commands()
        return

    def load_commands(self):

        def __load_from_file(commands, filepath):
            f = json.load(open(filepath))
            for command_name, command_list in f.items():
                if (len(command_list) > 1):
                    commands[command_name] = command_list
                else:
                    commands[command_name] = command_list[0]
            return commands

        commands = __load_from_file({}, './sql/twitch_create.json')
        commands = __load_from_file(commands, './sql/twitch_insert.json')
        commands = __load_from_file(commands, './sql/twitch_select.json')
        return commands



    # Connect ------------------------------------------------------------------

    def get_connection(self):
        return sqlite3.connect(self.filepath, timeout = 1 * 60 * 15) # <- 15 minutes

    # Create -------------------------------------------------------------------

    def create_tables(self):
        conn = sqlite3.connect(self.filepath)
        for command in self.commands['create-tables-twitch']:
            conn.execute(command)
        conn.commit()
        conn.close()


    # Insert -------------------------------------------------------------------

    # inserts a new streamer into streamers table
    def insert_new_streamer(self, conn, streamer):
        conn.execute(self.commands['insert-new-streamer-twitch'], streamer.to_db_tuple('insert'))
        return


    # updates an existing streamer in the streamers table
    def update_streamer(self, conn, streamer):
        update_command = self.commands['update-existing-streamer-twitch'].replace('{streamer_id}', str(streamer.id))
        conn.execute(update_command, streamer.to_db_tuple('update'))
        return

    # inserts a TwitchGame into games table
    def insert_game(self, conn, game):
        conn.execute(self.commands['insert-game-twitch'], game.to_db_tuple())
        return

    # inserts a StatsBucket object into the game_snapshots table
    def insert_game_snapshot(self, conn, game_stats):
        conn.execute(self.commands['insert-game-snapshot-twitch'], game_stats.to_db_tuple())
        return

    # inserts a TwitchTag into tags table
    def insert_tag(self, conn, tag):
        conn.execute(self.commands['insert-tag-twitch'], tag.to_db_tuple())
        return

    # insert a TwitchLivestream object into livestream_snapshots table
    def insert_livestream_snapshot(self, conn, livestream):
        conn.execute(self.commands['insert-livestream-snapshot-twitch'], livestream.to_db_tuple())


    def insert_logs(self, conn, log_name, time_started, timelog_str, stats_str):
        insert_command = self.commands['insert-log-twitch']
        tuple_to_insert = (log_name, time_started, int(time.time()), timelog_str, stats_str, )
        conn.execute(insert_command, tuple_to_insert)
        return

    # Select -------------------------------------------------------------------

    # returns a lookup table of streamer_ids for streamers that are already in the database
    def get_all_streamer_ids(self, conn):
        ids = {}
        for row in conn.execute(self.commands['get-all-streamer-ids-twitch']):
            ids[row[0]] = True
        return ids

    # returns a lookup table of game_ids for games that are already in the database
    def get_all_game_ids(self, conn):
        ids = {}
        for row in conn.execute(self.commands['get-all-game-ids-twitch']):
            ids[row[0]] = True
        return ids

    # returns a lookup table of tag_ids that already exist in database
    def get_all_tag_ids(self, conn):
        ids = {}
        for row in conn.execute(self.commands['get-all-tag-ids-twitch']):
            ids[row[0]] = True
        return ids
