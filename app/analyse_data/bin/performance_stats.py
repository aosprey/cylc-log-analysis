#!/usr/bin/env python

import os
import pandas as pd
from datetime import datetime
from cylc_performance import *

# To Do: Reorganise this code. Calcs could go in CoupledData class

def generate_stats(data_dir='.', perf_file='./suite_perf.csv'):
    """Generate performance data for suites: 
    - Run progress
    - SYPD 
    - ASYPD
    """
    # Load data 
    suite_status = SuiteStatus(data_dir+'/suite_status.csv')     
    coupled = CoupledData(data_dir+'/coupled_jobs.csv', suite_status)
    coupled.reset_errors() 
    
    # Drop un-completed entries
    coupled.data.drop(coupled.data[coupled.data['Exit status']!='SUCCEEDED'].index, inplace=True)
    
    # SYPD
    data_by_suite = coupled.data.groupby('Suite id')
    suite_status.data['Mean elapsed time (s)'] = data_by_suite['Elapsed time (s)'].mean()
    suite_status.data['SYPD'] = 86400 / (suite_status.data['Mean elapsed time (s)'] * 360 
                                         / suite_status.data['Cycle length (days)'])

    # Run progress 
    suite_status.data['Target run length (years)'] = (suite_status.data['Cycle length (days)'] * 
                                                      suite_status.data['Run length (cycles)']) / 360

    # Maybe need to use cftime to work out 360 day calendar ? 
    suite_status.data['Last completed cycle'] = data_by_suite.last()['Cycle']
    years = suite_status.data['Last completed cycle'].dt.year - suite_status.data['First cycle'].dt.year
    months = suite_status.data['Last completed cycle'].dt.month-1 + suite_status.data['Cycle length (days)']/30
    suite_status.data['Run progress (years)'] = years + months/12
    
    # ASYPD 
    suite_status.data['End time'] = data_by_suite.last()['Exit time']
    suite_status.data['Run time (days)'] = (suite_status.data['End time'] - suite_status.data['Start time']).dt.total_seconds() / 86400
    suite_status.data['ASYPD'] = suite_status.data['Run progress (years)'] / suite_status.data['Run time (days)']

    # Write out
    write_cols = ['User','Description','Production','Status',
                  'Target run length (years)', 'Run progress (years)',
                  'SYPD','ASYPD']
    round_cols = ['SYPD','ASYPD']
    suite_status.data[round_cols] = suite_status.data[round_cols].round(decimals=2)
    suite_status.data.to_csv(perf_file, columns=write_cols)
    
if __name__=='__main__':
    data_dir = os.environ.get('DATA_DIR', '/gws/nopw/j04/canari/users/aosprey/log-analysis/data')
    stats_dir = os.environ.get('STATS_DIR', '.') 
    generate_stats(data_dir, stats_dir+'/suite_perf.csv')
