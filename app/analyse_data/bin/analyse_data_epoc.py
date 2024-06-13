#!/usr/bin/env python

from datetime import datetime
import numpy as np
import os
from cylc_performance import *

def coupled_data(data_dir='.', plot_dir='.'):
    """Generate performance plots and suite stats for coupled jobs"""
    # Load data 
    suite_status = SuiteStatus(data_dir+'/suite_status.csv')     
    coupled = CoupledData(data_dir+'/coupled_jobs.csv', suite_status)

    # Performance stats
    coupled.set_filesystem() 
    coupled.set_xios_logs()
    coupled.calc_metrics()
    coupled.write(data_dir+'/coupled_jobs_plus.csv')
    coupled.calc_suite_stats()

    # Overwrite NVMe plot labels
    labels['nvme'] = 'NVMe + extra diags'
    labels['nvme_succ'] = 'Succeeded NVMe + extra diags'
    labels['nvme_fail'] = 'Failed NVMe + extra diags'

    # Plots 
    image_dir = plot_dir+'/IMAGES'
    coupled.plot_queue_time(
        plot_file=image_dir+'/coupled_queue_time.png', 
        title='Job queue times: HH runs on ARCHER2', 
	mean=True,
	hlines=np.arange(10,50,10))
    coupled.plot_runtime_filesystem(
        plot_file=image_dir+'/coupled_runtime.png', 
        title='Run times per model month: HH runs on ARCHER2', 
	hlines=np.arange(2,9,2),
        status=True, 
        xios_logs=True) 
    coupled.plot_sypd_filesystem(
        plot_file=image_dir+'/coupled_SYPD.png', 
        title='SYPD per model month: HH runs on ARCHER2', 
	hlines=np.arange(0.1,0.8,0.1),
        mean=True, 
        xios_logs=True) 
    coupled.plot_daily_status(
        plot_file=image_dir+'/coupled_status.png', 
        title='Model task statuses per day: HH runs on ARCHER2', 
        mean=True, 
	hlines=np.arange(5,25,5),
	y_ticks=np.arange(5,25,5))
    coupled.plot_asypd_sypd_suites(
        plot_file=image_dir+'/asypd_sypd.png', 
	title='Run speed on ARCHER2', 
	hlines=np.arange(0.1,0.8,0.1))
	
    # HTML
    perf_csv = plot_dir+'/DATA/suite_perf.csv'
    perf_html = plot_dir+'/DATA/suite_perf.html'
    plot_format = '<a href="IMAGES/asypd_sypd_{0}.png">{0}</a>'
    coupled.write_suite_stats(perf_csv, perf_html, plot_format)
    update_html('coupled_plots.html', data_dir, plot_dir) 
    update_html('index.html', data_dir, plot_dir, perf_html)
    
def pptransfer_data(data_dir='.', plot_dir='.'): 
    """Generate performance plots for pptransfer jobs."""
    # Load data 
    suite_status = SuiteStatus(data_dir+'/suite_status.csv')     
    pptransfer = PPTransferData(data_dir+'/pptransfer_jobs.csv', suite_status) 

    # Calculate metrics 
    pptransfer.calc_metrics()

    # Plots
    image_dir = plot_dir+'/IMAGES'
    pptransfer.plot_daily_status(
        plot_file=image_dir+'/pptransfer_status.png', 
        title='EPOC transfer task statuses each day', 
	mean=True, 
	hlines=[5,10,15,20],
	y_ticks=np.arange(5,30,5))
    pptransfer.plot_speed(
        plot_file=image_dir+'/pptransfer_speed.png', 
	title='EPOC speed of successful transfer tasks', 
	mean=True, 
        hlines=[50,100,150,200])
    update_html('pptransfer_plots.html', data_dir, plot_dir) 

def update_html(template_file, data_dir='.', plot_dir='.', perf_file=None): 
    """
    Generate html wrapper for plots and perf stats based on template file. 
    """
    f = open(template_file, 'r')
    contents = f.read()
    f.close()

    now = datetime.now() 
    now_str = now.strftime('%Y-%m-%d %H:%M:%S')
    contents = contents.replace('XX_DATE_XX', now_str) 
    
    if perf_file is not None: 
        f = open(perf_file, 'r')
        table = f.read()
        f.close()
        contents = contents.replace('XX_TABLE_XX', table) 

    out_file = plot_dir+'/'+template_file
    f = open(out_file, 'w') 
    f.write(contents) 
    f.close()
 
if __name__=='__main__': 
    data_dir = os.environ.get('DATA_DIR', '/gws/nopw/j04/epoc/aosprey/log-analysis/data')
    plot_dir = os.environ.get('PLOT_DIR', '.')

    coupled_data(data_dir=data_dir, plot_dir=plot_dir)
    pptransfer_data(data_dir=data_dir, plot_dir=plot_dir)
