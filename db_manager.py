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

        commands = __load_from_file({}, './sql/create.json')
        commands = __load_from_file(commands, './sql/insert.json')
        commands = __load_from_file(commands, './sql/select.json')
        return commands



    # Connect ------------------------------------------------------------------

    def get_connection(self):
        return sqlite3.connect(self.filepath)

    # Create -------------------------------------------------------------------

    def create_tables(self):
        conn = sqlite3.connect(self.filepath)
        for command in self.commands['create-tables-mixer']:
            conn.execute(command)
        conn.commit()
        conn.close()


    # Insert -------------------------------------------------------------------

    #
    def insert_new_channel(self, conn, channel):
        conn.execute(self.commands['insert-new-channel-mixer'], channel.get_db_tuple('insert-channel'))
        return


    def update_channel(self, conn, channel):
        command = self.commands['update-channel-mixer'].replace('{channel_id}', str(channel.id))
        conn.execute(command, channel.get_db_tuple('update-channel'))
        return



    # Select -------------------------------------------------------------------

    # returns a lookup table of channel_ids for channels that are already in the database
    # needs an existing connection to run
    def get_all_channel_ids(self, conn):
        ids = {}
        for row in conn.execute(self.commands['get-all-channel-ids-mixer']):
            ids[row[0]] = True
        return ids


# ==============================================================================
# Class: TwitchDBManager
# ==============================================================================

class TwitchDB():
    def __init__(self):
        return
