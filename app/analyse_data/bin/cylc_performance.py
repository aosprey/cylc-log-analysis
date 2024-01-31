"""Code for analysing and plotting data from cylc job logs stored in a CSV file.""" 

import numpy as np
import pandas as pd 
from pandas.tseries.offsets import DateOffset
import matplotlib.pyplot as plt

def setup_plots(): 
    """Set plotting parameters"""

    plt.rcParams['font.size'] = '12'
    plt.rcParams['figure.figsize'] = (12,6)


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

    def plot_status(self, plot_file, suites=None, mean=False, hlines=None):
        """Plot number of task successes and failures per day."""
        # Filter data by suites 
        if suites is not None: 
            data = self.data[self.data['Suite id'].isin(suites)]
        else:
            data = self.data 
        
        # Group by exit status 
        status_by_date = data.groupby(data['Init time'].dt.date)['Exit status'].value_counts()

        # Reindex and fill with 0 for dates with no data
        dates = pd.date_range(status_by_date.index.get_level_values(0)[0], 
                          status_by_date.index.get_level_values(0)[-1])
        new_index = pd.MultiIndex.from_product([dates, status_by_date.index.levels[1]], 
                                               names = ["Init time", "Exit status"])
        status_by_date = status_by_date.reindex(new_index, fill_value=0)

        fig, ax = plt.subplots()

        # Plot horizontal lines underneath
        if hlines is not None: 
            for yval in hlines: 
                plt.axhline(y=yval, color='black', linewidth=0.5, label='_')

        data = status_by_date.xs("SUCCEEDED", level="Exit status")
        data.plot(ax=ax, x='Init time', y='count', color='deepskyblue', label='Succeeded')

        if mean: 
            rolling_mean = data.rolling(7, min_periods=1, center=True).mean()
            rolling_mean.plot(ax=ax, x='Init time', y='count', color='navy', label='Succeeded (rolling 7 day mean)')

        data = status_by_date.xs("EXIT", level="Exit status")
        data.plot(ax=ax, x='Init time', y='count', color='red', label='Failed')

        plt.legend(loc='upper left')
        ax.set_xlabel('Start date')
        ax.set_ylabel('Number of tasks')
        ax.set_title('CANARI '+self.task_name+' task statuses each day')

        plt.savefig(plot_file)   

    def plot_quantity(self, plot_file, x_col, y_col, x_label, y_label, data_label, title, 
		      y_ticks=None, job_filter=None, mean=False, hlines=None):
        """Plot some metric against time. Optionally add 7 day rolling mean."""        
        # Filter 
        if job_filter is not None: 
            data = self.data[job_filter]
        else: 
            data = self.data 

        fig, ax = plt.subplots()

        # Plot horizontal lines underneath
        if hlines is not None: 
            for yval in hlines: 
                plt.axhline(y=yval, color='black', linewidth=0.5, label='_')
 
        # Plot data 
        data.plot(ax=ax, x=x_col, y=y_col, label=data_label, style='o', ms=2, color='deepskyblue') 
 
        # Daily means 
        if mean: 
            mean_sypd_by_date = data.groupby(data[x_col].dt.date)[y_col].mean()
            dates = pd.date_range(mean_sypd_by_date.index[0], mean_sypd_by_date.index[-1])
            mean_sypd_by_date = mean_sypd_by_date.reindex(dates, fill_value=pd.NA) 
            mean_sypd_by_date.index = mean_sypd_by_date.index.tz_localize('UTC')
            mean_sypd_by_date.index = mean_sypd_by_date.index + DateOffset(hours=12)

            rolling_mean = mean_sypd_by_date.rolling(7, min_periods=3, center=True).mean()
            rolling_mean.plot(ax=ax, x=x_col, y=y_col, color='navy', label='Rolling 7 day mean')   	      

        # Annotate plot
        box = ax.get_position()
        ax.set_position([box.x0, box.y0, box.width, box.height * 0.9])
    
        plt.legend(markerscale=1.2, bbox_to_anchor=(0, 1.01, 1, 0.1), loc="lower left", ncol=2)
        ax.set_xlabel(x_label)
        ax.set_ylabel(y_label)
        if y_ticks is not None: 
            ax.set_yticks(y_ticks)
        plt.title(title, y=1.15)

        plt.savefig(plot_file)
			      
    
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

    def calc_metrics(self): 
        """Calculate run/queue time in h and SYPD."""
        self.data['Queued time (h)'] = self.data['Queued time (s)'] / 3600.0
        self.data['Elapsed time (h)'] = self.data['Elapsed time (s)'] / 3600.0

        for suite in self.suite_status.suites: 
            cycles_per_year = 360 / self.suite_status.data.loc[suite, 'Cycle length (days)'] 
            successful_jobs = (self.data['Suite id'] == suite) & (self.data['Exit status'] == 'SUCCEEDED')
            self.data.loc[successful_jobs, 'SYPD'] = 86400.0 / (self.data.loc[successful_jobs, 'Elapsed time (s)']*cycles_per_year)

    def plot_runtime(self, plot_file, suites=None, date_string='2023-03-01', ms=2, xios_logs=False): 
        """Plot time to completion for successful tasks. 
        Organise by file system and optionally whether XIOS writing logs."""
        # Filter data by suites 
        if suites is not None: 
            data = self.data[self.data['Suite id'].isin(suites)]
        else:
            data = self.data 
 
        fig, ax = plt.subplots()
	
        ref_date = pd.Timestamp(date_string, tz='UTC')
		
        # Plot baseline: (spinning disk) work
        if xios_logs:
            work_data = data[ (data['File system'] == 'Disk')  & 
	                           (data['Submit time'] > ref_date) & 
				   (data['XIOS logs']) ]
        else: 
            work_data = data[ (data['File system'] == 'Disk')  & 
	                           (data['Submit time'] > ref_date) ]
        work_data[work_data['Exit status']=='SUCCEEDED'].plot(
            ax=ax, x='Init time', y='Elapsed time (h)', style='o', ms=ms, color='lawngreen')
        work_data[work_data['Exit status']=='EXIT'].plot(
            ax=ax, x='Init time', y='Elapsed time (h)', style='x', mew=1.5, ms=ms, color='green')
    
        # Plot NVMe
        nvme_data = data[(data['File system'] == 'NVMe') & (data['Submit time'] > ref_date)]

        nvme_data[nvme_data['Exit status']=='SUCCEEDED'].plot(
            ax=ax, x='Init time', y='Elapsed time (h)', style='o', ms=ms, color='magenta')
        nvme_data[nvme_data['Exit status']=='EXIT'].plot(
            ax=ax, x='Init time', y='Elapsed time (h)', style='+', mew=1.5, ms=ms+1, color='purple')


        # Plot XIOS logs off (Work only) 
        if xios_logs:
            logs_off_data = data[ (data['File system'] == 'Disk')  &
				  (data['Submit time'] > ref_date) & 
				  ~(data['XIOS logs']) ]
            logs_off_data[logs_off_data['Exit status']=='SUCCEEDED'].plot(
                ax=ax, x='Init time', y='Elapsed time (h)', style='o', ms=ms, color='gold')
            logs_off_data[logs_off_data['Exit status']=='EXIT'].plot(
                ax=ax, x='Init time', y='Elapsed time (h)', style='x', mew=1.5, ms=ms, color='tomato')
     
        # Annotate plot
        box = ax.get_position()
        ax.set_position([box.x0, box.y0, box.width, box.height * 0.85])
        labels = ['Succeeded Disk', 'Failed Disk', 
                  'Succeeded NVMe', 'Failed NVMe', 
                  'Succeeded XIOS logs off', 'Failed XIOS logs off']
        if xios_logs:
            plt.legend(labels, markerscale=1.5, ncol=3, 
                       bbox_to_anchor=(0.1, 1.01, 1, 0.1), loc="lower left")
        else: 
            plt.legend(labels[:4], markerscale=1.5, ncol=2, 
                       bbox_to_anchor=(0.1, 1.01, 1, 0.1), loc="lower left")
        ax.set_xlabel('Start time')
        ax.set_ylabel('Time to completion (h)')
        title='CANARI coupled task run times since {}'.format(date_string)
        plt.title(title, y=1.25) 

        plt.savefig(plot_file)

    def plot_queue_time(self, plot_file, suites=None, mean=False, hlines=None):
        """Plot queue time for all jobs."""
        if suites is not None: 
            job_filter = self.data['Suite id'].isin(suites)
        else:
            job_filter = None
	    
        self.plot_quantity(plot_file=plot_file, 
                           x_col='Submit time', y_col='Queued time (h)', 
			   x_label='Submission time', y_label='Queue time (h)', 
	                   data_label='Queue time per job', 
			   title='CANARI coupled task queue times', 
		           job_filter=job_filter, mean=mean, hlines=hlines)

    def plot_sypd(self, plot_file, suites=None, mean=False, hlines=None):
        """Plot SYPD for successful tasks."""
        if suites is not None: 
            job_filter = self.data['Suite id'].isin(suites)
        else: 
            job_filter = None

        self.plot_quantity(plot_file=plot_file, 
	                   x_col='Init time', y_col='SYPD', x_label='Start time', y_label='SYPD', 
	                   data_label='SYPD per job', title='CANARI SYPD for successful coupled tasks', 
		           y_ticks=np.arange(0.6,2.6,0.2), 
		           job_filter=job_filter, mean=mean, hlines=hlines)
		

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

    def plot_speed(self, plot_file, suites=None, mean=False, hlines=None): 
        """Plot transfer speed."""
        if suites is not None: 
            job_filter = self.data['Suite id'].isin(suites) 
        else: 
            job_filter = None 

        self.plot_quantity(plot_file=plot_file, 
                           x_col='Init time', y_col='Speed (MB/s)', 
                           x_label='Start time', y_label='Transfer speed (MB/s)', 
                           data_label='Speed of transfer job (MB/s)', 
                           title='CANARI speed of successful pptransfer tasks', 
                           job_filter=job_filter, mean=mean, hlines=hlines)
