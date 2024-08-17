"""Code for analysing and plotting data from cylc job logs stored in a CSV file.""" 

import os
import numpy as np
import pandas as pd 
from pandas.tseries.offsets import DateOffset
import matplotlib.pyplot as plt
from datetime import timedelta

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
              'Disk + XIOS logs', 'Disk + XIOS logs: succeeded', 'Disk + XIOS logs: failed',
              'Disk', 'Disk: succeeded', 'Disk: failed',
              'NVMe', 'NVMe: succeeded', 'NVMe: failed', 
	      'SYPD (mean over prev 7 days)', 'ASYPD (prev 7 days)', 'ASYPD since start']
colors = dict(zip(keys, color_vals))
labels = dict(zip(keys, label_vals))

def convert_to_period(x):
    """Convert a date string formatted as YYYYMMDD... to pandas period[D]"""
    if pd.isnull(x):
        return pd.NaT
    else: 
        return pd.Period(year=int(x[0:4]), month=int(x[4:6]), day=int(x[6:8]), freq='D')


class JobPlot:

    plt.rcParams['font.size'] = '12'
    plt.rcParams['figure.figsize'] = (12,6)

    def __init__(self):
        fig, ax = plt.subplots()
        self.fig = fig 
        self.ax = ax
	
    def __del__(self):
        plt.close(self.fig)

    def annotate(self, x_label, y_label, title, y_ticks=None, y_grid=False, 
                 legend_above=False, legend_loc="upper left", legend_cols=2, legend_rows=1): 
        """Add to plot: legend, title, axes labels, y ticks, y grid lines."""
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

        if title_pos is not None: 
            self.ax.set_title(title, y=title_pos)
        else: 
            self.ax.set_title(title)
        self.ax.set_xlabel(x_label)
        self.ax.set_ylabel(y_label)
        if y_ticks is not None: 
            self.ax.set_yticks(y_ticks)
        if y_grid:
            plt.grid(axis='y')

    def save(self, plot_file):
        """Save plot."""
        plt.savefig(plot_file)
	
 
class SuiteStatus: 
    """Suite status data"""
    
    float_format = '%.2f'
    date_format = '%Y-%m-%d %H:%M:%S'

    def __init__(self, csv_file): 
        index_col = 'Suite id'
        dt_cols = ['Start time']
        period_cols = ['First cycle', 'First NVMe cycle', 'First no log cycle']
        self.data = pd.read_csv(csv_file, index_col=index_col, parse_dates=dt_cols)
        for col in period_cols: 
            self.data[col] = self.data[col].apply(convert_to_period)
        self.suites = self.data.index
	
    def write_csv(self, out_file, cols=None, suites=None): 
        """Write data as CSV file."""
        if suites is not None: 
            suite_info = self.data.loc[suites]
        else:
            suite_info = self.data
        suite_info.to_csv(out_file, columns=cols, 
                         float_format=self.float_format, date_format=self.date_format)
	
    def write_html(self, out_file, cols=None, formatters=None, suites=None): 
        """Write data as HTML table.
	   To do: Should be able to get formatters to work directly with to_html()"""
        if suites is not None:
            suite_info = self.data.loc[suites]
        else:
            suite_info = self.data
        if formatters is not None: 
            for col in cols: 
                suite_info[col] = suite_info[col].apply(formatters[col])
        suite_info.to_html(out_file, columns=cols, justify='left', render_links=True, escape=False)


class CylcJobData:
    """Data from cylc job logs for a particular task."""

    def __init__(self, csv_file, task_name, suite_status): 
        index_col = 'Batch id'
        dt_cols = ['Submit time', 'Init time', 'Exit time'] 
        types = {'Batch id':str, 'Cycle':'period[D]'} 

        self.data = pd.read_csv(csv_file, index_col=index_col, dtype=types, parse_dates=dt_cols)
        self.task_name = task_name
        self.suite_status = suite_status

    def write(self, out_file, cols=None): 
        """Write data as CSV file."""
        if cols is not None: 
            self.data.to_csv(out_file, columns=cols) 
        else:
            self.data.to_csv(out_file)
        
    def _filter_jobs(self, job_filter=None, job_filter2=None, suites=None, succeeded_only=False, x_col=None): 
        """Filter data based on various optional criteria: 
           generic job filter, list of suites, exit status of succeeded, and a non-null value in x-col for plotting."""
        data = self.data
        if job_filter is not None: 
            data = data.loc[job_filter]
        if job_filter2 is not None:
            data = data.loc[job_filter2]
        if suites is not None: 
            data = data[data['Suite id'].isin(suites)]
        if succeeded_only: 
            data = data[data['Exit status']=='SUCCEEDED']
        if x_col is not None: 
            data = data[data[x_col].notnull()]
        return data

    def _plot_data(self, ax, x_col, y_col, ms=2, line=False, key='data', key_fail='fail', data_label=None, 
                   status=False, job_filter=None, job_filter2=None, suites=None, succeeded_only=False):
        """Plot data. Default is to use symbols. 
	   Options: filter data by job and suites,
	            key in global colors and labels, 
		    plot by job status (success and failures), 
		    line plot (not with status)
		    string for label (not with status)."""
        data = self._filter_jobs(job_filter=job_filter, job_filter2=job_filter2, suites=suites, x_col=x_col, succeeded_only=succeeded_only)
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

    def _calc_rolling_mean(self, x_col, y_col, window='7D', min_periods=10, job_filter=None, center=True, suites=None, succeeded_only=False):
         """Calc rolling mean. Return as y_col indexed by x_col."""
         data = self._filter_jobs(job_filter=job_filter, suites=suites, succeeded_only=succeeded_only)
         data = data[[x_col, y_col]].dropna()
         if data.empty:
             return
         data.sort_values(x_col, inplace=True)
         rolling = data.rolling(window, min_periods=min_periods, center=center, on=x_col).mean()
         return rolling.set_index(x_col)

    def _calc_rolling_daily_mean(self, x_col, y_col, window=7, min_periods=3, center=True, 
                                 job_filter=None, suites=None, succeeded_only=False): 
         """Plot 7 day rolling mean.
            Group data by day and reindex, so any days with no data show up as missing data."""
         data = self._filter_jobs(job_filter=job_filter, suites=suites, succeeded_only=succeeded_only)
         if data.empty:
             return
         mean_by_date = data.groupby(data[x_col].dt.date)[y_col].mean()
         dates = pd.date_range(mean_by_date.index[0], mean_by_date.index[-1])
         mean_by_date = mean_by_date.reindex(dates, fill_value=pd.NA) 
         mean_by_date.index = mean_by_date.index.tz_localize('UTC')
         mean_by_date.index = mean_by_date.index + DateOffset(hours=12)
         return mean_by_date.rolling(window, min_periods=min_periods, center=center).mean()

    def _plot_rolling_mean(self, ax, x_col, y_col, key='mean', center=True, daily_mean=True,
                           job_filter=None, suites=None, succeeded_only=False): 
         """Plot 7 day rolling mean."""
         if daily_mean: 
             rolling_mean = self._calc_rolling_daily_mean(x_col, y_col, job_filter=job_filter, center=center, 
                                                          suites=suites, succeeded_only=succeeded_only)
         else: 
             rolling_mean = self._calc_rolling_mean(x_col, y_col, job_filter=job_filter, center=center, 
                                                    suites=suites, succeeded_only=succeeded_only)
         if rolling_mean is not None: 
             rolling_mean.plot(ax=ax, x=x_col, y=y_col, color=colors[key], label=labels[key])
	        
    def plot_quantity(self, plot_file, title, x_col, y_col, x_label, y_label, 
                      data_label='', legend_above=True, y_ticks=None, y_grid=False, 
                      mean=False, status=False, job_filter=None, suites=None, succeeded_only=False):
        """Plot some metric against time. Note: can't plot status and mean together."""
        plot = JobPlot()
        self._plot_data(plot.ax,  x_col, y_col, key='data', key_fail='fail', data_label=data_label, 
	                status=status, job_filter=job_filter, suites=suites, succeeded_only=False) 
        legend_cols = 2
        if status:     
            legend_rows = 2
        else:
            legend_rows = 1
            if mean: 
                self._plot_rolling_mean(plot.ax, x_col, y_col, job_filter=job_filter, suites=suites, succeeded_only=True)
                legend_cols = 3
        plot.annotate(x_label, y_label, title, y_ticks=y_ticks, y_grid=y_grid,
                      legend_above=legend_above, legend_cols=legend_cols, legend_rows=legend_rows)
        plot.save(plot_file)
    
    def plot_quantity_suites(self, plot_file, title, x_col, y_col, x_label, y_label, y_ticks=None, y_grid=False, 
                             job_filter=None, suites=None, ignore_rows=0, succeeded_only=False):
        """Plot some metric against time, with different lines for each suite."""
        data = self._filter_jobs(job_filter=job_filter, suites=suites, succeeded_only=succeeded_only)
        plot = JobPlot()

        for suite in self.suite_status.suites:
            suite_data = data[data['Suite id'] == suite][ignore_rows:]
            suite_data.plot(ax=plot.ax, x=x_col, y=y_col, label=suite) 

        plot.annotate(x_label, y_label, title, y_ticks=y_ticks, y_grid=y_grid, legend_loc='lower left')
        plot.save(plot_file)
                              
    def plot_daily_status(self, plot_file, title, suites=None, mean=False, ref_date=None, y_ticks=None, y_grid=False):
        """Plot number of task successes and failures per day."""
        if ref_date is not None:
            date_filter = self.data['Init time'] > ref_date
        else: 
            date_filter = None
        data = self._filter_jobs(suites=suites, job_filter=date_filter)
    
        # Group by exit status 
        status_by_date = data.groupby(data['Init time'].dt.date)['Exit status'].value_counts()
        # Reindex and fill with 0 for dates with no data
        dates = pd.date_range(status_by_date.index.get_level_values(0)[0], 
                          status_by_date.index.get_level_values(0)[-1])
        new_index = pd.MultiIndex.from_product([dates, status_by_date.index.levels[1]], 
                                               names = ["Init time", "Exit status"])
        status_by_date = status_by_date.reindex(new_index, fill_value=0)

        plot = JobPlot()
        data = status_by_date.xs("SUCCEEDED", level="Exit status")
        data.plot(ax=plot.ax, x='Init time', y='count', color='deepskyblue', label='Succeeded')
        if mean: 
            rolling_mean = data.rolling(7, min_periods=1, center=True).mean()
            rolling_mean.plot(ax=plot.ax, x='Init time', y='count', color='navy', label='Succeeded (rolling 7 day mean)')
        data = status_by_date.xs("EXIT", level="Exit status")
        data.plot(ax=plot.ax, x='Init time', y='count', color='red', label='Failed') 

        plot.annotate(x_label="Start date", y_label="Number of tasks", title=title, y_ticks=y_ticks, y_grid=y_grid, 
                      legend_loc="upper left")
        plot.save(plot_file)
   
    
class CoupledData(CylcJobData):
    """Cylc job log data from coupled task."""
        
    def __init__(self, csv_file, suite_status):
        CylcJobData.__init__(self, csv_file, 'coupled', suite_status) 
        
    def __time_hours(self): 
        """Calculate run time & queue time in h."""
        self.data['Queued time (h)'] = self.data['Queued time (s)'] / 3600.0
        self.data['Elapsed time (h)'] = self.data['Elapsed time (s)'] / 3600.0

    def __successful_jobs(self, suite): 
        """Return boolean list of jobs that completed successfully for suite."""
        return (self.data['Suite id'] == suite) & (self.data['Exit status'] == 'SUCCEEDED')

    def __calc_sypd(self): 
        """Calculate SYPD for each successful job."""
        for suite in self.suite_status.suites: 
            cycles_per_year = 360 / self.suite_status.data.loc[suite, 'Cycle length (days)'] 
            successful_jobs = (self.data['Suite id'] == suite) & (self.data['Exit status'] == 'SUCCEEDED')
            self.data.loc[successful_jobs, 'SYPD'] = 86400.0 / (self.data.loc[successful_jobs, 'Elapsed time (s)']*cycles_per_year)
            
    def __calc_completed_years(self): 
        """Calculte length of the run so far in years, for each cycle."""
        for suite in self.suite_status.suites: 
            jobs = self.__successful_jobs(suite)
            # To do: Catch case where cycle length is not an exact number of months         
            cycle_months = self.suite_status.data.loc[suite,'Cycle length (days)'] / 30 
            self.suite_status.data.loc[suite,'Cycle length (months)'] = cycle_months
            start_cycle = self.suite_status.data.loc[suite,'First cycle']
            start_years = start_cycle.year + (start_cycle.month-cycle_months) / 12
            self.data.loc[jobs, 'Completed years'] = (self.data.loc[jobs, 'Cycle'].dt.year +
                                                      self.data.loc[jobs, 'Cycle'].dt.month/12 - start_years)
                
    def __calc_run_time(self): 
        """Calculate time taken so far in days for each cycle. 
           Take start time as time of first submitted job."""
        for suite in self.suite_status.suites: 
            data = self._filter_jobs(suites=[suite])
            if data.empty: 
                continue 
            jobs = self.__successful_jobs(suite)
            start_time = data['Submit time'].iloc[0]
            self.data.loc[jobs,'Run time (days)'] = (self.data.loc[jobs,'Exit time'] 
                                                    - start_time).dt.total_seconds() / 86400.0

    def __calc_cycle_time(self): 
        """Calculate time to complete cycle, starting from completion time of previous cycle."""
        for suite in self.suite_status.suites:
            jobs = self.__successful_jobs(suite)
            self.data.loc[jobs, 'Cycle time (hours)'] = (self.data.loc[jobs, 'Exit time'] - 
                                                         self.data.loc[jobs, 'Exit time'].shift()).dt.total_seconds() / 3600.0
      
    def __calc_asypd(self): 
        """Calculate ASYPD (since start of run) for each job."""
        self.__calc_completed_years()
        self.__calc_run_time()
        self.data['ASYPD'] = self.data['Completed years'] / self.data['Run time (days)']
	 
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
        """Fix cycles which are marked as succeeded but actually failed.
           This should maybe be outside main code."""
        suites_3m = self.suite_status.data[self.suite_status.data['Cycle length (days)'] == 90].index
        jobs = (self.data['Suite id'].isin(suites_3m)) & (self.data['Elapsed time (s)'] < 7200)
        self.data.loc[jobs, 'Exit status'] = 'EXIT'

    def calc_metrics(self): 
        """Calculate metrics for each successful job: 
           - run time in h, queue time in h
	   - SYPD, ASYPD (since start), ASYPD (current cycle)."""
        self.__time_hours()
        self.__calc_sypd()
        self.__calc_asypd()
        self.__calc_cycle_time()

    def __progress_stats(self): 
        """Derive run progress stats for each run"""
        data_by_suite = self.data.groupby('Suite id')
        suite_info = self.suite_status.data
        suite_info['Run length (years)'] = (suite_info['Cycle length (days)'] * suite_info['Run length (cycles)']) / 360
        last_job = data_by_suite.nth(-1, dropna='any').set_index('Suite id')
        suite_info['Completed years'] = last_job['Completed years']
        suite_info['Last job exit time'] = last_job['Exit time']
        suite_info['SYPD'] = data_by_suite['SYPD'].mean()
        suite_info['ASYPD'] = data_by_suite['ASYPD'].last()
        self.suite_status.data = suite_info

    def __predict_end(self): 
        """Work out when run will completed based on ASYPD for last 7 days."""
        suite_info = self.suite_status.data
        running_suites = suite_info[suite_info['Status'] == 'Running'].index
        for suite in running_suites:
            suite_info.loc[suite,'Remaining years'] = suite_info.loc[suite,'Run length (years)'] - suite_info.loc[suite,'Completed years']
            suite_info.loc[suite, 'Time of latest job'] = suite_info.loc[suite, 'Last job exit time']
            ref_date = suite_info.loc[suite, 'Time of latest job'] - timedelta(days=7)
            job_filter = self.data['Exit time'] > ref_date
            data = self._filter_jobs(job_filter=job_filter, suites=[suite], succeeded_only=True)
            if data.shape[0] == 0: 
                print(suite, 'no jobs in last 7 days')
                suite_info.loc[suite, 'ASYPD (last 7 days)'] = 0
            else: 
                start = data['Cycle'].iloc[0]
                end = data['Cycle'].iloc[-1]
                cycle_months = suite_info.loc[suite,'Cycle length (months)']
                start_years = start.year + (start.month - cycle_months)/12
                completed_years = (end.year + end. month/12) - start_years

                start_time = data['Submit time'].iloc[0]
                end_time = data['Exit time'].iloc[-1]
                run_time_days = (end_time - start_time).total_seconds() / 86400
                suite_info.loc[suite, 'ASYPD (last 7 days)'] = completed_years / run_time_days
                remaining_days = suite_info.loc[suite,'Remaining years'] / suite_info.loc[suite, 'ASYPD (last 7 days)']
                suite_info.loc[suite,'Predicted end time'] = suite_info.loc[suite,'Time of latest job'] + timedelta(days=remaining_days)
        self.suite_status.data = suite_info
        	    
    def calc_suite_stats(self): 
        """Calculate summary stats for each suite: 
	   - target run length (years), run progress (years)
	   - SYPD, ASYPD (since start), ASYPD (over last 7 days), 
	   - date of last completed job, predicted end date
	   Need to have already run calc_metrics()."""
        self.__progress_stats()
        self.__predict_end()
	
    def __html_formatters(self, plot_format):
        """Define html formatters for suite perf data.
	   Could pass these in."""
        self.out_cols = ['Description', 'Status', 'File system',
                         'Completed years', 'SYPD', 'ASYPD', 'ASYPD (last 7 days)', 
                         'Time of latest job', 'Remaining years', 'Predicted end time', 
                         'Plot']
        default_formatters = lambda x: x
        self.col_formatters = {col:default_formatters for col in self.out_cols}

        date_cols = ['Time of latest job', 'Predicted end time']
        date_format = '%Y-%m-%d %H:%M:%S'
        date_formatter = lambda x: x.strftime(date_format) if pd.notnull(x) else ''
        self.col_formatters.update({col:date_formatter for col in date_cols})
    
        float_cols = ['Run length (years)', 'Completed years', 
                      'SYPD', 'ASYPD', 'ASYPD (last 7 days)', 
	              'Remaining years']
        float_format = '{:.2f}'
        float_formatter = lambda x: float_format.format(x) if pd.notnull(x) else ''
        self.col_formatters.update({col:float_formatter for col in float_cols})
	
	# Add in link to plots
        self.suite_status.data['Plot'] = self.suite_status.data.apply(lambda x: plot_format.format(x.name), axis=1)
	
    def write_suite_stats(self, csv_file=None, html_file=None, plot_format=None, suites=None): 
        """
        Write out suite perf data as csv and/or html. 
        For html, option to point to plot file.
	"""
        if csv_file is not None:
            self.suite_status.write_csv(csv_file, suites=suites)
        if html_file is not None:
            self.__html_formatters(plot_format)
            self.suite_status.write_html(
	        html_file, cols=self.out_cols, formatters=self.col_formatters, suites=suites)
	
    def plot_queue_time(self, plot_file, title, mean=False, suites=None, ref_date=None, y_grid=False):
        """Plot queue time for all jobs.""" 
        if ref_date is not None: 
            job_filter = self.data['Submit time'] > ref_date
        else: 
            job_filter = None
        self.plot_quantity(plot_file=plot_file, title=title, 
                           x_col='Submit time', y_col='Queued time (h)', 
                           x_label='Submission time', y_label='Queue time (h)', 
                           data_label='Queue time per job',
                           legend_above=False, mean=mean, y_grid=y_grid,
                           suites=suites, job_filter=job_filter)

    def plot_sypd(self, plot_file, title, suites=None, mean=False, ref_date=None, y_ticks=None, y_grid=False):
        """Plot SYPD for successful tasks."""
        if ref_date is not None: 
            job_filter = self.data['Init time'] > ref_date
        else: 
            job_filter = None
        self.plot_quantity(plot_file=plot_file, title=title, 
                           x_col='Init time', y_col='SYPD', x_label='Start time', y_label='SYPD', 
                           data_label='SYPD per job', y_ticks=y_ticks, y_grid=y_grid,
                           mean=mean, suites=suites, job_filter=job_filter)
                           
    def plot_runtime(self, plot_file, title, suites=None, mean=False, ref_date=None,
                     y_ticks=None, y_grid=False, status=False):
        """Plot run time. If status specified plot succeeded and failed jobs, otherwise just succeeded ones."""
        if ref_date is not None: 
            job_filter = self.data['Init time'] > ref_date
        else:
            job_filter = None
        succeeded_only = not status
        self.plot_quantity(plot_file=plot_file, title=title, 
                           x_col='Init time', y_col='Elapsed time (h)', 
                           x_label='Start time', y_label='Time to completion (h)', 
                           data_label='Run time per job', y_ticks=y_ticks, y_grid=y_grid, 
                           mean=mean, status=status,
                           job_filter=job_filter, suites=suites, succeeded_only=succeeded_only)
               
    def plot_asypd(self, plot_file, title, suites=None, ignore_rows=0, y_ticks=None, y_grid=False): 
        """Plot ASYPD over time for each suite as separate lines. Ignore first X cycles"""
        self.plot_quantity_suites(plot_file, title,
                                 x_col='Exit time', y_col='ASYPD', 
                                 x_label='Completion time for coupled job', y_label='ASYPD',
                                 y_ticks=y_ticks, y_grid=y_grid, 
                                 job_filter=job_filter, suites=suites, ignore_rows=ignore_rows, succeeded_only=True)

    def _plot_rolling_asypd(self, ax, suite): 
        rolling_mean = self._calc_rolling_mean('Init time', 'Cycle time (hours)', min_periods=1, center=False, 
                                               suites=[suite], succeeded_only=True)
        if rolling_mean is not None:
            cycle_months = self.suite_status.data.loc[suite, 'Cycle length (months)']
            rolling_mean['ASYPD'] = (24 * cycle_months/12) / rolling_mean['Cycle time (hours)']
            rolling_mean.plot(ax=ax, y='ASYPD', color=colors['asypd_cycle'], label=labels['asypd_cycle'])

    def plot_asypd_sypd_suites(self, plot_file, title, suites=None, y_ticks=None, y_grid=False): 
        """Plot SYPD, ASYPD as rolling mean over prev 7 days, and ASYPD since start over time.
	   Generates one plot per suite.
           Add filename to suite_status for html table."""		
        root, ext = os.path.splitext(plot_file)
        if suites is None: 
            suites = self.suite_status.suites
        for suite in suites: 
            plot = JobPlot()
            self._plot_rolling_mean(plot.ax, 'Init time', 'SYPD', key='sypd', center=False, 
                                    suites=[suite], succeeded_only=True) 
            self._plot_rolling_asypd(plot.ax, suite) 
            self._plot_data(plot.ax, 'Init time', 'ASYPD', line=True, key='asypd', suites=[suite], succeeded_only=True)
            title_suite = title + ': ' + self.suite_status.data.loc[suite, 'Description'] + '(' + suite + ')'
            plot.annotate('Job start time', 'SYPD', title, y_ticks=y_ticks, y_grid=y_grid, 
                          legend_above=True, legend_cols=3, legend_rows=1)     
            plot_file_suite = root + '_' + suite + ext	   
            plot.save(plot_file_suite)  
                
    def plot_quantity_filesystem(self, plot_file, title, x_col, y_col, x_label, y_label, ms=2,
                                 mean=False, status=None, ref_date=None, xios_logs=False, suites=None, y_grid=False): 
        """Plot quantity, split up by file system and optionally whether XIOS writing logs."""
        if ref_date is not None:
            date_filter = self.data['Init time'] > ref_date
        else: 
            date_filter = None
        if xios_logs:
            work_filter = (self.data['File system'] == 'Disk') & (self.data['XIOS logs'])
            logs_off_filter = (self.data['File system'] == 'Disk') & ~(self.data['XIOS logs'])
        else: 
            work_filter = (self.data['File system'] == 'Disk')
        nvme_filter = (self.data['File system'] == 'NVMe')
    
        plot = JobPlot()
        legend_cols = 2	
        if status:
            keys = ['disk_succ', 'logs_off_succ', 'nvme_succ']
            legend_rows = 2
        else: 
            keys = ['disk', 'logs_off', 'nvme']
            legend_rows = 1
 
        self._plot_data(plot.ax, x_col, y_col, ms=ms, key=keys[0], key_fail='disk_fail',
	                status=status, job_filter=work_filter, job_filter2=date_filter, suites=suites) 
        if xios_logs: 
            self._plot_data(plot.ax, x_col, y_col, ms=ms, key=keys[1], key_fail='logs_off_fail',
	                   status=status, job_filter=logs_off_filter, job_filter2=date_filter, suites=suites) 
            legend_cols += 1 
        self._plot_data(plot.ax, x_col, y_col, ms=ms, key=keys[2], key_fail='nvme_fail', 
	               status=status, job_filter=nvme_filter, job_filter2=date_filter, suites=suites)            
        if mean and not status:
            self._plot_rolling_mean(plot.ax, x_col, y_col, job_filter=date_filter, suites=suites, succeeded_only=True) 
            legend_cols += 1
 
        plot.annotate(x_label, y_label, title, y_grid=y_grid, 
                      legend_above=True, legend_cols=legend_cols, legend_rows=legend_rows) 
        plt.savefig(plot_file)
	
    def plot_runtime_filesystem(self, plot_file, title, ms=2, ref_date=None, 
                                status=False, xios_logs=False, suites=None, y_grid=False):
        """Plot runtime per job, split by file system. 
           Options to plot whether XIOS logs off, and plot success and failures."""
        self.plot_quantity_filesystem(plot_file=plot_file, title=title, 
                                      x_col='Init time', y_col='Elapsed time (h)',
				      x_label='Job start time', y_label='Time to completion (h)',
                                      ms=ms, ref_date=ref_date, status=status, xios_logs=xios_logs, suites=suites, y_grid=y_grid)
	
    def plot_sypd_filesystem(self, plot_file, title, ms=2, ref_date=None, 
                              mean=False, xios_logs=False, suites=None, y_grid=False):
        """Plot SYPD per job, split by file system. 
           Options to plot whether XIOS logs off, and plot rolling mean."""
        self.plot_quantity_filesystem(plot_file=plot_file, title=title, 
                                      x_col='Init time', y_col='SYPD', x_label='Job start time', y_label='SYPD',
                                      ms=ms, ref_date=ref_date, mean=mean, xios_logs=xios_logs, suites=suites, y_grid=y_grid)	


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

    def plot_speed(self, plot_file, title, suites=None, mean=False, y_grid=False): 
        """Plot transfer speed."""
        self.plot_quantity(plot_file=plot_file, title=title, 
                           x_col='Init time', y_col='Speed (MB/s)', 
                           x_label='Start time', y_label='Transfer speed (MB/s)', 
                           data_label='Speed of transfer job (MB/s)', 
                           mean=mean, y_grid=y_grid, suites=suites)
