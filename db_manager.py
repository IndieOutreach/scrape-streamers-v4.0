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
        return


    def create_tables(self):
        f = json.load(open('./sql/create.json'))
        conn = sqlite3.connect(self.filepath)
        for command in f['create-tables-mixer']:
            conn.execute(command)
        conn.commit()
        conn.close()


# ==============================================================================
# Class: TwitchDBManager
# ==============================================================================

class TwitchDB():
    def __init__(self):
        return
