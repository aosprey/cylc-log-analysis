#!/usr/bin/env python

import pandas as pd
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
    coupled.reset_errors()
    coupled.calc_metrics()
    coupled.write(data_dir+'/coupled_jobs_plus.csv')
    coupled.calc_suite_stats()

    # Filters
    suites_3m = suite_status.data[suite_status.data['Cycle length (days)'] == 90].index
    suites_prod = suite_status.data[suite_status.data['Production']].index
    suites_hist = suite_status.data[suite_status.data['Description'].str.contains('HIST2') &
                                    suite_status.data['Production']].index
    suites_ssp = suite_status.data[suite_status.data['Description'].str.contains('SSP370') &
                                   suite_status.data['Production']].index    

    # Plots 
    image_dir = plot_dir+'/IMAGES'
    ens_label = 'CANARI LE on ARCHER2: '

    coupled.plot_queue_time(
        plot_file=image_dir+'/coupled_queue_time.png', 
        title=ens_label+'Job queue times', 
        suites=suites_3m, 
        mean=True, 
        hlines=np.arange(10,50,10))
    coupled.plot_runtime_filesystem(
        plot_file=image_dir+'/coupled_runtime.png', 
        title=ens_label+'Run times per model month',
        suites=suites_3m,
#	hlines=np.arange(2,10,2),
        status=True, 
        xios_logs=True) 
    coupled.plot_sypd(
        plot_file=image_dir+'/coupled_SYPD.png', 
        title=ens_label+'SYPD per model month',
        suites=suites_3m,
	hlines=np.arange(0.8,2.6,0.4),
        y_ticks=np.arange(0.8,2.6,0.2),
        mean=True) 
    coupled.plot_daily_status(
        plot_file=image_dir+'/coupled_status.png', 
        title=ens_label+'Model task statuses per day',
        suites=suites_3m,
        mean=True, 
	hlines=np.arange(20,110,20))
    coupled.plot_asypd_sypd_suites(
        plot_file=image_dir+'/asypd_sypd.png', 
	title='Run speed on ARCHER2',
        suites=suites_prod)
	
    # HTML
    perf_csv = plot_dir+'/DATA/suite_perf.csv'
    coupled.write_suite_stats(csv_file=perf_csv, suites=suites_prod)
    
    plot_format = '<a href="IMAGES/asypd_sypd_{0}.png">{0}</a>'
    perf_html_hist = plot_dir+'/DATA/suite_perf_hist.html'
    coupled.write_suite_stats(html_file=perf_html_hist, plot_format=plot_format, suites=suites_hist) 
    perf_html_ssp = plot_dir+'/DATA/suite_perf_ssp.html'
    coupled.write_suite_stats(html_file=perf_html_ssp, plot_format=plot_format, suites=suites_ssp) 
    
    timestamp_html('coupled_plots.html', data_dir, plot_dir) 
    total_sy_hist = suite_status.data['Completed years'].loc[suites_hist].sum()
    total_sy_ssp = suite_status.data['Completed years'].loc[suites_ssp].sum()
    populate_html('index.html', data_dir, plot_dir, total_sy_hist, total_sy_ssp, perf_html_hist, perf_html_ssp)
    
def pptransfer_data(data_dir='.', plot_dir='.'): 
    """Generate performance plots for pptransfer jobs."""
    # Load data 
    suite_status = SuiteStatus(data_dir+'/suite_status.csv')     
    pptransfer = PPTransferData(data_dir+'/pptransfer_jobs.csv', suite_status) 

    # Calculate metrics 
    pptransfer.calc_metrics()

    # Plots
    image_dir = plot_dir+'/IMAGES'
    ens_label = 'CANARI LE on ARCHER2: '
    pptransfer.plot_daily_status(
        plot_file=image_dir+'/pptransfer_status.png', 
        title=ens_label+'Transfer task statuses per day', 
	mean=True, 
	hlines=[50,100,150,200],
	y_ticks=np.arange(5,30,5))
    pptransfer.plot_speed(
        plot_file=image_dir+'/pptransfer_speed.png', 
	title=ens_label+'Transfer task speed',
	mean=True, 
        hlines=[50,100,150,200])
    timestamp_html('pptransfer_plots.html', data_dir, plot_dir) 
    
def timestamp_html(template_file, data_dir, plot_dir): 
    """Add timesamp to html template file."""
    contents = read_file(template_file) 
    now = pd.Timestamp.now()
    now_str = now.strftime('%Y-%m-%d %H:%M:%S')
    contents = contents.replace('XX_DATE_XX', now_str) 
    write_file(plot_dir+'/'+template_file, contents) 
    
def populate_html(template_file, data_dir, plot_dir, 
                  total_sy_hist, total_sy_ssp, perf_file_hist, perf_file_ssp): 
    """
    Generate html based on perf stats and total SY for HIST2 and SSP370 enembles. 
    """
    timestamp_html(template_file, data_dir, plot_dir)
    out_file = plot_dir+'/'+template_file
    contents = read_file(out_file)     
    contents = contents.replace('XX_SY_HIST_XX', str(round(total_sy_hist))) 
    contents = contents.replace('XX_SY_SSP_XX', str(round(total_sy_ssp))) 
    table = read_file(perf_file_hist)
    contents = contents.replace('XX_TABLE_HIST_XX', table) 
    table = read_file(perf_file_ssp)
    contents = contents.replace('XX_TABLE_SSP_XX', table) 
    write_file(out_file, contents)

def read_file(in_file): 
    """Read file and return contents"""
    f = open(in_file, 'r')
    contents = f.read()
    f.close()
    return contents     

def write_file(out_file, contents): 
    """Write contents to file."""   
    f = open(out_file, 'w') 
    f.write(contents) 
    f.close()

if __name__=='__main__': 
    data_dir = os.environ.get('DATA_DIR', '/gws/nopw/j04/canari/users/aosprey/log-analysis/data')
    plot_dir = os.environ.get('PLOT_DIR', './plots')

    coupled_data(data_dir=data_dir, plot_dir=plot_dir)
    pptransfer_data(data_dir=data_dir, plot_dir=plot_dir)
