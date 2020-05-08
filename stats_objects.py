# ==============================================================================
# About: stats_objects.py
# ==============================================================================
#
# stats_objects.py contains classes that are helpful for calculating stats
# - StatsBucket - useful for getting min, max, averages on a sample set.
#               -> this is used by MixerScraper to get stats about game's viewership
#

# Imports ----------------------------------------------------------------------

import sys
import math
import time

# ==============================================================================
# Class: StatsBucket
# ==============================================================================

# Assumption: all values added to StatsBucket are non-negative
class StatsBucket():
    def __init__(self, id):
        self.id         = id # <- ID for saying what the bucket is for
        self.data       = [] # <- data being added together
        self.num_added  = 0  # <- the number of times .add() was called
        self.num_zero   = 0  # <- the number of times .add() was called w/ a value of 0
        self.date_initialized = int(time.time())
        return

    # adds data to the StatsBucket object
    def add(self, v):
        if (v == 0):
            self.num_zero += 1
        else:
            self.data.append(v)
            self.num_added += 1

    # resets the StatsBucket to be as if it were empty
    def reset(self):
        self.data      = []
        self.num_added = 0
        self.num_zero  = 0
        self.date_initialized = int(time.time())

    # returns stats about the data in the bucket
    def get_stats(self):
        stats = {'mean': 0, 'max': False, 'min': False, 'median': 0, 'std_dev': 0, 'total': 0}
        stats['num_items'] = self.num_added
        stats['num_zero']  = self.num_zero

        n = len(self.data)
        if (n == 0):
            stats['max'] = 0
            stats['min'] = 0
            return stats

        # grab median
        self.data.sort()
        midpoint = int(len(self.data) / 2)
        stats['median'] = self.data[midpoint]

        # calculate mean
        for v in self.data:
            stats['mean']  += v
            stats['total'] += v
            stats['min']    = v if (v < stats['min'] or stats['min'] == False) else stats['min']
            stats['max']    = v if (v > stats['max'] or stats['max'] == False) else stats['max']
        stats['mean'] = stats['mean'] / n

        # calculate variance and std_dev
        for v in self.data:
            stats['std_dev'] += (stats['mean'] - v) ** 2
        stats['std_dev'] = stats['std_dev'] / (n - 1) if (n > 1) else stats['std_dev']
        stats['std_dev'] = math.sqrt(stats['std_dev'])

        # round results
        stats['mean']    = round(stats['mean'], 2)
        stats['std_dev'] = round(stats['std_dev'], 2)

        return stats


    def to_db_tuple(self):
        stats = self.get_stats()
        return (
            self.id,
            self.date_initialized,
            stats['num_items'],
            stats['num_zero'],
            stats['total'],
            stats['min'],
            stats['max'],
            stats['median'],
            stats['mean'],
            stats['std_dev']
        )
