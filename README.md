# cylc-log-analysis

A cylc-8 workflow for asynchronously archiving and analysing cylc job logs from multiple cylc suites/workflows.

This workflow is set up to analyse the CANARI runs performed on ARCHER2.

## Outputs

The data and plots are all on the JASMIN CANARI GWS.
* Log files are archived to: `/gws/nopw/j04/canari/users/aosprey/logs`
* Data extracted from coupled job logs: `/gws/nopw/j04/canari/users/aosprey/log-analysis/data/coupled_jobs.csv`
* Plots: https://gws-access.jasmin.ac.uk/public/canari/perf_analysis/IMAGES/
* Performance metrics: https://gws-access.jasmin.ac.uk/public/canari/perf_analysis/DATA/
  
## Details

The workflow looks like this:
```
    [[graph]]   
        PT12H = """
                @wall_clock => archive_logs:finish => 
                check_logs:fail? => sync_puma2_logs => untar_logs
                """

        P1D = """
              @wall_clock => archive_logs:finish => 
              check_logs:fail? => sync_puma2_logs => untar_logs
              check_logs? | untar_logs => process_logs

              process_logs => concat_logs =>
              plot_coupled => performance_stats => plot_wsypd => 
              housekeeping 
              """
```

### `archive_logs` app

* `file/suite_status.csv`: Defines the suites to be archived/analysed. 
* `archive_logs`: Rsyncs the `cylc-run/log` directories for each suite to a location on JASMIN gws.
* `check_logs`: Since the A2 logs are purged by housekeeping, check if there are any missing cycles.
* `sync_puma2_logs`: If gaps are identified, copy the tarred up job logs from puma2.
* `untar_logs`: Untar the logs on Jasmin. 

### `process_logs` app

* `process_logs`: Identify new jobs, extract data, and add to a data file for each suite. For each job the code extracts the slurm batch id, submit time, run time, exit time and exit status. Then the run times and queue times for each job are derived.
* `concat_logs`: Combine the data files for all suites into a single file for analysis.  

### `analyse_data` app

* `plot_coupled`: generate some plots for the coupled tasks over all suites:
  * queue time
  * run time
  * status (how many jobs succeeded and failed each day)
  * speed (in SYPD) 
* `performance_statys`: calculate metrics for each suite:
  * the run progress in simulated years
  * the speed of the model in simulated years per day (SYPD)
  * the speed of the workflow as a whole in actual simulated years per day (ASYPD)
* `plot_wsypd`: plots the weighted SYPD for each suite
