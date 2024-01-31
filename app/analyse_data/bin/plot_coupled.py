#!/usr/bin/env python

import os
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
    coupled.plot_runtime(plot_dir+'/coupled_runtime_all.png', suites_3m, '2023-03-01', 2)
    coupled.plot_runtime(plot_dir+'/coupled_runtime_from_Oct.png', suites_3m, '2023-10-01', 3)
    coupled.plot_runtime(plot_dir+'/coupled_runtime_xios_logs.png', suites_3m, '2023-10-01', 3, xios_logs=True)
    coupled.plot_status(plot_dir+'/coupled_status.png', suites_3m, mean=True, hlines=[20,40,60,80])
    coupled.plot_sypd(plot_dir+'/coupled_sypd.png', suites_3m, mean=True, hlines=[0.8,1.2,1.6,2.0,2.4])
    coupled.plot_queue_time(plot_dir+'/coupled_queue_time.png', suites_3m, mean=True, hlines=[10,20,30])
     
if __name__=='__main__': 
    data_dir = os.environ.get('DATA_DIR', '/gws/nopw/j04/canari/users/aosprey/log-analysis/data')
    plot_dir = os.environ.get('PLOT_DIR', '.')
    generate_plots(data_dir=data_dir, plot_dir=plot_dir)
