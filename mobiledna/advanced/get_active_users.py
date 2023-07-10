# -*- coding: utf-8 -*-

"""
    __  ___      __    _ __     ____  _   _____
   /  |/  /___  / /_  (_) /__  / __ \/ | / /   |
  / /|_/ / __ \/ __ \/ / / _ \/ / / /  |/ / /| |
 / /  / / /_/ / /_/ / / /  __/ /_/ / /|  / ___ |
/_/  /_/\____/_.___/_/_/\___/_____/_/ |_/_/  |_|

Functions that return id's that meet some criteria (e.g. active users of an app, users that have churned from an app)
-- Coded by Simon Perneel
-- mailto:Simon.Perneel@UGent.be
"""

import pandas as pd
from mobiledna.core.help import log

def get_active_users(apps: pd.DataFrame, application='com.facebook.orca', time_unit='daily'):
    """
    Get active users of an application - daily, weekly, monthly
    :param apps: Appevents object
    :param time_unit: time unit to aggregate the data on
    :return: DataFrame with bool users
    """
    # Filter to application appevents
    apps = apps.query('application == @application')
    # todo

def get_churners(ae_df=pd.DataFrame, application=str) -> pd.DataFrame:
    """
    Get users that have churned from an application. If a user has not used the application for more days than he/she has used it,,
    the user is considered to have churned from the app.
    :param ae_df: dataframe with appevents
    :param application: application codename to check for churners
    :return: DataFrame with id's of users that have churned from the application and the last date they used the app
    """
    # Get start and end logdate
    logdates = ae_df.groupby('id')['startDate'].agg(['min', 'max'])\
                    .rename(columns={'min': 'start_logging', 'max': 'end_logging'})

    # Filter to application appevents
    ae_app = ae_df.query('application == @application')
    logdates_app = ae_app.groupby('id')['startDate'].agg(['min', 'max'])\
                         .rename(columns={'min': 'start_app', 'max': 'end_app'})

    logdates = logdates.merge(logdates_app, on='id', how='right')  # Right merge to keep only app users
    logdates['days_used'] = (logdates['end_app'] - logdates['start_app']).dt.days
    logdates['days_not_used'] = (logdates['end_logging'] - logdates['end_app']).dt.days
    logdates['churned'] = logdates.apply(lambda row: True if row['days_not_used'] > row['days_used'] else False, axis=1)
    log(f'{logdates.churned.sum()} out of {len(logdates)} users churned from "{application}"')

    logdates = logdates.drop(columns=['start_logging', 'end_logging', 'start_app'])\
                       .rename(columns={'end_app': 'last_use'})

    return logdates.query('churned == True')




