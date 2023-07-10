# -*- coding: utf-8 -*-

"""
    __  ___      __    _ __     ____  _   _____
   /  |/  /___  / /_  (_) /__  / __ \/ | / /   |
  / /|_/ / __ \/ __ \/ / / _ \/ / / /  |/ / /| |
 / /  / / /_/ / /_/ / / /  __/ /_/ / /|  / ___ |
/_/  /_/\____/_.___/_/_/\___/_____/_/ |_/_/  |_|

HELPER FUNCTIONS

-- Coded by Wouter Durnez
-- mailto:Wouter.Durnez@UGent.be
"""

import os
import random as rnd
import sys
import time
from datetime import datetime
from pathlib import Path
from pprint import PrettyPrinter
from typing import Callable

import numpy as np
import pandas as pd
from termcolor import colored

import matplotlib.pyplot as plt
import seaborn as sns

pp = PrettyPrinter(indent=4)

####################
# GLOBAL VARIABLES #
####################

# Set log level (1 = only top level log messages -> 3 = all log messages)
LOG_LEVEL = 3
DATA_DIR = os.path.join(os.pardir, os.pardir, 'data')
CACHE_DIR = os.path.join(os.curdir, 'cache')
INDICES = {'notifications', 'appevents', 'sessions', 'logs', 'connectivity'}
INDEX_FIELDS = {
    'notifications': [
        'application',
        'data_version',
        'id',
        'notificationID',
        'ongoing',
        'posted',
        'priority',
        'studyKey',
        'surveyId',
        'time'],
    'appevents': [
        'application',
        'battery',
        'data_version',
        'startTime',
        'endTime',
        'id',
        'latitude',
        'longitude',
        'model',
        'notification',
        'notificationId',
        'session',
        'studyKey',
        'surveyId'
    ],
    'sessions': [
        'startTime',
        'endTime',
        'data_version',
        'id',
        'sessionID',
        'studyKey',
        'surveyId',
        'session on',  # TODO: remove later
        'session off'  # TODO: remove later
    ],
    'logs': [
        'data_version',
        'id',
        'studyKey',
        'surveyId',
        'logging enabled',
        'date'
    ],
    'connectivity': [
        'latitude',
        'longitude',
        'networkOperatorName',
        'networkType',
        "signalStrengthAsu",
        "signalStrengthDbm",
        "signalStrengthLevel",
        "timestampMillis",
        'timestamp',
        'id',
    ]
}
# Fields for a more lightweight df:
MIN_INDEX_FIELDS = {
    'appevents': [
        'id',
        'application',
        'startTime',
        'endTime',
        'session',
        'surveyId'
    ],
    'notifications': [
        'id',
        'application',
        'ongoing',
        'posted',
        'priority',
        'surveyId',
        'time'],
}


####################
# Helper functions #
####################

def set_param(log_level=None, data_dir=None, cache_dir=None):
    """
    Set mobileDNA parameters.

    :param log_level: new value for log level
    :param data_dir: new data directory
    """

    # Declare these variables to be global
    global LOG_LEVEL
    global DATA_DIR
    global CACHE_DIR

    # Set log level
    if log_level:
        LOG_LEVEL = log_level

    # Set new data directory
    if data_dir:
        DATA_DIR = data_dir

    # Set new cache directory
    if cache_dir:
        CACHE_DIR = cache_dir


def log(*message, lvl=3, sep="", title=False):
    """
    Print wrapper that adds timestamp, and can be used to toggle levels of logging info.

    :param message: message to print
    :param lvl: importance of message: level 1 = top importance, level 3 = lowest importance
    :param sep: separator
    :param title: toggle whether this is a title or not
    :return: /
    """

    # Set timezone
    if 'TZ' not in os.environ and sys.platform == 'darwin':
        os.environ['TZ'] = 'Europe/Amsterdam'
        time.tzset()

    # Title always get shown
    lvl = 1 if title else lvl

    # Print if log level is sufficient
    if lvl <= LOG_LEVEL:

        # Print title
        if title:
            n = len(*message)
            print('\n' + (n + 4) * '#')
            print('# ', *message, ' #', sep='')
            print((n + 4) * '#' + '\n')

        # Print regular
        else:
            t = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())
            print(str(t), (" - " if sep == "" else "-"), *message, sep=sep)

    return


def time_it(f: Callable):
    """
    Timer decorator: shows how long execution of function took.
    :param f: function to measure
    :return: /
    """

    def timed(*args, **kwargs):
        t1 = time.time()
        res = f(*args, **kwargs)
        t2 = time.time()

        log("\'", f.__name__, "\' took ", round(t2 - t1, 3), " seconds to complete.", sep="")

        return res

    return timed


def set_dir(*dirs):
    """
    If folders don't exist, make them.

    :param dirs: directories to check/create
    :return: None
    """

    for dir in dirs:
        if not os.path.exists(dir):
            os.makedirs(dir)
            log("WARNING: Data directory <{dir}> did not exist yet, and was created.".format(dir=dir), lvl=1)
        else:
            log("\'{}\' folder accounted for.".format(dir), lvl=3)


##################
# Time functions #
##################

def split_time_range(time_range: tuple, duration: pd.Timedelta, ignore_error=False) -> tuple:
    """
    Takes a time range (formatted strings: '%Y-%m-%dT%H:%M:%S.%f'), and selects
    a random interval within these boundaries of the specified active_screen_time.

    :param time_range: tuple with formatted time strings
    :param duration: timedelta specifying the active_screen_time of the new interval
    :param ignore_error: (bool) if true, the function ignores durations
                         that exceed the original length of the time range
    :return: new time range
    """

    # Convert the time range strings to unix epoch format
    start = datetime.strptime(time_range[0], '%Y-%m-%dT%H:%M:%S.%f').timestamp()
    stop = datetime.strptime(time_range[1], '%Y-%m-%dT%H:%M:%S.%f').timestamp()

    # Calculate total active_screen_time (in seconds) of original
    difference = stop - start

    # Calculate active_screen_time of new interval (in seconds)
    duration = duration.total_seconds()

    # Error handling
    if difference < duration:

        if ignore_error:
            log(
                "WARNING: New interval length exceeds original time range active_screen_time! Returning original time range.")
            return time_range

        else:
            raise Exception('ERROR: New interval length exceeds original time range active_screen_time!')

    # Pick random new start and stop
    new_start = rnd.randint(int(start), int(stop - duration))
    new_stop = new_start + duration

    # Format new time range
    new_time_range = (datetime.fromtimestamp(new_start).strftime('%Y-%m-%dT%H:%M:%S.%f')[:-3],
                      datetime.fromtimestamp(new_stop).strftime('%Y-%m-%dT%H:%M:%S.%f')[:-3])

    return new_time_range


def remove_first_and_last(df: pd.DataFrame, col='startDate') -> pd.DataFrame:
    """
    Chop the first and last day off of a data frame, on the basis of startDates.
    WARNING: does this over the whole data frame, ignoring ids. Use in combination with groupby.

    :param df: input data frame
    :param col: column on which to perform operation
    :return: filtered data frame
    """

    # Get first and last date
    first, last = list(df[col].agg(['min', 'max']))

    # Restrict original df
    df = df.loc[(df[col] != first) & (df[col] != last)]

    return df


def longest_uninterrupted(df: pd.DataFrame, column='startDate') -> pd.DataFrame:
    """
    Filter data frame to retain longest uninterrupted logging period (based on designated column)
    :param df: data frame
    :param column: date column
    :return: filtered data frame
    """

    if len(df.id.unique()) > 1:
        raise Exception("Cannot apply function to data frame from multiple ids. Use groupby.")

    # Get unique dates from data frame
    dates = sorted(df[column].unique())

    # Silence some warnings
    previous = None
    run, longest = [], []

    # Loop over indexed dates
    for idx, date in enumerate(dates):

        # Calculate difference

        # If we're at the first, set up our run (which is now the longest run)
        if idx == 0:

            run = [date]
            longest = [date]

        # If current date does not follow previous date, or if we reached end of the line
        elif ((date - previous).astype('timedelta64[D]') / np.timedelta64(1, 'D')) != 1:

            # Start new run
            run = [date]

        # In any other case, keep updating run
        else:
            run.append(date)

        if len(run) > len(longest):
            longest = run

        # Remember last date
        previous = date

    # Print some output
    log(f"Longest uninterrupted log period for {df.id.iloc[0]}: {len(longest)} days.", lvl=4)

    # Filter data frame
    df = df.loc[df[column].isin(longest)]

    return df


############################
# Initialization functions #
############################

def hi(title=None, log_level: int = None, data_dir=None, cache_dir: str = None, ):
    """
    Say hello. (It's stupid, I know.)
    If there's anything to initialize, do so here.
    """

    print()
    print(colored("                   _     _ _     ______ _   _   ___", 'blue'))
    print(colored("                  | |   (_) |    |  _  \ \ | | / _ \ ", 'blue'))
    print(colored("   _ __ ___   ___ | |__  _| | ___| | | |  \| |/ /_\\ \\", 'blue'))
    print(colored("  | '_ ` _ \ / _ \| '_ \| | |/ _ \ | | | . ` ||  _  |", 'blue'))
    print(colored("  | | | | | | (_) | |_) | | |  __/ |/ /| |\  || | | |", 'blue'))
    print(colored("  |_| |_| |_|\___/|_.__/|_|_|\___|___/ \_| \_/\_| |_/", 'blue'))
    print()

    if title:
        log(title, title=True)

    # Set cache dir
    if not cache_dir:
        path = Path(os.path.dirname(os.path.abspath(__file__)))
        cache_dir = os.path.join(path.parent, 'cache')

    set_param(log_level=log_level, data_dir=data_dir, cache_dir=cache_dir)

    print("📝 LOG_LEVEL is set to {}.".format(colored(LOG_LEVEL, 'red')))
    print("🗄 DATA_DIR is set to {}".format(colored(os.path.abspath(DATA_DIR), 'red')))
    print("🫗 CACHE_DIR is set to {}".format(colored(CACHE_DIR, 'red')))
    print()

    # Set this warning if you intend to keep working on the same data frame,
    # and you're not too worried about messing up the raw data.
    pd.set_option('chained_assignment', None)
    pd.set_option('display.max_rows', 500)
    pd.set_option('display.max_columns', 500)
    pd.set_option('display.width', 1000)

    # Set a random seed
    rnd.seed(616)


########################
# Data frame functions #
########################

def check_index(df: pd.DataFrame, index: str, ignore_error=False) -> bool:
    """
    Checks if a data frame is indeed of the right index type.

    :param df: data frame that will be checked
    :param index: type of data that is expected
    :return: (bool) checks out (True) or doesn't (False)
    """

    # Check index argument
    if index not in INDICES:
        raise Exception(
            "ERROR: When checking index type, please enter valid index"
            " ('appevents','notifications', 'logs', 'sessions' or 'connectivity'.")

    unique_columns = {
        'appevents': 'session',
        'notifications': 'time',
        'sessions': 'session on',
        'logs': 'date',
        'connectivity': 'networkOperatorName'
    }

    # Check what type of data we're dealing with in reality
    true_index = None

    # Go over unique columns, and check if they're in our data frame
    for unique_key in unique_columns.keys():

        # If they are, that's the type of data frame we're dealing with
        if unique_columns[unique_key] in df:
            true_index = unique_key
            break

    # If our data type is not what we expected, return False (or throw an error)
    if true_index != index:
        if ignore_error:
            log(f"Unexpected index! Expected <{index}>, but got <{true_index}>.", lvl=3)
            return False
        else:
            raise Exception(f"ERROR: Unexpected index! Expected <{index}>, but got <{true_index}>.")

    # ...else return that check is A-OK
    return True


def format_data(df: pd.DataFrame, index: str) -> pd.DataFrame:
    """
    Set the data types of each column in a data frame, depending on the index.
    This is done to save memory.

    :param df: data frame to format
    :param index: type of data
    :return: formatted data frame
    """

    # Check if index is valid
    if index not in INDICES:
        raise Exception("ERROR: Invalid doc type! Please choose 'appevents', 'notifications', 'sessions', or 'logs'.")

    elif index == 'appevents':

        # Reformat data version (trying to convert to int)
        try:
            df.data_version = pd.to_numeric(df.data_version, downcast='float')
        except ValueError:
            df.data_version = df.data_version.astype(str)
        except AttributeError as e:
            print(e)

        # Format timestamps
        df.startTime = df.startTime.astype('datetime64[ns]')
        df.endTime = df.endTime.astype('datetime64[ns]')

        # Downcast lat/long
        try:
            df.latitude = pd.to_numeric(df.latitude, downcast='float')
            df.longitude = pd.to_numeric(df.longitude, downcast='float')
        except Exception as e:
            print(e)

        # Downcast battery column
        try:
            df.battery = df.battery.astype('uint8')
        except Exception as e:
            print(e)

        # Factorize categorical variables (ids, apps, session numbers, etc.)
        to_category = ['id', 'application', 'session', 'studyKey', 'surveyId', 'model']
        for column in to_category:
            try:
                df[column] = df[column].astype('category')
            except Exception as e:
                print(e)

    elif index == 'notifications':

        df.time = df.time.astype('datetime64[ns]')
        df.id = df.id.astype('category')
        df.application = df.application.astype('category')
        df.notificationID = df.notificationID.astype('category')
        df.studyKey = df.studyKey.astype('category')
        df.surveyId = df.surveyId.astype('category')

    elif index == 'sessions':

        # Convert to timestamp
        df['timestamp'] = df.timestamp.astype('datetime64[ns]')

        # Sort data frame
        df.sort_values(by=['id', 'timestamp'], inplace=True)
        df.reset_index(drop=True, inplace=True)
        df.rename(columns={'timestamp': 'startTime'}, inplace=True)

        # Add end timestamp
        df['endTime'] = df.groupby('id')['startTime'].shift(-1)
        df['session off'] = df.groupby('id')['session on'].shift(-1)
        # print(df.head(20))

        # Add ID which links with appevents index
        df['sessionID'] = pd.to_numeric(df['startTime'], downcast='unsigned') - 3600
        # print('original', len(df))

        # Get indices for valid entries, that have a start and a stop to them
        valids = (df['session on'] == True) & (df['session off'] == False)
        # print('valids', np.sum(valids))

        # Remove bogus rows
        df = df.loc[df['session on'] == True]

        # Mark the end time of invalid entries as nan
        # df = df.loc[df['session off'] == True]
        df.loc[(df['session off'] == True), 'endTime'] = None

        # Return some info
        log(f"Formatted sessions, accounted for {np.sum(valids)}/{len(df)} "
            f"({100 * np.round(np.sum(valids) / len(df), 2)}%)", lvl=3)

    elif index == 'logs':

        df['date'] = df.date.astype('datetime64[ns]')

    for col in df.columns:

        if col.startswith('Unnamed') or col not in INDEX_FIELDS[index]:
            df.drop(labels=[col], axis=1, inplace=True)

    # Drop duplicates
    #df.drop_duplicates(inplace=True)

    log("Successfully formatted dataframe.", lvl=3)

    return df


def add_duration(df: pd.DataFrame, clear_negatives=True) -> pd.DataFrame:
    """
    Calculate app event duration and add to (new) data frame.

    :param df: data frame to process (should be appevents or sessions index)
    :return: modified data frame
    """

    # Check if data contains necessary columns
    if 'startTime' not in df.columns or \
            'endTime' not in df.columns:
        raise Exception("ERROR: Necessary columns missing!")

    # Convert to correct data types
    try:
        df.startTime = df.startTime.astype('datetime64[ns]')
    except Exception as e:
        print('Could not convert startTime column to datetime format: ', e)
    try:
        df.endTime = df.endTime.astype('datetime64[ns]')
    except Exception as e:
        print('Could not convert endTime column to datetime format.', e)

    # Calculate duration (in seconds)
    try:
        df['duration'] = (df['endTime'] - df['startTime']).dt.total_seconds()
    except:
        raise Exception("ERROR: Failed to calculate duration!")

    # Check if there are any negative durations.
    if not df[df["duration"] < 0].empty:

        # Store proportion of negative durations
        negative_proportion = round(100 * len(df[df["duration"] < 0]) / len(df), 4)

        # Clear negatives if requested
        if clear_negatives:

            log(f"WARNING: encountered negative duration! Removing from data frame... ({negative_proportion}%)", lvl=1)
            df = df.loc[df["duration"] >= 0]

        else:
            log(f"WARNING: encountered negative duration! ({negative_proportion}%)", lvl=1)

    return df


def add_dates(df: pd.DataFrame, index: str) -> pd.DataFrame:
    """
    Get dates from datetime columns and add them as new column.

    :param df: data frame to process
    :param index: type of data
    :return: adjusted data frame
    """
    if index == 'appevents' or index == 'sessions':

        df['startDate'] = pd.to_datetime(df.startTime.dt.date)
        df['endDate'] = pd.to_datetime(df.endTime.dt.date)

    elif index == 'notifications':

        df['date'] = df.time.dt.date

    elif index == 'connectivity':

        df['date'] = df.timestamp.dt.date

    else:
        log('Wrong index: nothing changed!', lvl=1)

    return df


def get_unique(column: str, df: pd.DataFrame) -> np.ndarray:
    """
    Get list of unique column values in given data frame.

    :param column: column to sift through
    :param df: data frame to look in
    :return: unique values in given column
    """

    try:
        unique_values = df[column].unique()
    except:
        raise Exception("ERROR: Could not find variable {column} in dataframe.".format(column=column))

    return unique_values

###########################
# Visualization functions #
###########################

def plot_logdays_freq(df: pd.DataFrame) -> plt.figure:
    """
    Plot histogram of # logdays for each logger
    :param df: appevents dataframe
    returns: a matplotlib figure
    """
    df['date'] = df.startTime.dt.day
    # loggers per date
    loggers = df.groupby('id')['date'].nunique()

    fig, axes = plt.subplots(1,1, figsize=(12,8))

    sns.histplot(data=loggers, ax=axes)

    axes.set_xlabel('logging days')
    axes.set_ylabel('# loggers')
    plt.title('Histogram # logging days per person')

    return fig

#####################
# Storage functions #
#####################


def save(df: pd.DataFrame, dir: str, name: str, csv_file=True, pickle=False, parquet=False):
    """
    Wrapper function to save mobileDNA data frames.

    :param df: data to store on disk
    :param dir: location to store it in
    :param name: name of the file
    :param csv_file: save in CSV format (bool)
    :param pickle: save in pickle format (bool)
    :param parquet: save in parquet format (bool)
    :return: /
    """

    # Check if directory exists
    if not os.path.exists(dir):
        set_dir(dir)

    path = os.path.join(dir, name)

    # Store to CSV
    if csv_file:

        # Try and save it
        try:

            df.to_csv(path_or_buf=path + ".csv", sep=";", decimal='.')
            log("Saved data frame to {}".format(path + ".csv"))

        except Exception as e:

            log("ERROR: Failed to store data frame as CSV! {e}".format(e=e), lvl=1)

    # Store to pickle
    if pickle:

        try:

            df.to_pickle(path=path + ".pkl")
            log("Saved data frame to {}".format(path + ".pkl"))

        except Exception as e:

            log("ERROR: Failed to pickle data frame! {e}".format(e=e), lvl=1)

    # Store to parquet
    if parquet:

        try:
            df.to_parquet(path=path + ".parquet", engine='auto', compression='snappy')
            log("Saved data frame to {}".format(path + ".parquet"))

        except Exception as e:

            log("ERROR: Failed to store data frame as parquet! {e}".format(e=e), lvl=1)


@time_it
def load(path: str, index: str, file_type='infer', sep=';', dec='.', format=False, bare=False) -> pd.DataFrame:
    """
    Wrapper function to load mobileDNA data frames.

    :param path: location of data frame
    :param index: type of mobileDNA data
    :param file_type: file type (default: infer from path, other options: pickle, csv, or parquet)
    :param sep: field separator
    :param dec: decimal symbol
    :param bare: load only the most necessary columns for a more lightweight dataframe
    :return: data frame
    """

    # Check if index is valid
    if index not in INDICES:
        raise Exception(
            "Invalid doc type! Please choose 'appevents', 'notifications', 'sessions', 'connectivity' or 'logs'.")

    # Set params if bare loading
    usecols = columns = MIN_INDEX_FIELDS[index] if bare else None

    # Load data frame, depending on file type
    if file_type == 'infer':

        # Get extension
        file_type = path.split('.')[-1]

        # Only allow the following extensions
        if file_type not in ['csv', 'pickle', 'pkl', 'parquet']:
            raise Exception("ERROR: Could not infer file type!")

        log("Recognized file type as <{type}>.".format(type=file_type), lvl=3)

    # CSV
    if file_type == 'csv':
        df = pd.read_csv(filepath_or_buffer=path,
                         # usecols=,
                         sep=sep, decimal=dec,
                         on_bad_lines='warn',
                         usecols=usecols)

    # Pickle
    elif file_type == 'pickle' or file_type == 'pkl':
        df = pd.read_pickle(path=path)

    # Parquet
    elif file_type == 'parquet':
        df = pd.read_parquet(path=path,
                             engine='auto',
                             columns=columns)

    # Unknown
    else:
        raise Exception("ERROR: You want me to read what now? Invalid file type! ")

    # If there's nothing there, just go ahead and return the empty df
    if df.empty:
        return df

    # Drop 'Unnamed' columns
    for col in df.columns:

        if col.startswith('Unnamed'):
            df.drop(labels=[col], axis=1, inplace=True)

    # Add duration if necessary
    """
    if 'duration' not in df and (
            check_index(df=df, index='appevents', ignore_error=True) or
            check_index(df=df, index='sessions', ignore_error=True)):
        add_duration(df)
    """
    if format:
        df = format_data(df=df, index=index)

    return df


################
# App metadata #
################

def load_meta(path=None) -> dict:
    """
    Load the app meta data dictionary
    :param path: if custom path, specify here, otherwise default cache location
    :return: app meta data dictionary
    """

    # If not specified, load from standard location
    if not path:
        path = os.path.join(CACHE_DIR, 'app_meta.npy')

    app_meta = dict(np.load(file=path, allow_pickle=True).item())

    return app_meta


def save_meta(app_meta: dict, dir=None, name='app_meta.npy'):
    """
    Save the app meta data dictionary
    :param app_meta: app meta data dictionary to store
    :param dir: if custom directory, specify here, otherwise default cache location
    """

    # If not specified, load from standard location
    if not dir:
        dir = CACHE_DIR

    np.save(file=os.path.join(dir, name), arr=app_meta)


def edit_meta(app_meta: dict, app_name: str, changes: dict, overwrite=True) -> dict:
    """
    Given an app meta data dictionary, make changes to a specific entry
    :param app_meta: the app meta data
    :param app_name: entry for which to make changes
    :param changes: dictionary with fields, which may already be present
    :param overwrite: whether to overwrite existing fields
    :return: adjusted dict
    """
    app_meta = app_meta.copy()

    if overwrite:
        app_meta[app_name] = app_meta[app_name] | changes
    else:
        app_meta[app_name] = changes | app_meta[app_name]

    return app_meta


def update_app_meta_keys(meta: dict) -> dict:
    """
    Updates app meta to change "fancyname" key into "name" key.

    :param meta: app meta dict
    :return: updated app meta dict
    """
    meta = meta.copy()

    try:
        for k, v in meta.items():
            try:
                v["name"] = v.pop("fancyname")
            except KeyError:
                pass
    except:
        pass

    return meta


def add_alias_to_meta(app_meta: dict, alias_dict: dict) -> dict:
    """
    Based on the cached app_meta and a provided dict with {alias: list_of_apps,},
    adds an alias key to the app_meta dictionary.

    :param app_meta: app_meta dictionary
    :param alias_dict: app alias dictionary with alias (key) and list of app (value)
    :return: app_meta dictionary with added alias key where provided
    """
    app_meta = app_meta.copy()

    for alias in alias_dict:
        for app in alias_dict[alias]:
            if app in app_meta:
                app_meta[app]["alias"] = alias
    return app_meta


########
# MAIN #
########

if __name__ in ['__main__', 'builtins']:
    # Howdy
    hi()

    # Load meta data
    meta = load_meta()

    # We'll change this entry
    name = 'com.facebook.orca'

    # These are the fields we want to add/change
    changes = {'our_name': 'facebook', 'fancyname': 'messengerrrrr'}

    # We can either impose our changes ...
    meta_new = edit_meta(meta, name, changes)

    # ... or be careful not to overwrite existing fields
    meta_new2 = edit_meta(meta, name, changes, overwrite=False)

    ts = '2019-11-04 21:43:16.139000'
    # start = pd.to_numeric(pd.to_datetime(df.startTime).astype(int) / 10 ** 9, downcast='unsigned')

    # logs = load(path=os.path.join(DATA_DIR,"log_test_logs.parquet"), index='logs')

    # df = pd.read_parquet(path=os.path.join(DATA_DIR, "glance_small_appevents.parquet"), engine='auto')

    # df2 = load(path=os.path.join(DATA_DIR, "glance_small_appevents.parquet"), index='appevents')
