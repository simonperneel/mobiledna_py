#           _                  _      _                 ___
#   __ __ _| |_  ___ _ _ ___  (_)___ | |_  ___ _ __  __|__ \
#   \ V  V / ' \/ -_) '_/ -_) | (_-< | ' \/ _ \ '  \/ -_)/_/
#    \_/\_/|_||_\___|_| \___| |_/__/ |_||_\___/_|_|_\___(_)
#

'''
Coded by: Wouter Durnez (wouter.durnez@ugent.be)
Updated and maintained by: Simon Perneel (simon.perneel@ugent.be)
'''

import datetime
from os.path import join

import geopy.distance
import matplotlib.pyplot as plt
import mobiledna.core.help as hlp
import numpy as np
import pandas as pd
import seaborn as sns

from mobiledna.core.help import log
from mobiledna.core.appevents import Appevents
from scipy.spatial.distance import cdist, euclidean
from tqdm import tqdm

from datetime import datetime, timedelta, time
import random as rnd
from matplotlib import pyplot as plt

tqdm.pandas()


def is_consecutive(df: pd.DataFrame, col='startDate', shut_up=False) -> bool:
    """
    Check if all days contain data between first and last.
    WARNING: does this over the whole data frame, ignoring ids. Use in combination with groupby.

    :param df: input data frame
    :param col: column on which we'll perform the check
    :param shut_up: set to true to suppress info
    :return: result of check
    """

    # ids can get stuck in the index, without there actually being data attached to them
    # We'll make sure the function doesn't trip up later by dealing with them first
    if df.empty:
        return False

    # All dates occurring in data frame
    df_days = df[col].unique()

    # Earliest and latest date, and their difference
    first, last = min(df_days), max(df_days)
    delta = (last - first).days

    # Go over all days in between and make sure there's data for it
    for d in range(delta + 1):

        day = first + timedelta(days=d)

        # If the present day is not in the list of unique dates,
        # our check failed, and we can abort
        if day not in df_days:
            if not shut_up:
                print(f"Nothing logged on {day}! Got to {d} days before check failed.")
            return False

    # If it hasn't failed by the end of the loop, we're good
    if not shut_up:
        print(f"We got a good one! Logged for {delta} days")
    return True


def geometric_median(coordinates: np.ndarray, eps=1e-7):
    """
    Calculate geometric median of 2D-arrays
    Taken from: https://stackoverflow.com/questions/30299267/geometric-median-of-multidimensional-points
    See also: http://www.pnas.org/content/97/4/1423.full.pdf

    :param X: coordinate array ~ np.ndarray(shape=(N,2)
    :param eps: tolerance
    :return: coordinates for median
    """

    # Start with mean location as first guess for median
    y = np.mean(coordinates, 0)

    # Iterate until criterion is met
    while True:

        # Calculate distances between mean location and locations
        D = cdist(coordinates, [y])

        # Get nonzero distances
        nonzeros = (D != 0)[:, 0]

        # Invert and normalize them (weights)
        Dinv = 1 / D[nonzeros]
        Dinvs = np.sum(Dinv)
        W = Dinv / Dinvs
        T = np.sum(W * coordinates[nonzeros], 0)

        # Get number of zeros;
        # if none are zero, return weighted sum of nonzero coordinates;
        # if they're all zero, return the current mean;
        # else, proceed with algorithm
        num_zeros = len(coordinates) - np.sum(nonzeros)
        if num_zeros == 0:
            y1 = T
        elif num_zeros == len(coordinates):
            return y
        else:
            R = (T - y) * Dinvs
            r = np.linalg.norm(R)
            rinv = 0 if r == 0 else num_zeros / r
            y1 = max(0, 1 - rinv) * T + min(1, rinv) * y

        # Convergence tolerance: abort if we meet the criterion
        if euclidean(y, y1) < eps:
            return y1

        # Update new median
        y = y1


def calculate_distance(latX: float, lonX: float, latY: float, lonY: float):
    """
    Calculate distance between a pair of decimal coordinates (X and Y)
    :param latX: point X latitude
    :param lonX: point X longitude
    :param latY: point Y latitude
    :param lonY: point Y longitude
    :return: distance in meters
    """
    if (((latX == 0) & (lonX == 0)) |
            ((latY == 0) & (lonY == 0))):
        return np.nan

    if any(np.isnan([latY, latX, lonX, lonY])):
        return np.nan

    return geopy.distance.distance((latX, lonX), (latY, lonY)).m


def where_is_home(appevents: pd.DataFrame,
                  home_time_range=(time(23, 30, 0), time(4, 30, 0)),
                  plot=True,
                  shut_up=False) -> np.ndarray:
    """
    Get an estimate for the home location, by calculating the geometric median
    of appevent locations between a certain time range.

    :param appevents: data frame of mobiledna appevents
    :param home_time_range: time range where we expect people to be home
    :return:
    """

    # First, check if there are any coordinates in there (so drop the (0,0)s)
    no_data = appevents[(appevents.latitude != 0) | (appevents.longitude != 0)].empty
    if no_data:
        if not shut_up:
            log(f"User {appevents.id.iloc[0]} probably didn't allow location tracking.")
        return np.array([np.nan, np.nan])

    # Add dates from timestamp
    appevents.startTime = appevents.startTime.astype("datetime64[s]")
    appevents.endTime = appevents.endTime.astype("datetime64[s]")

    appevents['startToD'] = appevents.startTime.dt.time
    appevents['endToD'] = appevents.endTime.dt.time

    # Drop columns we don't care about right now, and reorder
    appevents = appevents[['id', 'startTime', 'endTime', 'startToD', 'endToD', 'latitude', 'longitude']]
    appevents = appevents.loc[(appevents.latitude != 0) & (appevents.longitude != 0)].copy()

    # Plot all events
    if plot:
        # Set colors
        colors = sns.color_palette('pastel')

        # Plot points
        ax = sns.scatterplot(x='longitude', y='latitude', color='gainsboro', data=appevents, alpha=.003)

    # Restrict appevents to 'home time'
    home_apps = appevents.loc[(appevents.startTime.dt.time > home_time_range[0]) |
                              (appevents.startTime.dt.time < home_time_range[1])]
    if not shut_up:
        log(f'Original appevent count {len(appevents)} - filtered count {len(home_apps)}')

    # Get latitudes and longitudes as ndarray
    x = home_apps.longitude.values
    y = home_apps.latitude.values

    # Plot points using seaborn (because we love it so much)
    if plot:
        sns.scatterplot(x='longitude', y='latitude', color='orange', data=home_apps, alpha=.01, ax=ax)
        # plt.plot(x,y, 'bo', alpha=.005)

    # Get geometric median
    xy = np.ndarray(shape=(len(x), 2))
    xy[:, 0] = x
    xy[:, 1] = y
    home = geometric_median(xy)

    # ... and plot it
    if plot:
        plt.plot(home[0], home[1], 'ro')
        plt.title(f"Guessed home for {appevents.id.iloc[0]}")

    # Add a circle around home
    radius = 0.0002
    home_zone = plt.Circle((home[0], home[1]), radius=radius, fill=False, color='c')
    if plot:
        ax.add_artist(home_zone)
        plt.show()

    return home


def add_home_distance(row) -> float:
    distance = calculate_distance(latX=row['latitude'],
                                  lonX=row['longitude'],
                                  latY=row['home_latitude'],
                                  lonY=row['home_longitude'])

    return distance

def is_home(row) -> str:
    if row.distance_to_home < 100:
        return 'home'
    if 100 < row.distance_to_home < 1000:
        return 'grey_zone'
    else:
        return 'out_of_home'


if __name__ == '__main__':

    # Sup
    hlp.hi()

    # Load data
    apps = Appevents.load_data('/Users/simonperneel/Library/CloudStorage/OneDrive-UGent/Imec-mict-Onedrive/mobileDNA-data-exports/mdecline/291121/mdecline_appevents.parquet').get_data()
    apps['startDate'] = apps.startTime.dt.date

    log('Getting good ids...')
    # Check number of logged days
    day_counts = apps.groupby(['id']).startDate.nunique()

    # Logged enough?
    logged_enough = set(day_counts[day_counts > 7].index)

    # Check if you logged consecutively
    #consecutive_check = apps.groupby(['id']).apply(is_consecutive)
    #logged_consecutively = set(consecutive_check[consecutive_check].index)

    # Get people who did both
    good_ids = list(logged_enough)
    #good_ids = good_ids[0:10]

    apps = apps.loc[apps.id.isin(good_ids)]

    # Find some homes
    log('Getting home coordinates...')
    apps['home_latitude'] = np.nan
    apps['home_longitude'] = np.nan
    homes = {}
    for id in tqdm(list(good_ids)):
        try:
            homes[id] = where_is_home(appevents=apps.loc[apps.id == id], plot=False, shut_up=True)
        except Exception as e:
            homes[id] = [np.nan, np.nan]
            print(f'Failed for {id}: {e}')

    log('Adding latitude column...')
    apps['home_latitude'] = apps.progress_apply(lambda row: homes[row['id']][1], axis=1)
    log('Adding longitude column...')
    apps['home_longitude'] = apps.progress_apply(lambda row: homes[row['id']][0], axis=1)

    # Add a column to the data that reflects distance to home
    log('Adding distance column...')
    apps['distance_to_home'] = apps.progress_apply(lambda row: add_home_distance(row), axis=1)
    apps['home'] = apps.progress_apply(lambda row: is_home(row), axis=1)

    # Get median distance
    #median_distance_from_home = apps.groupby(['id','week']).distance_to_home.median()
    #median_distance_from_home = median_distance_from_home.reset_index()
    #median_distance_from_home.to_csv("/Users/wouter/Documents/OneDrive - UGent/02_Projects/000_Internal/"
     #                                "001_MobileDNA/mobiledna_py/data/corona/median_distance_from_home.csv")

    # Get median distance
    #std_distance_from_home = apps.groupby(['id', 'week']).distance_to_home.std()
    #std_distance_from_home = std_distance_from_home.reset_index()
    #std_distance_from_home.to_csv("/Users/wouter/Documents/OneDrive - UGent/02_Projects/000_Internal/"
     #                                "001_MobileDNA/mobiledna_py/data/corona/std_distance_from_home.csv")

    #sns.lineplot(x='week', y='distance_to_home', data=std_distance_from_home)
    #sns.lineplot(x='week', y='distance_to_home', data=median_distance_from_home)
    #plt.legend(['standard deviation','median'])
    #plt.ylabel('Meters from home')
    #plt.xlim(0,11)
    #plt.show()

    print(apps.head())

