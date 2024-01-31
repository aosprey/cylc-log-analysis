#!/usr/bin/env python

import os
from cylc_performance import * 

def generate_plots(data_dir='.', plot_dir='.'): 
    """Generate performance plots for pptransfer jobs: 
    - Task statuses 
    - Transfer task speed
    """
    # Load data 
    suite_status = SuiteStatus(data_dir+'/suite_status.csv')     
    pptransfer = PPTransferData(data_dir+'/pptransfer_jobs.csv', suite_status) 

    # Calculate metrics 
    pptransfer.calc_metrics()

    # Plots 
    setup_plots()
    pptransfer.plot_status(plot_dir+'/pptransfer_status.png', mean=True, hlines=[50,100,150,200])
    pptransfer.plot_speed(plot_dir+'/pptransfer_speed.png', mean=True, hlines=[50,100,150,200])

if __name__=="__main__": 
    data_dir = os.environ.get('DATA_DIR', '/gws/nopw/j04/canari/users/aosprey/log-analysis/data')
    plot_dir = os.environ.get('PLOT_DIR', '.') 
    generate_plots(data_dir, plot_dir)
