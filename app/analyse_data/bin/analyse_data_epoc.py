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

    # Filters 
    #suites_prod = suite_status.data[suite_status.data['Production']].index
    #suites_LL = suite_status.data[suite_status.data['Description'].str.contains('LL') &
    #                              suite_status.data['Production']].index
    #suites_HH = suite_status.data[suite_status.data['Description'].str.contains('HH') &
    #                              suite_status.data['Production']].index
    suites_all = suite_status.data.index
    suites_LL = suite_status.data[suite_status.data['Description'].str.contains('LL')].index
    suites_HH = suite_status.data[suite_status.data['Description'].str.contains('HH')].index

    # Plots 
    image_dir = plot_dir+'/IMAGES'
    ens_label = 'LL runs on ARCHER2: '
    coupled.plot_queue_time(
        plot_file=image_dir+'/coupled_queue_time_LL.png', 
        title=ens_label+'Job queue times', 
	suites=suites_LL, mean=True, y_grid=True)
    coupled.plot_runtime(
        plot_file=image_dir+'/coupled_runtime_LL.png', 
        title=ens_label+'Run times per model month', 
	suites=suites_LL, status=True, y_grid=True) 
    coupled.plot_sypd(
        plot_file=image_dir+'/coupled_SYPD_LL.png', 
        title=ens_label+'SYPD per model month', 
        suites=suites_LL, mean=True, y_grid=True) 
    coupled.plot_daily_status(
        plot_file=image_dir+'/coupled_status_LL.png', 
        title=ens_label+'Model task statuses per day', 
        suites=suites_LL, mean=True, y_grid=True)

    ens_label = 'HH runs on ARCHER2: '
    coupled.plot_queue_time(
        plot_file=image_dir+'/coupled_queue_time_HH.png', 
        title=ens_label+'Job queue times', 
	suites=suites_HH, mean=True, y_grid=True)
    coupled.plot_runtime_filesystem(
        plot_file=image_dir+'/coupled_runtime_HH.png', 
        title=ens_label+'Run times per model month', 
	suites=suites_HH, status=True, xios_logs=True, y_grid=True) 
    coupled.plot_sypd_filesystem(
        plot_file=image_dir+'/coupled_SYPD_HH.png', 
        title=ens_label+'SYPD per model month', 
        suites=suites_HH, mean=True, xios_logs=True, y_grid=True) 
    coupled.plot_daily_status(
        plot_file=image_dir+'/coupled_status_HH.png', 
        title=ens_label+'Model task statuses per day', 
        suites=suites_HH, mean=True, y_ticks=np.arange(5,25,5), y_grid=True)

    coupled.plot_asypd_sypd_suites(
        plot_file=image_dir+'/asypd_sypd.png', 
	suites=suites_all, title='Run speed on ARCHER2')
	
    # HTML
    plot_format = '<a href="IMAGES/asypd_sypd_{0}.png">{0}</a>'
    perf_html_LL = plot_dir+'/DATA/suite_perf_LL.html'
    coupled.write_suite_stats(html_file=perf_html_LL, plot_format=plot_format, suites=suites_LL)
    perf_html_HH = plot_dir+'/DATA/suite_perf_HH.html'
    coupled.write_suite_stats(html_file=perf_html_HH, plot_format=plot_format, suites=suites_HH)

    timestamp_html('coupled_plots_LL.html', plot_dir)
    timestamp_html('coupled_plots_HH.html', plot_dir)
    populate_html('index.html', data_dir, plot_dir, perf_html_LL, perf_html_HH)

    # Suite stats
    perf_csv = plot_dir+'/DATA/suite_perf.csv'
    coupled.write_suite_stats(csv_file=perf_csv)
   
def pptransfer_data(data_dir='.', plot_dir='.'): 
    """Generate performance plots for pptransfer jobs."""
    # Load data 
    suite_status = SuiteStatus(data_dir+'/suite_status.csv')     
    pptransfer = PPTransferData(data_dir+'/pptransfer_jobs.csv', suite_status) 

    # Calculate metrics 
    pptransfer.calc_metrics()

    # Filters 
    suites_LL = suite_status.data[suite_status.data['Description'].str.contains('LL')].index
    suites_HH = suite_status.data[suite_status.data['Description'].str.contains('HH')].index

    # Plots
    image_dir = plot_dir+'/IMAGES'
    ens_label = 'LL runs on ARCHER2: '
    pptransfer.plot_daily_status(
        plot_file=image_dir+'/pptransfer_status_LL.png', 
        title='EPOC transfer task statuses each day', 
	suites=suites_LL, mean=True, y_grid=True)
    pptransfer.plot_speed(
        plot_file=image_dir+'/pptransfer_speed_LL.png', 
	title='EPOC speed of successful transfer tasks',
        suites=suites_LL, mean=True, y_grid=True)

    ens_label = 'HH runs on ARCHER2: '
    pptransfer.plot_daily_status(
        plot_file=image_dir+'/pptransfer_status_HH.png', 
        title='EPOC transfer task statuses each day', 
	suites=suites_HH, mean=True, y_ticks=np.arange(5,30,5), y_grid=True)
    pptransfer.plot_speed(
        plot_file=image_dir+'/pptransfer_speed_HH.png', 
	title='EPOC speed of successful transfer tasks',
        suites=suites_HH, mean=True, y_grid=True)

    timestamp_html('pptransfer_plots_LL.html', plot_dir) 
    timestamp_html('pptransfer_plots_HH.html', plot_dir) 

def timestamp_html(template_file, plot_dir): 
    """Add timesamp to html template file."""
    contents = read_file(template_file) 
    now = pd.Timestamp.now()
    now_str = now.strftime('%Y-%m-%d %H:%M:%S')
    contents = contents.replace('XX_DATE_XX', now_str) 
    write_file(plot_dir+'/'+template_file, contents) 

def populate_html(template_file, data_dir, plot_dir, perf_file_LL, perf_file_HH): 
    """
    Generate html wrapper for plots and perf stats based on template file. 
    """
    timestamp_html(template_file, plot_dir)
    out_file = plot_dir+'/'+template_file
    contents = read_file(out_file)
    table = read_file(perf_file_LL)
    contents = contents.replace('XX_TABLE_LL_XX', table) 
    table = read_file(perf_file_HH)
    contents = contents.replace('XX_TABLE_HH_XX', table) 
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
    data_dir = os.environ.get('DATA_DIR', '.')
    plot_dir = os.environ.get('PLOT_DIR', './plots')

    coupled_data(data_dir=data_dir, plot_dir=plot_dir)
    pptransfer_data(data_dir=data_dir, plot_dir=plot_dir)
