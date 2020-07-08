#!/usr/bin/env python
# ==============================================================================
# About: eztime.py
# ==============================================================================
# eztime.py is a tool for converting to and from unix epoch time in a convenient way
# -> this tool can be referenced while testing SQL queries
#


# Imports ----------------------------------------------------------------------

import sys
import time
import datetime
import argparse


# Constants --------------------------------------------------------------------

CURRENT_TIME = int(time.time())

# Command Line Arguments -------------------------------------------------------

__reference_description   = """The --reference-time flag will set what unix epoch time the program will center its calculations off of.
                                You can input a unix epoch time or a timestamp in the form of `mm/dd/yyyy`.
                                If you do not specify a reference-time, the program will default to the current time. """
__mods_description        = """To use the --modifications flag, specify a list of integers that will be added/subtracted from the current epoch time.
                                The integers are in seconds, but they will be converted according to the --units flag.
                                Specifying 0 will return the current time."""
__units_description       = """The --units flag allows you to specify what units of time are used by the program.
                                If no unit is specified, this program will use hours as its base unit.
                                Available Units are: [seconds, minutes, hours, days, weeks, months, years]"""


parser = argparse.ArgumentParser()
parser.add_argument('-t', '--reference-time', dest='reference_time', type=str,  help=__reference_description)
parser.add_argument('-m', '--modifications',  dest='modifications',  nargs='+', help=__mods_description)
parser.add_argument('-u', '--units',          dest='units',          type=str,  help=__units_description)
args = parser.parse_args()


# Preprocessing ----------------------------------------------------------------

# Handle Units
UNIT_MULTIPLIER = 60 * 60       # <- Default to hours
UNIT_NAME = "hours"
if (args.units is not None):
    UNIT_NAME = args.units
    if (args.units == 'seconds'):
        UNIT_MULTIPLIER = 1
    elif (args.units == 'minutes'):
        UNIT_MULTIPLIER = 60
    elif (args.units == 'hours'):
        UNIT_MULTIPLIER = 60 * 60
    elif (args.units == 'days'):
        UNIT_MULTIPLIER = 60 * 60 * 24
    elif (args.units == 'weeks'):
        UNIT_MULTIPLIER = 60 * 60 * 24 * 7
    elif (args.units == 'months'):
        UNIT_MULTIPLIER = 60 * 60 * 24 * 30
    elif (args.units == 'years'):
        UNIT_MULTIPLIER = 60 * 60 * 24 * 365
    else:
        print("Please specify a valid unit of time from list: [seconds, minutes, hours, days, weeks, months, years].")
        sys.exit()


# Get Reference Time
REFERENCE_TIME = CURRENT_TIME
if (args.reference_time is not None):
    if ('/' in args.reference_time):
        REFERENCE_TIME = int(time.mktime(time.strptime(args.reference_time, '%m/%d/%Y')))
    else:
        REFERENCE_TIME = int(args.reference_time)


# Functions --------------------------------------------------------------------

def print_reference_time():
    print('Reference Time ----------------------------------------------------')
    print(f" - {REFERENCE_TIME}")
    print(f" - {datetime.datetime.fromtimestamp(REFERENCE_TIME).strftime('%c')}")
    if (REFERENCE_TIME == CURRENT_TIME):
        print(" - This *IS* the current time. ")
    else:
        print(" - This *IS NOT* the current time. ")
    print('')

def handle_modifications(subtraction_list):
    list_epoch = {'+': [], '-': []}
    list_stamp = {'+': [], '-': []}
    if (subtraction_list is not None):
        for t in subtraction_list:
            converted_positive = REFERENCE_TIME + int(t) * UNIT_MULTIPLIER
            converted_negative = REFERENCE_TIME - int(t) * UNIT_MULTIPLIER
            list_epoch['+'].append(converted_positive)
            list_epoch['-'].append(converted_negative)
            list_stamp['+'].append(datetime.datetime.fromtimestamp(converted_positive).strftime('%c'))
            list_stamp['-'].append(datetime.datetime.fromtimestamp(converted_negative).strftime('%c'))
    else:
        return

    print('Modification Times ------------------------------------------------')
    for key in ['+', '-']:
        for i in range(len(list_epoch[key])):
            print(f" {key} [{subtraction_list[i]} {UNIT_NAME}] {list_stamp[key][i]} -> {list_epoch[key][i]}")

# Main -------------------------------------------------------------------------

def run():
    print('')
    print_reference_time()
    handle_modifications(args.modifications)
    print('')

# Run --------------------------------------------------------------------------

if (__name__ == '__main__'):
    run()
else:
    print('FUCK')
