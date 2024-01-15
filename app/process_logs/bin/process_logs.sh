#!/usr/bin/bash
set -e

# Extract run times and submit times from cycle logs.
# Can process all suites, or just suites where we are transferring logs. 
# To do: catch error if can't read suite_status 

echo "Process all: $PROCESS_ALL"
echo "Archive dir: $ARCHIVE_DIR"
echo "Data dir: $DATA_DIR"
echo "Suite status: $SUITE_STATUS"
echo "Tasks: $TASKS"

. log_functions.sh

while IFS="," read -r suite process
do
    if [[ "$PROCESS_ALL" == "True" || "$process" == "True" ]]
    then
	logdir=$ARCHIVE_DIR/$suite
	rawdir=${DATA_DIR}/raw/${suite}
	procdir=${DATA_DIR}/processed/${suite}
    
	# Check suite dir exists
	if [[ ! -d $logdir ]]
	then
            continue
	fi 

	# Make output directories if they do not exist	  
	if [[ ! -d "$rawdir" ]]; 
	then 
	    mkdir -p $rawdir
	fi

	if [[ ! -d "$procdir" ]]
	then
	    mkdir -p $procdir
	fi

        for task in $TASKS
        do   
	    echo "Processing $suite $task" 

            cylc_data_raw=${rawdir}/${task}_cylc.csv
            cylc_data_proc=${procdir}/${task}_cylc.csv

	    get_cylc_times $logdir $task $cylc_data_raw 
	    process_cylc_times.py $cylc_data_raw $cylc_data_proc
	done

    fi
done < <(cut -d "," -f1,7 $SUITE_STATUS | tail -n +2) 

