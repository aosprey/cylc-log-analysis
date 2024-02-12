#!/usr/bin/env python

import os
import numpy as np
from cylc_performance import * 

def generate_plots(data_dir='.', plot_dir='.'):
    """Generate performance plots for coupled jobs: 
    - Run time
    - Task status
    - SYPD
    - Queue time 
    """
    # Load data 
    suite_status = SuiteStatus(data_dir+'/suite_status.csv')     
    coupled = CoupledData(data_dir+'/coupled_jobs.csv', suite_status)

    # Derive columns for plotting
    coupled.set_filesystem() 
    coupled.set_xios_logs()
    coupled.reset_errors()
    coupled.calc_metrics()
    
    # Write out data 
    coupled.write('coupled_jobs_plus.csv')

    # Filter
    suites_3m = suite_status.data[suite_status.data['Cycle length (days)'] == 90].index

    # Plots 
    setup_plots()
    
    date_string='2023-03-01'
    coupled.plot_runtime_filesystem(
        plot_file=plot_dir+'/coupled_runtime_all.png', 
        title='CANARI coupled task run times since {}'.format(date_string),
        suites=suites_3m, 
	date_string=date_string, 
	ms=2)
	
    date_string='2023-10-01'
    coupled.plot_runtime_filesystem(
        plot_file=plot_dir+'/coupled_runtime_from_Oct.png',
	title='CANARI coupled task run times since {}'.format(date_string),
        suites=suites_3m, 
	date_string=date_string, 
        ms=3)
    coupled.plot_runtime_filesystem(
        plot_file=plot_dir+'/coupled_runtime_xios_logs.png',
	title='CANARI coupled task run times since {}'.format(date_string),
        suites=suites_3m, 
        date_string=date_string, 
        ms=3, 
        xios_logs=True)
	
    coupled.plot_status(
        plot_file=plot_dir+'/coupled_status.png',
        title='CANARI coupled task statuses each day',
        suites=suites_3m, 
        mean=True, 
        hlines=[20,40,60,80])	
    coupled.plot_sypd(
        plot_file=plot_dir+'/coupled_sypd.png', 
	title='CANARI SYPD for successful coupled tasks',
	suites=suites_3m, 
	mean=True, 
	hlines=[0.8,1.2,1.6,2.0,2.4], 
        y_ticks=np.arange(0.6,2.6,0.2))
    coupled.plot_queue_time(
        plot_file=plot_dir+'/coupled_queue_time.png', 
        title='CANARI coupled task queue times',
        suites=suites_3m, 
        mean=True, 
        hlines=[10,20,30])
     
if __name__=='__main__': 
    data_dir = os.environ.get('DATA_DIR', '/gws/nopw/j04/canari/users/aosprey/log-analysis/data')
    plot_dir = os.environ.get('PLOT_DIR', '.')
    generate_plots(data_dir=data_dir, plot_dir=plot_dir)
