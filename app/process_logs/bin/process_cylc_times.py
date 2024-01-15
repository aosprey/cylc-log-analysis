#!/usr/bin/env python

# Process time data from cylc logs.
# These should be in the form of CSV file written by process_logs.sh.

# * Rename columns
# * Calc run time and wait time
# * Remove entires with no slurm id. 

import argparse
import pandas as pd

parser = argparse.ArgumentParser(description='Process time data from cylc logs.')
parser.add_argument('input_file', help='Input file containing data from cylc logs')
parser.add_argument('output_file', help='Output file to store processed data')
args = parser.parse_args()

# Read data
dt_cols = ['CYLC_BATCH_SYS_JOB_SUBMIT_TIME', 'CYLC_JOB_INIT_TIME', 'CYLC_JOB_EXIT_TIME']
types = {'CYLC_BATCH_SYS_JOB_ID' : str}
logs = pd.read_csv(args.input_file, index_col='CYLC_BATCH_SYS_JOB_ID', 
                   dtype=types, parse_dates=dt_cols)

# Rename column names 
rename_cols = {'CYLC_BATCH_SYS_JOB_SUBMIT_TIME' : 'Submit time',
               'CYLC_JOB_INIT_TIME' : 'Init time',
               'CYLC_JOB_EXIT_TIME' : 'Exit time',
               'CYLC_JOB_EXIT' : 'Exit status'}
logs.rename(columns=rename_cols, inplace=True)

index_name = 'Batch id'
logs.index.name = index_name

# Drop null batch ids 
logs = logs[logs.index.notnull()]

# Derive queue time and run time 
logs['Queued time (s)'] = ( logs['Init time']-logs['Submit time'] ).dt.total_seconds()
logs['Elapsed time (s)'] = ( logs['Exit time']-logs['Init time'] ).dt.total_seconds()

# Write data
logs.to_csv(args.output_file)
    

