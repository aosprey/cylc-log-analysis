#!/usr/bin/env python

# Work out years run so far, SYPD, ASYPD for each suite

import os
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from datetime import datetime


# Read suite status file
def read_suite_status(suite_status_file):

    dt_cols = ['First cycle', 'Start time']
    suite_status = pd.read_csv(suite_status_file, index_col='Suite id', parse_dates=dt_cols)
    return suite_status


# Read log data
# By default read all suites, or list of suite-ids.
def read_logs(log_file, suites=None):

    # Read logs
    dt_cols = ['Cycle', 'Submit time', 'Init time', 'Exit time']
    types = {'Batch id' : str}
    logs = pd.read_csv(log_file, index_col='Batch id', dtype=types, parse_dates=dt_cols)

    # If defined, filter by suite id
    if suites is not None: 
        logs = logs[logs['Suite id'].isin(suites)]
   
    return logs


# Calculate run progress, SYPD and ASYPD for each suite 
def performance_stats(suite_status, logs, perf_file):

    # Drop un-completed entries
    logs.drop(logs[logs['Exit status']!='SUCCEEDED'].index, inplace=True)
 
    # If runtime less than 2h and 3m cycle make sure set as failed
    suites_3m = suite_status[suite_status['Cycle length (days)'] == 90].index
    logs.loc[(logs['Elapsed time (s)'] < 7200) & (logs['Suite id'].isin(suites_3m)),'Exit status'] = 'EXIT'

    # SYPD
    logs_by_suite = logs.groupby('Suite id')
    suite_status['Mean elapsed time (s)'] = logs_by_suite['Elapsed time (s)'].mean()
    suite_status['SYPD'] = 86400 / (suite_status['Mean elapsed time (s)'] * 360 / suite_status['Cycle length (days)'])

    # Run progress 
    suite_status['Target run length (years)'] = (suite_status['Cycle length (days)'] * suite_status['Run length (cycles)']) / 360

    # Maybe need to use cftime to work out 360 day calendar ? 
    suite_status['Last completed cycle'] = logs_by_suite.last()['Cycle']
    years = suite_status['Last completed cycle'].dt.year - suite_status['First cycle'].dt.year
    months = suite_status['Last completed cycle'].dt.month-1 + suite_status['Cycle length (days)']/30
    suite_status['Run progress (years)'] = years + months/12

    # ASYPD 
    suite_status['End time'] = logs_by_suite.last()['Exit time']
    suite_status['Run time (days)'] = (suite_status['End time'] - suite_status['Start time']).dt.total_seconds() / 86400
    suite_status['ASYPD'] = suite_status['Run progress (years)'] / suite_status['Run time (days)']

    # Write out
    write_cols = ['User','Description','Production','Status',
                  'Target run length (years)', 'Run progress (years)',
                  'SYPD','ASYPD']
    round_cols = ['SYPD','ASYPD']
    suite_status[round_cols] = suite_status[round_cols].round(decimals=2)
    suite_status.to_csv(perf_file, columns=write_cols)

    
if __name__=="__main__":

    # Env vars
    data_dir = os.environ["DATA_DIR"]
    suite_status_file = os.environ["SUITE_STATUS"]
    plot_dir = os.environ["PLOT_DIR"]

    # Read data
    suite_status = read_suite_status(suite_status_file)
    log_file = data_dir+'/coupled_jobs.csv'
    logs = read_logs(log_file)

    # Generate stats
    perf_file = plot_dir + '/../DATA/suite_perf.csv'
    performance_stats(suite_status, logs, perf_file)
 
