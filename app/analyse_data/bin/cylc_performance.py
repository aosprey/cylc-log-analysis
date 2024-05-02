"""Code for analysing and plotting data from cylc job logs stored in a CSV file.""" 

import os
import numpy as np
import pandas as pd 
from pandas.tseries.offsets import DateOffset
import matplotlib.pyplot as plt

# Default plot colours and data labels - can be overwritten in calling code. 
keys = ['data', 'fail', 'mean', 
        'disk', 'disk_succ', 'disk_fail', 
	'logs_off', 'logs_off_succ', 'logs_off_fail', 
	'nvme', 'nvme_succ', 'nvme_fail', 
	'sypd', 'asypd_cycle', 'asypd'] 
color_vals = ['deepskyblue', 'red', 'navy',
              'lawngreen', 'lawngreen', 'green', 
              'gold', 'gold', 'tomato', 
	      'magenta', 'magenta', 'purple', 
	      'blue', 'orange', 'green'] 
label_vals = ['Successful jobs', 'Failed jobs', 'Rolling 7 day mean', 
              'Disk', 'Succeeded Disk', 'Failed Disk',
              'XIOS logs off', 'Succeeded XIOS logs off', 'Failed XIOS logs off',
              'NVMe', 'Succeeded NVMe', 'Failed NVMe', 
	      'SYPD (rolling 7 day mean)', 'ASYPD per cycle (rolling 7 day mean)', 'ASYPD since start']
colors = dict(zip(keys, color_vals))
labels = dict(zip(keys, label_vals))


class JobPlot:

    plt.rcParams['font.size'] = '12'
    plt.rcParams['figure.figsize'] = (12,6)

    def __init__(self):
        fig, ax = plt.subplots()
        self.fig = fig 
        self.ax = ax
    
    def hlines(self, hlines):
        """Plot horizontal grid lines (if defined), usually call before plotting data."""
        if hlines is not None:
            for yval in hlines: 
                plt.axhline(y=yval, color='gray', linewidth=0.5, label='_')

    def annotate(self, x_label, y_label, title, y_ticks=None, 
                 legend_above=False, legend_loc="upper left", legend_cols=2, legend_rows=1): 
        """Add plot legend, title, axes titles, y_ticks."""
        if legend_above: 
            box = self.ax.get_position()
            if legend_rows == 1: 
                scale = 0.9
                title_pos = 1.15
            else: 
                scale = 0.85 
                title_pos = 1.25
            self.ax.set_position([box.x0, box.y0, box.width, box.height * scale])
            plt.legend(markerscale=1.2, ncol=legend_cols,
                       bbox_to_anchor=(0, 1.01, 1, 0.1), loc="lower left")
        else:
            plt.legend(loc=legend_loc)
            title_pos=1
	
        self.ax.set_xlabel(x_label)
        self.ax.set_ylabel(y_label)
        if y_ticks is not None: 
            self.ax.set_yticks(y_ticks)
        if title_pos is not None: 
            self.ax.set_title(title, y=title_pos)
        else: 
            self.ax.set_title(title)

    def save(self, plot_file):
        """Save plot."""
        plt.savefig(plot_file)
      

class SuiteStatus: 
    """Suite status data"""

    def __init__(self, csv_file): 
        dt_cols = ['First cycle', 'Start time'] 
        index_col = 'Suite id'        

        self.data = pd.read_csv(csv_file, index_col=index_col, parse_dates=dt_cols) 
        self.suites = self.data.index


class CylcJobData:
    """Data from cylc job logs for a particular task."""

    def __init__(self, csv_file, task_name, suite_status): 
        index_col = 'Batch id'
        dt_cols = ['Cycle', 'Submit time', 'Init time', 'Exit time'] 
        types = {'Batch id' : str} 

        self.data = pd.read_csv(csv_file, index_col=index_col, dtype=types, parse_dates=dt_cols)
        self.task_name = task_name
        self.suite_status = suite_status

    def write(self, out_file, cols=None): 
        """Write data as CSV file."""
        if cols is not None: 
            self.data.to_csv(out_file, columns=cols) 
        else:
            self.data.to_csv(out_file)
        
    def _filter_jobs(self, job_filter=None, suites=None): 
        """Return jobs matching filter in list of suites."""
        if suites is not None: 
            data = self.data[self.data['Suite id'].isin(suites)]
        else: 
            data = self.data
        if job_filter is not None: 
            return data.loc[job_filter]
        else: 
            return data

    def _plot_data(self, ax, x_col, y_col, ms=2, line=False, key='data', key_fail='fail', data_label=None, 
                   status=False, job_filter=None, suites=None):
        """Plot data. Default is to use symbols. 
	   Options: filter data by job and suites,
	            key in global colors and labels, 
		    plot by job status (success and failures), 
		    line plot (not with status)
		    string for label (not with status)."""
        data = self._filter_jobs(job_filter, suites)
        if status: 
            data[data['Exit status']=='SUCCEEDED'].plot(
            ax=ax, x=x_col, y=y_col, style='o', ms=ms, color=colors[key], label=labels[key])
            data[data['Exit status']=='EXIT'].plot(
            ax=ax, x=x_col, y=y_col, style='x', ms=ms, color=colors[key_fail], label=labels[key_fail])
        else: 
            if data_label is not None: 
                label = data_label 
            else: 
                label = labels[key]
            if line: 
                data.plot(ax=ax, x=x_col, y=y_col, color=colors[key], label=label)	    
            else: 
                data.plot(ax=ax, x=x_col, y=y_col, style='o', ms=ms, color=colors[key], label=label)

#    def _plot_rolling_mean(self, ax, x_col, y_col, key='mean', job_filter=None, suites=None): 
#        """Plot 7 day rolling mean."""
#        data = self._filter_jobs(job_filter, suites)
#        data = data[[x_col, y_col]].dropna()
#        data.sort_values(x_col, inplace=True)
#        rolling_mean = data.rolling('7D', min_periods=10, center=True, on=x_col).mean()
#        rolling_mean.plot(ax=ax, x=x_col, y=y_col, color=colors[key], label=labels[key])

    def _plot_rolling_mean(self, ax, x_col, y_col, key='mean', job_filter=None, suites=None): 
         """Plot 7 day rolling mean."""   
         # Group data by day and reindex, so any days with no data show up as missing data. 
         data = self._filter_jobs(job_filter, suites)
         mean_sypd_by_date = data.groupby(data[x_col].dt.date)[y_col].mean()
         dates = pd.date_range(mean_sypd_by_date.index[0], mean_sypd_by_date.index[-1])
         mean_sypd_by_date = mean_sypd_by_date.reindex(dates, fill_value=pd.NA) 
         mean_sypd_by_date.index = mean_sypd_by_date.index.tz_localize('UTC')
         mean_sypd_by_date.index = mean_sypd_by_date.index + DateOffset(hours=12)
         
         rolling_mean = mean_sypd_by_date.rolling(7, min_periods=3, center=True).mean()
         rolling_mean.plot(ax=ax, x=x_col, y=y_col, color=colors[key], label=labels[key])
	        
    def plot_quantity(self, plot_file, title, x_col, y_col, x_label, y_label, 
                      data_label='', y_ticks=None, mean=False, hlines=None, status=False, 
                      job_filter=None, suites=None):
        """Plot some metric against time. Note: can't plot status and mean together."""  
        plot = JobPlot()
        plot.hlines(hlines)
	
        self._plot_data(plot.ax,  x_col, y_col, key='data', key_fail='fail', data_label=data_label, 
	                status=status, job_filter=job_filter, suites=suites) 
        legend_cols = 2
        if status:     
            legend_rows = 2
        else:
            legend_rows = 1
            if mean: 
                job_filter = self.data['Exit status']=='SUCCEEDED'
                self._plot_rolling_mean(plot.ax, x_col, y_col, job_filter=job_filter, suites=suites)                          
                legend_cols = 3	
			
        plot.annotate(x_label, y_label, title, y_ticks=y_ticks, 
	              legend_above=True, legend_cols=legend_cols, legend_rows=legend_rows)
        plot.save(plot_file)
    
    def plot_quantity_suites(self, plot_file, title, x_col, y_col, x_label, y_label, 
                            y_ticks=None, hlines=None, job_filter=None, suites=None, ignore_rows=0):
        """Plot some metric against time, with different lines for each suite."""
        data = self._filter_jobs(job_filter, suites)
        plot = JobPlot()
        plot.hlines(hlines)

        for suite in self.suite_status.suites:
            suite_data = data[data['Suite id'] == suite][ignore_rows:]
            suite_data.plot(ax=plot.ax, x=x_col, y=y_col, label=suite) 
        
        plot.annotate(x_label, y_label, title, y_ticks=y_ticks, legend_loc='lower left')
        plot.save(plot_file)
                              
    def plot_daily_status(self, plot_file, title, suites=None, mean=False, hlines=None, y_ticks=None):
        """Plot number of task successes and failures per day."""  
        data = self._filter_jobs(suites=suites)
    
        # Group by exit status 
        status_by_date = data.groupby(data['Init time'].dt.date)['Exit status'].value_counts()
        # Reindex and fill with 0 for dates with no data
        dates = pd.date_range(status_by_date.index.get_level_values(0)[0], 
                          status_by_date.index.get_level_values(0)[-1])
        new_index = pd.MultiIndex.from_product([dates, status_by_date.index.levels[1]], 
                                               names = ["Init time", "Exit status"])
        status_by_date = status_by_date.reindex(new_index, fill_value=0)

        plot = JobPlot()
        plot.hlines(hlines)

        data = status_by_date.xs("SUCCEEDED", level="Exit status")
        data.plot(ax=plot.ax, x='Init time', y='count', color='deepskyblue', label='Succeeded')
        if mean: 
            rolling_mean = data.rolling(7, min_periods=1, center=True).mean()
            rolling_mean.plot(ax=plot.ax, x='Init time', y='count', color='navy', label='Succeeded (rolling 7 day mean)')
        data = status_by_date.xs("EXIT", level="Exit status")
        data.plot(ax=plot.ax, x='Init time', y='count', color='red', label='Failed')

        plot.annotate(x_label="Start date", y_label="Number of tasks", title=title, y_ticks=y_ticks, legend_loc="upper left")
        plot.save(plot_file)
   
    
class CoupledData(CylcJobData):
    """Cylc job log data from coupled task."""

    def __init__(self, csv_file, suite_status):
        CylcJobData.__init__(self, csv_file, 'coupled', suite_status) 

    def set_filesystem(self):
        """Work out whether jobs ran on spinning disk or nVME."""
        self.data['File system'] = 'Disk' 
        nvme_suites = self.suite_status.data[self.suite_status.data['File system'] == 'NVMe'].index    
        for nvme_suite in nvme_suites: 
            first_cycle = self.suite_status.data.loc[nvme_suite, 'First NVMe cycle']
            cycles = (self.data['Suite id'] == nvme_suite) & (self.data['Cycle'] >= first_cycle)
            self.data.loc[cycles, 'File system'] = 'NVMe'

    def set_xios_logs(self): 
        """Work out whether job ran with XIOS logging on or off."""
        self.data['XIOS logs'] = True
        logs_off_suites = self.suite_status.data[~self.suite_status.data['XIOS logs']].index 
        for suite in logs_off_suites:     
            first_cycle = self.suite_status.data.loc[suite, 'First no log cycle']
            cycles = (self.data['Suite id'] == suite) & (self.data['Cycle'] >= first_cycle)
            self.data.loc[cycles, 'XIOS logs'] = False

    def reset_errors(self): 
        """Fix cycles which are marked as succeeded but actually failed."""
        suites_3m = self.suite_status.data[self.suite_status.data['Cycle length (days)'] == 90].index
        jobs = (self.data['Suite id'].isin(suites_3m)) & (self.data['Elapsed time (s)'] < 7200)
        self.data.loc[jobs, 'Exit status'] = 'EXIT'

    def calc_metrics(self, asypd=False): 
        """Calculate run/queue time in h and SYPD."""
        self.__time_hours()
        self.__calc_sypd()
        if asypd: 
            self.__calc_asypd()
            self.__calc_rolling_asypd()
        
    def __time_hours(self): 
        """Calculate run time & queue time in h."""
        self.data['Queued time (h)'] = self.data['Queued time (s)'] / 3600.0
        self.data['Elapsed time (h)'] = self.data['Elapsed time (s)'] / 3600.0

    def __calc_sypd(self): 
        """Calculate SYPD for each successful job."""
        for suite in self.suite_status.suites: 
            cycles_per_year = 360 / self.suite_status.data.loc[suite, 'Cycle length (days)'] 
            successful_jobs = (self.data['Suite id'] == suite) & (self.data['Exit status'] == 'SUCCEEDED')
            self.data.loc[successful_jobs, 'SYPD'] = 86400.0 / (self.data.loc[successful_jobs, 'Elapsed time (s)']*cycles_per_year)
            
    def __calc_run_length(self): 
        """Calculte length of the run so far in years, for each cycle."""
        for suite in self.suite_status.suites: 
            jobs = (self.data['Suite id'] == suite) & (self.data['Exit status'] == 'SUCCEEDED')
            
            # To do: Catch case where cycle length is not an exact number of months         
            cycle_months = self.suite_status.data.loc[suite,'Cycle length (days)'] / 30 
            start_cycle = self.suite_status.data.loc[suite,'First cycle']
            start_years = start_cycle.year + (start_cycle.month-cycle_months) / 12
            self.data.loc[jobs, 'Run length (years)'] = (self.data.loc[jobs, 'Cycle'].dt.year +
                                                         self.data.loc[jobs, 'Cycle'].dt.month/12 - start_years)
                
    def __calc_run_time(self): 
        """Calculate time taken so far in days for each cycle"""
        for suite in self.suite_status.suites: 
            jobs = (self.data['Suite id'] == suite) & (self.data['Exit status'] == 'SUCCEEDED') 
        
            start_time = self.suite_status.data.loc[suite,'Start time']
            self.data.loc[jobs,'Run time (days)'] = (self.data.loc[jobs,'Exit time'] - start_time).dt.total_seconds() / 86400.0

    def __calc_cycle_time(self): 
        """Calculate time to complete cycle, starting from completion time of previous cycle."""
        for suite in self.suite_status.suites: 
            jobs = (self.data['Suite id'] == suite) & (self.data['Exit status'] == 'SUCCEEDED') 
            self.data.loc[jobs, 'Cycle time (hours)'] = (self.data.loc[jobs, 'Exit time'] - 
                                                         self.data.loc[jobs, 'Exit time'].shift()).dt.total_seconds() / 3600.0
      
    def __calc_asypd(self): 
        """Calculate ASYPD for each job."""
        self.__calc_run_length()
        self.__calc_run_time()
        self.data['ASYPD'] = self.data['Run length (years)'] / self.data['Run time (days)']

    def __calc_rolling_asypd(self): 
        self.__calc_cycle_time()
        self.data['Cycle ASYPD'] = (1/12) / (self.data['Cycle time (hours)']/24)
        
    def plot_queue_time(self, plot_file, title, hlines=None, mean=False, suites=None):
        """Plot queue time for all jobs.""" 
        self.plot_quantity(plot_file=plot_file, title=title, 
                           x_col='Submit time', y_col='Queued time (h)', 
                           x_label='Submission time', y_label='Queue time (h)', 
                           data_label='Queue time per job', 
                           mean=mean, hlines=hlines, suites=suites)

    def plot_sypd(self, plot_file, title, suites=None, mean=False, hlines=None, y_ticks=None):
        """Plot SYPD for successful tasks."""
        self.plot_quantity(plot_file=plot_file, title=title, 
                           x_col='Init time', y_col='SYPD', x_label='Start time', y_label='SYPD', 
                           data_label='SYPD per job', y_ticks=y_ticks, 
                           mean=mean, hlines=hlines, suites=suites)
                           
    def plot_runtime(self, plot_file, title, suites=None, mean=False, hlines=None, y_ticks=None, status=False):
        """Plot run time. If status specified plot succeeded and failed jobs, otherwise just succeede ones."""
        if not status: 
            job_filter = self.data['Exit status']=='SUCCEEDED'
        self.plot_quantity(data, plot_file=plot_file, title=title, 
                           x_col='Init time', y_col='Elapsed time (h)', 
                           x_label='Start time', y_label='Time to completion (h)', 
                           data_label='Run time per job', y_ticks=y_ticks, 
                           mean=mean, hlines=hlines, status=status, 
                           job_filter=job_filter, suites=suites)
               
    def plot_asypd(self, plot_file, title, suites=None, ignore_rows=0, y_ticks=None, hlines=None): 
        """Plot ASYPD over time for each suite as separate lines. Ignore first X cycles"""
        job_filter = self.data['Exit status']=='SUCCEEDED'
        self.plot_quantity_suites(plot_file, title,
                                 x_col='Exit time', y_col='ASYPD', 
                                 x_label='Completion time for coupled job', y_label='ASYPD',
                                 y_ticks=y_ticks, hlines=hlines, 
                                 job_filter=job_filter, suites=suites, ignore_rows=ignore_rows)

    def plot_asypd_sypd_suites(self, plot_file, title, suites=None, y_ticks=None, hlines=None): 
        """Plot SYPD as rolling mean, ASYPD over time and ASYPD per cycle as rolling mean.
	   Generates one plot per suite."""		
        job_filter = self.data['Exit status']=='SUCCEEDED'
        root, ext = os.path.splitext(plot_file)
        for suite in self.suite_status.suites: 
            plot = JobPlot()
            plot.hlines(hlines)           
            
            self._plot_rolling_mean(plot.ax, 'Init time', 'SYPD', key='sypd', job_filter=job_filter, suites=[suite]) 
            self._plot_rolling_mean(plot.ax, 'Init time', 'Cycle ASYPD', key='asypd_cycle', job_filter=job_filter, suites=[suite])
            self._plot_data(plot.ax, 'Init time', 'ASYPD', line=True, key='asypd', job_filter=job_filter, suites=[suite])
	    
            title_suite = title + ': ' + self.suite_status.data.loc[suite, 'Description'] + '(' + suite + ')'
            plot.annotate('Job start time', 'SYPD', title, legend_above=True, legend_cols=3, legend_rows=1)     
            plot_file_suite = root + '_' + suite + ext	    
            plot.save(plot_file_suite)  
                
    def plot_quantity_filesystem(self, plot_file, title, x_col, y_col, x_label, y_label, ms=2, hlines=None, 
                                 mean=False, status=None, date_string='2023-03-01', xios_logs=False, suites=None): 
        """Plot quantity, split up by file system and optionally whether XIOS writing logs."""                 
        ref_date = pd.Timestamp(date_string, tz='UTC')
        date_filter = self.data['Submit time'] > ref_date
    
        if xios_logs:
            work_filter = (self.data['File system'] == 'Disk') & (self.data['XIOS logs']) & date_filter
            logs_off_filter = (self.data['File system'] == 'Disk') & ~(self.data['XIOS logs']) & date_filter
        else: 
            work_filter = (self.data['File system'] == 'Disk') & date_filter
        nvme_filter = (self.data['File system'] == 'NVMe') & date_filter
    
        plot = JobPlot()
        plot.hlines(hlines)
        legend_cols = 2	
        if status:
            keys = ['disk_succ', 'logs_off_succ', 'nvme_succ']
            legend_rows = 2
        else: 
            keys = ['disk', 'logs_off', 'nvme']
            legend_rows = 1
 
        self._plot_data(plot.ax, x_col, y_col, ms=ms, key=keys[0], key_fail='disk_fail',
	                status=status, job_filter=work_filter, suites=suites) 
        if xios_logs: 
            self._plot_data(plot.ax, x_col, y_col, ms=ms, key=keys[1], key_fail='logs_off_fail',
	                   status=status, job_filter=logs_off_filter, suites=suites) 
            legend_cols += 1 
        self._plot_data(plot.ax, x_col, y_col, ms=ms, key=keys[2], key_fail='nvme_fail', 
	               status=status, job_filter=nvme_filter, suites=suites)            
        if mean and not status:
            job_filter = self.data['Exit status']=='SUCCEEDED'
            self._plot_rolling_mean(plot.ax, x_col, y_col, job_filter=job_filter, suites=suites) 
            legend_cols += 1
 
        plot.annotate(x_label, y_label, title, legend_above=True, legend_cols=legend_cols, legend_rows=legend_rows) 
        plt.savefig(plot_file)
	
    def plot_runtime_filesystem(self, plot_file, title, ms=2, hlines=None, date_string='2023-03-01', 
                                status=False, xios_logs=False, suites=None):
        """Plot runtime per job, split by file system. 
           Options to plot whether XIOS logs off, and plot success and failures."""
        self.plot_quantity_filesystem(plot_file=plot_file, title=title, 
                                      x_col='Init time', y_col='Elapsed time (h)',
				      x_label='Job start time', y_label='Time to completion (h)',
                                      ms=ms, hlines=hlines, date_string=date_string, 
				      status=status, xios_logs=xios_logs, suites=suites)
	
    def plot_sypd_filesystem(self, plot_file, title, ms=2, hlines=None, date_string='2023-03-01', 
                              mean=False, xios_logs=False, suites=None):
        """Plot SYPD per job, split by file system. 
           Options to plot whether XIOS logs off, and plot rolling mean."""
        self.plot_quantity_filesystem(plot_file=plot_file, title=title, 
                                      x_col='Init time', y_col='SYPD', x_label='Job start time', y_label='SYPD',
                                      ms=ms, hlines=hlines, date_string=date_string, 
				      mean=mean, xios_logs=xios_logs, suites=suites)	

class PPTransferData(CylcJobData): 
    """Cylc job log data from pptransfer task."""

    def __init__(self, csv_file, suite_status):
        CylcJobData.__init__(self, csv_file, 'pptransfer', suite_status)
        
    def calc_metrics(self): 
        """Work out transfer speed. Ignore some outliers."""
        start_date = pd.Timestamp('2023-09-25', tz='UTC')
        end_date = pd.Timestamp('2023-09-27', tz='UTC')
        suites = ['u-cz568','u-cw264']
        outliers = (  self.data['Suite id'].isin(suites) & 
                     (self.data['Init time'] > start_date) & 
                     (self.data['Init time'] < end_date) )
        valid_jobs = ( (self.data['Rep'] == 1) & 
                       (self.data['Exit status'] == 'SUCCEEDED') & 
                       ~outliers )
        self.data.loc[valid_jobs,'Speed (MB/s)'] = (self.data.loc[valid_jobs,'Data size (GB)'] * 1024 /
                                                  self.data.loc[valid_jobs,'Elapsed time (s)'])

    def plot_speed(self, plot_file, title, suites=None, mean=False, hlines=None): 
        """Plot transfer speed."""           
        self.plot_quantity(plot_file=plot_file, title=title, 
                           x_col='Init time', y_col='Speed (MB/s)', 
                           x_label='Start time', y_label='Transfer speed (MB/s)', 
                           data_label='Speed of transfer job (MB/s)', 
                           mean=mean, hlines=hlines, suites=suites)
