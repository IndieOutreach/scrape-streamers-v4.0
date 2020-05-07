# ==============================================================================
# About logs.py
# ==============================================================================
#
# This file contains different types of logs that are useful for the scraper
# - TimeLogs is used for tracking the frequency / length of API requests
#


# Imports ----------------------------------------------------------------------

import sys
import csv
import time
import math
import datetime


# TimeLogs ---------------------------------------------------------------------

# class is used to record timing and number of different actions (ie: API requests)
# - It is imported by TwitchAPI
# NOTE: all times are in milliseconds
class TimeLogs():

    def __init__(self, action_categories):
        self.logs = {} # { request_name: [ {request_obj}, ... ] }
        self.action_categories = action_categories
        for type in action_categories:
            self.logs[type] = []
        self.time_initialized = self.__get_current_time()
        self.items_processed = 0


    # resets TimeLogs object
    def reset(self):
        self.logs = {}
        for type in self.action_categories:
            self.logs[type] = []
        self.time_initialized = self.__get_current_time()
        self.items_processed = 0

    # Actions ------------------------------------------------------------------

    def start_action(self, action_type):

        # case 0: this action type DNE and needs to be registered
        if (action_type not in self.logs):
            self.logs[action_type] = [ {'start': self.__get_current_time(), 'end': 0} ]
            return

        # case 1: there are no actions on record
        if (len(self.logs[action_type]) == 0):
            self.logs[action_type].append({'start': self.__get_current_time(), 'end': 0})
            return

        # case 2: the latest action is already finished so we can register a new one
        # -> note: if the current action is not finished yet, we can't do anything
        current_action = self.logs[action_type][-1]
        if (current_action['end'] > 0):
            self.logs[action_type].append({'start': self.__get_current_time(), 'end': 0})
            return


    def end_action(self, action_type):

        if ((action_type not in self.logs) or (len(self.logs[action_type]) == 0)):
            return

        last_index = len(self.logs[action_type]) - 1
        if (self.logs[action_type][last_index]['end'] == 0):
            self.logs[action_type][last_index]['end'] = self.__get_current_time()


    def get_time_since_start(self):
        t = self.__get_current_time() - self.time_initialized
        return round(t, 2)


    # returns the current time in milliseconds
    def __get_current_time(self):
        return int(round(time.time() * 1000))

    def set_number_of_items(self, num):
        self.items_processed = num


    # Stats --------------------------------------------------------------------

    def print_stats(self):
        for action_category, actions in self.logs.items():
            stats = self.__calc_stats_about_action(actions)
            print("Request: ", action_category)
            print(" - total: ", stats['n'], "requests")
            if (len(actions) > 0):
                print(" - mean: ", stats['mean'], "ms")
                print(" - std_dev: ", stats['std_dev'], "ms")
                print(" - min: ", stats['min'], "ms")
                print(" - max: ", stats['max'], "ms")
        print("Total Time: ", self.get_time_since_start(), "ms")

    # gets stats about each request in logs
    def get_stats_from_logs(self):
        stats = {}
        for action_category, actions in self.logs.items():
            if (len(actions) > 0):
                stats[action_category] = self.__calc_stats_about_action(actions)
        return stats

    def __calc_stats_about_action(self, actions):

        first_start, last_end = False, False
        min_val, max_val   = 9999999, -1
        mean, var, std_dev = 0, 0, 0

        if (len(actions) == 0):
            return {'n': 0, 'min': 0, 'max': 0, 'std_dev': 0, 'first_start': 0, 'last_end': 0}

        # convert actions from {'start', 'end'} objects into time_per_action
        times = []
        for action in actions:
            if (action['end'] > 0):
                time_took = action['end'] - action['start']
                times.append(time_took)
                min_val = time_took if (time_took < min_val) else min_val
                max_val = time_took if (time_took > max_val) else max_val

                first_start = action['start'] if ((first_start == False) or (action['start'] < first_start)) else first_start
                last_end = action['end'] if ((last_end == False) or (action['end'] > last_end)) else last_end

        # calc mean
        for t in times:
            mean += t
        mean = mean / len(times)

        # calc std_dev
        for t in times:
            var += (mean - t) ** 2
        if (len(times) > 1):
            var = var / (len(times) - 1)
        std_dev = math.sqrt(var)

        stats = {
            'n': len(actions),
            'min': min_val,
            'max': max_val,
            'mean': round(mean, 2),
            'std_dev': round(std_dev, 2),
            'first_start': first_start,
            'last_end': last_end
        }
        return stats
