#!/usr/bin/bash 

# The main function to be called.
# Get job times from a cylc job log directory. 
# Loop through all cycles and attempts for specified task. 
# Get batch id, submit time, start time, end time and exit status. 
# Try job.status first, then job-activity.log file. 
# Write data to a CSV file. 
# Inputs: job log dir, task name, output CSV file 

get_cylc_times() { 

    local log_dir=$1
    local task_name=$2
    local out_file=$3

    local current_dir=$PWD

    # First see if we can work out the last cycle recorded in out_file 
    local start=$(get_last_recorded_cycle $out_file) || new_file="True"
    
    echo "Starting from $start"
    
    # Start new log data file 
    if [[ "$new_file" == "True" ]]; then 
        write_data_header > $out_file 
	
    # Remove records from $start as we will re-process these
    else 
    	clear_last_cycle $out_file $start
    fi 
    
    if [ ! -d $log_dir ]; then 
        echo "Error: $log_dir does not exist"
        exit
    fi
    cd $log_dir

    for log in log.*; do
        if [ ! -d $log/job ]; then 
	    echo "Warning: $PWD/$log/job does not exist" >&2
	    continue
        fi
        cd $log/job

        # Work out which files to process
        cycles=$(get_cycles_to_process $start) 

        for cycle in $cycles; do

            if [ ! -d $cycle/$task_name ]; then
 	        continue
	    fi

	    cd $cycle/$task_name

            # Look at all repeats including failures, ignoring NN
	    for rep in [0-9]*; do
	        cd $rep

                reset_job_variables

                # Try job.status 
                if [ -f job.status ]; then 			
		    parse_job_status >> $out_file

                # Try job-activity.log
	        elif [ -f job-activity.log ]; then
		    parse_job_activity >> $out_file
		    env |grep "CYLC"
		
	        else 
		    echo "Warning: $PWD: No job information" >&2
                    cd ../
		    continue
	        fi
	    
	        #write_job_data $out_file

	        cd ../
	    done		    
	    cd ../../
	done
        cd ../../
    done

    cd $current_dir
} 


# Get the last cycle written in job data CSV. 
# Inputs: job log CSV file 
# Outputs: last valid cycle in file 
# Return: 1 if none found

get_last_recorded_cycle(){ 

    local file=$1

    # Check file exists 
    if [ ! -f $file ]; then  
        return 1
    fi 

    # Check contains at least 2 lines
    local len=$(wc -l $file | cut -f 1 -d ' ') 
    if (( len < 2 )); then  
        return 1 
    fi 
    
    # Test last line 
    check_cycle $file $len && return 0
    
    # Test 2nd to last line 
    (( len = len-1 ))
    check_cycle $file $len || return 1
} 


# Get first element of line N from file, 
# and test if it is in the format expected for a cycle. 
# Inputs: job log CSV file, line
# Outputs: last valid cycle in file 
# Return: 1 if none found

check_cycle(){ 

    local file=$1 
    local line=$2
    local pattern='^[0-9]{8}T[0-9]{4}Z$'
    
    # Get first element of line
    start=$(sed -n "${line}p" < $file | cut -f1 -d,)

    if [[ $start =~ $pattern ]]; then 
        echo $start 
    else 
        return 1 
    fi 
} 


# Remove lines from log job data CSV file, 
# starting from specified cycle. 
# Inputs: file, cycle

clear_last_cycle(){ 

   local file=$1
   local cycle=$2
     
   sed -i "/^$cycle/,\$d" $file
} 



# Return list of cycles in current dir, 
# starting from $start cycle if specified.
# Inputs: start cycle
# Outputs: list of cycles 

get_cycles_to_process(){ 

    local start=$1
    local run="False"
        
    if [ -z $start ]; then
    
        # If start not defined, just print all cycles 
    	for cycle in *; do 
	    echo $cycle 
	done 
    else   
        for cycle in *; do 
    	    if [[ "$run" == "True" ]]; then 
                echo $cycle 
            elif [[ "$cycle" == "$start" ]]; then 
                run="True"
                echo $cycle 
            fi 
        done
    fi
} 


# Reset cylc job status variables

reset_job_variables(){ 

    CYLC_BATCH_SYS_JOB_ID=""
    CYLC_BATCH_SYS_JOB_SUBMIT_TIME=""
    CYLC_JOB_INIT_TIME=""
    CYLC_JOB_EXIT=""
    CYLC_JOB_EXIT_TIME=""
} 


# Sets variables in cylc job.status file. 
# Inputs: job.status file 

parse_job_status(){ 
    
    while read -r line; do declare $line; done < job.status
    write_job_data   
} 


# Attempts to set cylc job status variables from 
# job-activity.log file. 
# Inputs: job-activity.log file 

parse_job_activity(){ 
 
    # Find status line - should be the last one starting with [jobs-poll out]
    local line=$(grep "\[jobs-poll out\]" job-activity.log | tail -1)

    CYLC_BATCH_SYS_JOB_ID=$(echo $line | grep -Po '"batch_sys_job_id": "\K.*?(?=")')
    CYLC_BATCH_SYS_JOB_SUBMIT_TIME=$(echo $line | grep -Po '"time_submit_exit": "\K.*?(?=")')
    CYLC_JOB_INIT_TIME=$(echo $line | grep -Po '"time_run": "\K.*?(?=")')
    CYLC_JOB_EXIT_TIME=$(echo $line | grep -Po '"time_run_exit": "\K.*?(?=")')
    local run_status=$(echo $line | grep -Po '"run_status": \K.*?(?=,)')
    if [[ "$run_status" == "0" ]]; then 
	CYLC_JOB_EXIT="SUCCEEDED"
    else 
	CYLC_JOB_EXIT=$(echo $line | grep -Po '"run_signal": "\K.*?(?=")')
    fi
    write_job_data  
} 


# Print header for cylc job data CSV file 

write_data_header(){ 

    echo "Cycle,Rep,Batch id,Submit time,Init time,Exit time,Exit status"
}
    
    

# Print data for cylc job to CSV file 

write_job_data(){

    echo "$cycle,$rep,$CYLC_BATCH_SYS_JOB_ID,$CYLC_BATCH_SYS_JOB_SUBMIT_TIME,$CYLC_JOB_INIT_TIME,$CYLC_JOB_EXIT_TIME,$CYLC_JOB_EXIT"   
} 


