#!/usr/bin/env python

import pandas as pd


# Generate single log CSV for all suites for a particular task,

def concat_suite_logs(task, suite_status_file, log_dir, out_file):

    # Read suite info
    dt_cols = ['First cycle', 'Start time']
    suite_status = pd.read_csv(suite_status_file, index_col='Suite id', parse_dates=dt_cols)
    suites = suite_status.index

    # Read logs for all suites 
    logs = read_logs(log_dir, suites, task)

    # Write out as single file
    logs.to_csv(out_file)        


# Read log data for a list of suites and return as single dataframe 

def read_logs(log_dir, suites, task): 

    dt_cols = ['Cycle', 'Submit time', 'Init time', 'Exit time']
    types = {'Batch id' : str}

    logs_list = []
    for suite in suites: 
        
        logfile = '{}/{}/{}_cylc.csv'.format(log_dir, suite, task)
        logs = pd.read_csv(logfile, index_col='Batch id', 
                           dtype=types, parse_dates=dt_cols)        
        logs['Suite id'] = suite
        logs_list.append(logs) 

    logs_df = pd.concat(logs_list, axis=0)
    return logs_df


if __name__=="__main__":

    import os

    tasks = os.environ["TASKS"]
    suite_status_file = os.environ["SUITE_STATUS"]
    data_dir = os.environ["DATA_DIR"]
    proc_dir = data_dir+'/processed'

    print("Tasks: ", tasks)
    print("Suite status: ", suite_status_file)
    print("Data dir: ", proc_dir)

    for task in tasks.split():

        out_file = '{}/{}_jobs.csv'.format(data_dir,task)
        concat_suite_logs(task, suite_status_file, proc_dir, out_file) 
                      

    
