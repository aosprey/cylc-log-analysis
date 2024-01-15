#!/usr/bin/env python

# Plot run times for successful and failed coupled tasks

import os
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from pandas.tseries.offsets import DateOffset
from performance_stats import * 


# Add file system column to logs
# A suite may have started on Disk and switched to NVMe 

def set_filesystem(logs, suite_status): 

    logs['File system'] = 'Disk' 

    nvme_suites = suite_status[suite_status['File system'] == 'NVMe'].index    
    for nvme_suite in nvme_suites: 

        first_cycle = suite_status.loc[nvme_suite, 'First NVMe cycle']
        logs.loc[(logs['Suite id'] == nvme_suite) & 
                 (logs['Cycle'] >= first_cycle), 'File system'] = 'NVMe'

    return logs


# Work out if job run with XIOS logs on or off 

def set_xios_logs(logs, suite_status): 

    logs['XIOS logs'] = True

    logs_off_suites = suite_status[~suite_status['XIOS logs']].index 
    for suite in logs_off_suites: 
    
        first_cycle = suite_status.loc[suite, 'First no log cycle']
        logs.loc[(logs['Suite id'] == suite) & 
                 (logs['Cycle'] >= first_cycle), 'XIOS logs'] = False

    return logs
        


# Calc metrics for plotting

def calc_metrics(logs): 

    logs['Queued time (h)'] = logs['Queued time (s)'] / 3600.0
    logs['Elapsed time (h)'] = logs['Elapsed time (s)'] / 3600.0
    logs['SYPD'] = 86400.0 / (logs['Elapsed time (s)']*4)

    # If runtime less than 2h make sure set as failed
    logs.loc[logs['Elapsed time (h)'] < 2,'Exit status'] = 'EXIT'

    return logs


# Write logs as CSV

def write_logs(logs, out_file): 

    write_cols = ['Cycle','Rep','Submit time','Init time','Exit time','Exit status','Queued time (s)','Elapsed time (s)','Suite id','File system','XIOS logs']
    logs.to_csv(out_file, columns=write_cols) 


# Global plot settings

def setup_plots():
    
    plt.rcParams['font.size'] = '12'
    plt.rcParams['figure.figsize'] = (12,6)


# Plot runtime for succeeded and failed tasks as scatter plot 
# Plot Disk only

def plot_runtime(logs, plot_file):

    fig, ax = plt.subplots()

    data = logs[(logs['File system'] == 'Disk') & 
                 (logs['Exit status'] == 'SUCCEEDED')]
    data.plot(ax=ax, x='Init time', y='Elapsed time (h)', style='o', ms=2, color='lawngreen')
    
    data = logs[(logs['File system'] == 'Disk') & 
                 (logs['Exit status'] == 'EXIT')]
    data.plot(ax=ax, x='Init time', y='Elapsed time (h)', style='o', ms=2, color='green')

    ax.legend(['Succeeded','Failed'], loc=2)
    ax.set_xlabel('Start time')
    ax.set_ylabel('Time to completion (h)')
    title = 'CANARI coupled task run times (exc NVMe)'
    ax.set_title(title)

    plt.savefig(plot_file)


# Plot runtime for succeeded and failed tasks as scatter plot
# Group by file system. 
# Only plot jobs submitted since a specified date 

def plot_runtime_filesystem(logs, date_string, ms, plot_file):
 
    fig, ax = plt.subplots()

    # Plot data
    
    ref_date = pd.Timestamp(date_string, tz='UTC')
    work_data = logs[(logs['File system'] == 'Disk') & 
                       (logs['Submit time'] > ref_date)]

    work_data[work_data['Exit status']=='SUCCEEDED'].plot(
        ax=ax, x='Init time', y='Elapsed time (h)', style='o', ms=ms, color='lawngreen')
    work_data[work_data['Exit status']=='EXIT'].plot(
        ax=ax, x='Init time', y='Elapsed time (h)', style='x', mew=1.5, ms=ms, color='green')
    
    # Plot NVMe
    
    nvme_data = logs[(logs['File system'] == 'NVMe') & 
                     (logs['Submit time'] > ref_date)]

    nvme_data[nvme_data['Exit status']=='SUCCEEDED'].plot(
        ax=ax, x='Init time', y='Elapsed time (h)', style='o', ms=ms, color='magenta')
    nvme_data[nvme_data['Exit status']=='EXIT'].plot(
        ax=ax, x='Init time', y='Elapsed time (h)', style='+', mew=1.5, ms=ms+1, color='purple')

    # Annotate plot
    
    box = ax.get_position()
    ax.set_position([box.x0, box.y0, box.width, box.height * 0.9])
    plt.legend(['Succeeded Disk', 'Failed Disk', 'Succeeded NVMe', 'Failed NVMe'],
               markerscale=1.5, ncol=4, 
               bbox_to_anchor=(0, 1.01, 1, 0.1), loc="lower left")
    ax.set_xlabel('Start time')
    ax.set_ylabel('Time to completion (h)')
    title='CANARI coupled task run times since {}'.format(date_string)
    plt.title(title, y=1.15) 

    plt.savefig(plot_file)

    
# Plot runtime for succeeded and failed tasks as scatter plot
# Group by file system, and whether XIOS logs off 
# Only plot jobs submitted since a specified date 

def plot_runtime_xios_logs(logs, date_string, ms, plot_file):
 
    fig, ax = plt.subplots()

    # Plot baseline: (spinning disk) work
    
    ref_date = pd.Timestamp(date_string, tz='UTC')
    work_data = logs[(logs['File system'] == 'Disk') & (logs['Submit time'] > ref_date)]

    work_data[work_data['Exit status']=='SUCCEEDED'].plot(
        ax=ax, x='Init time', y='Elapsed time (h)', style='o', ms=ms, color='lawngreen')
    work_data[work_data['Exit status']=='EXIT'].plot(
        ax=ax, x='Init time', y='Elapsed time (h)', style='x', mew=1.5, ms=ms, color='green')
    
    # Plot NVMe
    
    nvme_data = logs[(logs['File system'] == 'NVMe') & (logs['Submit time'] > ref_date)]

    nvme_data[nvme_data['Exit status']=='SUCCEEDED'].plot(
        ax=ax, x='Init time', y='Elapsed time (h)', style='o', ms=ms, color='magenta')
    nvme_data[nvme_data['Exit status']=='EXIT'].plot(
        ax=ax, x='Init time', y='Elapsed time (h)', style='+', mew=1.5, ms=ms+1, color='purple')


    # Plot XIOS logs off

    logs_off_data = logs[~(logs['XIOS logs']) & (logs['Submit time'] > ref_date)]
    
    logs_off_data[work_data['Exit status']=='SUCCEEDED'].plot(
        ax=ax, x='Init time', y='Elapsed time (h)', style='o', ms=ms, color='gold')
    logs_off_data[work_data['Exit status']=='EXIT'].plot(
        ax=ax, x='Init time', y='Elapsed time (h)', style='x', mew=1.5, ms=ms, color='tomato')
     
    # Annotate plot
    
    box = ax.get_position()
    ax.set_position([box.x0, box.y0, box.width, box.height * 0.85])
    plt.legend(['Succeeded Disk', 'Failed Disk', 
                'Succeeded NVMe', 'Failed NVMe', 
                'Succeeded XIOS logs off', 'Failed XIOS logs off'],
               markerscale=1.5, ncol=3, 
               bbox_to_anchor=(0.1, 1.01, 1, 0.1), loc="lower left")
    ax.set_xlabel('Start time')
    ax.set_ylabel('Time to completion (h)')
    title='CANARI coupled task run times since {}'.format(date_string)
    plt.title(title, y=1.25) 

    plt.savefig(plot_file)


# Plot SYPD for successful tasks 
# Only plot Disk

def plot_sypd(logs, plot_file):
    
    data = logs[(logs['File system'] == 'Disk') & 
                (logs['Exit status']=='SUCCEEDED')]
    
    ax = data.plot(x='Init time', y='SYPD', style='o', ms=2, legend=False, color='lawngreen')
    ax.set_xlabel('Start time')
    ax.set_ylabel('SYPD')
    ax.set_title('CANARI SYPD for successful coupled tasks (exc NVMe)')

    plt.savefig(plot_file)


# Plot SYPD for successful tasks 
# Also plot mean SYPD for each day grouped by init time.

def plot_sypd_mean(logs, plot_file):
   
    fig, ax = plt.subplots()

    plt.axhline(y=2.4, color='black', linewidth=0.5, label='_')
    plt.axhline(y=2.0, color='black', linewidth=0.5, label='_')
    plt.axhline(y=1.6, color='black', linewidth=0.5, label='_')
    plt.axhline(y=1.2, color='black', linewidth=0.5, label='_')
    plt.axhline(y=0.8, color='black', linewidth=0.5, label='_')
 
    # Plot SYPD
    
    data = logs[logs['Exit status'] == 'SUCCEEDED']
    data.plot(ax=ax, x='Init time', y='SYPD', label='SYPD per job',
              style='o', ms=2, color='deepskyblue')

    # Daily mean

    mean_sypd_by_date = data.groupby(data['Init time'].dt.date)['SYPD'].mean()
    dates = pd.date_range(mean_sypd_by_date.index[0], mean_sypd_by_date.index[-1])
    mean_sypd_by_date = mean_sypd_by_date.reindex(dates, fill_value=pd.NA) 
    mean_sypd_by_date.index = mean_sypd_by_date.index.tz_localize('UTC')
    mean_sypd_by_date.index = mean_sypd_by_date.index + DateOffset(hours=12)
    #mean_sypd_by_date.plot(ax=ax, color='black')

    rolling_mean = mean_sypd_by_date.rolling(7, min_periods=3, center=True).mean()
    rolling_mean.plot(ax=ax, x='Init time', y='SYPD', color='navy',
                      label='Rolling 7 day mean')
   
    # Annotate plot 
    
    box = ax.get_position()
    ax.set_position([box.x0, box.y0, box.width, box.height * 0.9])
    
    plt.legend(markerscale=1.2, bbox_to_anchor=(0, 1.01, 1, 0.1), loc="lower left", ncol=2)
    ax.set_xlabel('Start time')
    ax.set_ylabel('SYPD')
    ax.set_yticks(np.arange(0.6,2.6,0.2))
    plt.title('CANARI SYPD for successful coupled tasks', y=1.15)

    plt.savefig(plot_file)


# Plot successes and failures for each date

def plot_status(logs, plot_file): 

    status_by_date = logs.groupby(logs['Init time'].dt.date)['Exit status'].value_counts()

    # Reindex and fill with 0 for dates with no data
    dates = pd.date_range(status_by_date.index.get_level_values(0)[0], status_by_date.index.get_level_values(0)[-1])
    new_index = pd.MultiIndex.from_product([dates, status_by_date.index.levels[1]], 
                                           names = ["Init time", "Exit status"])
    status_by_date = status_by_date.reindex(new_index, fill_value=0)

    fig, ax = plt.subplots()

    data = status_by_date.xs("SUCCEEDED", level="Exit status")
    data.plot(ax=ax, x='Init time', y='count', color='deepskyblue')

    data = status_by_date.xs("EXIT", level="Exit status")
    data.plot(ax=ax, x='Init time', y='count', color='navy')

    ax.legend(['Succeeded','Failed'])
    ax.set_xlabel('Start date')
    ax.set_ylabel('Number of tasks')
    ax.set_title('CANARI coupled task statuses per day')

    plt.savefig(plot_file)


 # Plot successes and failures for each date

def plot_status_mean(logs, plot_file): 

    status_by_date = logs.groupby(logs['Init time'].dt.date)['Exit status'].value_counts()

    # Reindex and fill with 0 for dates with no data
    dates = pd.date_range(status_by_date.index.get_level_values(0)[0], status_by_date.index.get_level_values(0)[-1])
    new_index = pd.MultiIndex.from_product([dates, status_by_date.index.levels[1]], 
                                           names = ["Init time", "Exit status"])
    status_by_date = status_by_date.reindex(new_index, fill_value=0)

    fig, ax = plt.subplots()
  
    plt.axhline(y=20, color='black', linewidth=0.5, label='_')
    plt.axhline(y=40, color='black', linewidth=0.5, label='_')
    plt.axhline(y=60, color='black', linewidth=0.5, label='_')
    plt.axhline(y=80, color='black', linewidth=0.5, label='_')

    data = status_by_date.xs("SUCCEEDED", level="Exit status")
    data.plot(ax=ax, x='Init time', y='count', color='deepskyblue', label='Succeeded')

    rolling_mean = data.rolling(7, min_periods=1, center=True).mean()
    rolling_mean.plot(ax=ax, x='Init time', y='count', color='navy', label='Succeeded (rolling 7 day mean)')

    data = status_by_date.xs("EXIT", level="Exit status")
    data.plot(ax=ax, x='Init time', y='count', color='red', label='Failed')

    plt.legend()
    #ax.legend(['Succeeded','Succeeded (rolling 7 day mean)', 'Failed'])
    ax.set_xlabel('Start date')
    ax.set_ylabel('Number of tasks')
    ax.set_title('CANARI coupled task statuses each day')

    plt.savefig(plot_file)
   

# Plot queue time for all jobs

def plot_queue_time(logs, plot_file):
        
    ax = logs.plot(x='Submit time', y='Queued time (h)', style='o', ms=2, legend=False, color='deepskyblue')
    
    ax.set_xlabel('Submission time')
    ax.set_ylabel('Queue time (h)')
    ax.set_title('CANARI coupled task queue times')

    plt.savefig(plot_file)


# Plot queue time for all jobs and rolling mean

def plot_queue_time_mean(logs, plot_file):

    fig, ax = plt.subplots()
    
    plt.axhline(y=10, color='black', linewidth=0.5, label='_')
    plt.axhline(y=20, color='black', linewidth=0.5, label='_')
    plt.axhline(y=30, color='black', linewidth=0.5, label='_')

    logs.plot(ax=ax, x='Submit time', y='Queued time (h)', style='o', ms=2,
              color='deepskyblue', label='Queue time per job')
    
    # Daily means

    mean_queue_by_date = logs.groupby(logs['Submit time'].dt.date)['Queued time (h)'].mean()
    dates = pd.date_range(mean_queue_by_date.index[0], mean_queue_by_date.index[-1])
    mean_queue_by_date = mean_queue_by_date.reindex(dates, fill_value=pd.NA) 
    mean_queue_by_date.index = mean_queue_by_date.index.tz_localize('UTC')
    mean_queue_by_date.index = mean_queue_by_date.index + DateOffset(hours=12)
    #mean_queue_by_date.plot(ax=ax, color='black')

    rolling_mean = mean_queue_by_date.rolling(7, min_periods=3, center=True).mean()
    rolling_mean.plot(ax=ax, x='Submit time', y='Queued time (h)', color='navy',
                      label='Rolling 7 day mean')
    
    # Rolling mean

    #data = logs[logs['Init time'].notnull()][['Init time','Queued time (h)']]
    #data = data.sort_values(by="Init time")
    
    #rolling_mean = data.rolling('7D', on="Init time").mean()
    #rolling_mean.plot(ax=ax, x='Init time', y='Queued time (h)', color='black',
    #                  label='Rolling 7 day mean')
    
    # Annotate plot 
    
    box = ax.get_position()
    ax.set_position([box.x0, box.y0, box.width, box.height * 0.9])
    
    plt.legend(markerscale=1.2, bbox_to_anchor=(0, 1.01, 1, 0.1), loc="lower left", ncol=2)
    ax.set_xlabel('Submission time')
    ax.set_ylabel('Queue time (h)')
    ax.set_title('CANARI coupled task queue times', y=1.15)

    plt.savefig(plot_file)


if __name__=="__main__":

    # Env vars
    
    data_dir = os.environ["DATA_DIR"]
    suite_status_file = os.environ["SUITE_STATUS"]
    plot_dir = os.environ["PLOT_DIR"]

    # Read data
    
    suite_status = read_suite_status(suite_status_file)
    suites = suite_status[suite_status['Cycle length (days)'] == 90].index
    
    log_file = data_dir+'/coupled_jobs.csv'
    logs = read_logs(log_file, suites)
    
    # Derive columns
    
    logs = set_filesystem(logs, suite_status) 
    logs = set_xios_logs(logs, suite_status)
    logs = calc_metrics(logs) 

    write_logs(logs,data_dir+'/coupled_jobs_plus.csv') 

    # Run plots
    
    setup_plots()
    plot_runtime_filesystem(logs, '2023-03-01', 2, plot_dir+'/coupled_runtime_all.png')
    plot_runtime_filesystem(logs, '2023-10-01', 3, plot_dir+'/coupled_runtime_from_Oct.png')
    plot_runtime_xios_logs(logs, '2023-10-01', 3, plot_dir+'/coupled_runtime_xios_logs.png')
    plot_sypd_mean(logs, plot_dir+'/coupled_sypd.png')
    plot_status_mean(logs, plot_dir+'/coupled_status.png')
    plot_queue_time_mean(logs, plot_dir+'/coupled_queue_time.png')
