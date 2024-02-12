#!/usr/bin/env python

import os
from cylc_performance import * 

def generate_plots(data_dir='.', plot_dir='.'):
    """Generate performance plots for coupled jobs: 
    - Run time
    - SYPD
    - Queue time 
    """
    # Load data 
    suite_status = SuiteStatus(data_dir+'/suite_status.csv')     
    coupled = CoupledData(data_dir+'/coupled_jobs.csv', suite_status)

    # Derive columns for plotting
    coupled.calc_metrics()

    # Plots 
    setup_plots()
    coupled.plot_runtime(
        plot_file=plot_dir+'/coupled_runtime_mean.png', 
        title='EPOC run times for successful coupled tasks', 
	mean=True, 
	hlines=[3,4,5,6,7]) 
    coupled.plot_runtime(
        plot_file=plot_dir+'/coupled_runtime_status.png', 
        title='EPOC run times for coupled tasks', 
	status=True,
	hlines=[1,3,5,7]) 			 	    	    
    coupled.plot_sypd(
        plot_file=plot_dir+'/coupled_sypd.png', 
        title='EPOC SYPD for successful coupled tasks', 
        mean=True, 
	hlines=[0.3,0.4,0.5,0.6])
    coupled.plot_queue_time(
        plot_file=plot_dir+'/coupled_queue_time.png', 
        title='EPOC coupled task queue times', 
	mean=True,
	hlines=[10,20,30,40])
    coupled.plot_status(
        plot_file=plot_dir+'/coupled_status.png', 
        title='EPOC coupled tasks statuses each day', 
        mean=True, 
	hlines=[5,10,15],
	y_ticks=np.arange(2,20,2))
    
if __name__=='__main__': 
    data_dir = os.environ.get('DATA_DIR', '/gws/nopw/j04/epoc/aosprey/log-analysis/data')
    plot_dir = os.environ.get('PLOT_DIR', '.')
    generate_plots(data_dir=data_dir, plot_dir=plot_dir)
