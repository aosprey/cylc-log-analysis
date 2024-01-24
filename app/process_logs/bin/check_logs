#!/usr/bin/bash
#
# Report the number of cycles archived to Jasmin, and if there are gaps. 
# Just checks for cycle directories. Doesn't check task statuses. 
# Writes out missing cycles for each suite.
# Returns error code equal to number of suites with missing cycles. 

set -e

echo "Suite status: $SUITE_STATUS"
echo "Archive dir: $ARCHIVE_DIR"
echo "Report dir: $REPORT_DIR"
echo "Report file: $REPORT_FILE"

# Check we can read suite status file
if [ ! -f $SUITE_STATUS ]; then
    echo "Error: Can't find suite status file: $SUITE_STATUS"
    exit 1
fi

# Write header
header="Suite id,Final cycle,Last completed cycle,"
header+="Run length (cycles),Num cycle dirs,Missing cycles"
echo $header > $REPORT_DIR/$REPORT_FILE

# Keep track of the number of failures
err_count=0

# Loop through suite status file entries
while IFS="," read -r suite status cycle_len run_len start_cycle final_cycle
do

    echo "Processing $suite"
    
    # Count cycle directories archived on Jasmin
    dirs=""

    # Reset vars
    last_completed_cycle=""
    num_cycles=""
    num_missing_cycles=""
    
    # Check suite dir exists
    if [[ -d $ARCHIVE_DIR/$suite ]];
    then
        cd $ARCHIVE_DIR/$suite
			
        # Look in all log directories 
        for log in log*
        do 
    	    if [[ -d $log/job ]]; 
	    then 
	        cd $log/job
	        dirs+=$(\ls)' '
	        cd ../../
	    fi
        done
		
        # Directories with cycle date format
        cycle_dirs=$(echo $dirs | grep -Eo "[0-9]{8}T[0-9]{4}Z")
    
        # Remove duplicates and sort for comparison
        actual_cycles=$(echo $cycle_dirs | tr ' ' '\n' | sort -u)
 
        num_cycles=$(echo $actual_cycles | wc -w)	
        last_completed_cycle=$(echo $actual_cycles | awk '{print $NF}')

        # Only look at missing cycles for 3m cycling suites 	
        if [[ "$cycle_len" -eq 90 ]];
        then

	    # Work out what cycles we should have
    	    ref_cycles=''

    	    start_year=$(echo $start_cycle | cut -c1-4)
    	    end_year=$(echo $last_completed_cycle | cut -c1-4)
    	    years=$(seq $start_year $end_year)
    
    	    for year in $years
    	    do 
	        for month in 01 04 07 10
	        do
    	    	    cycle=$year$month'01T0000Z'
	    	    ref_cycles+=$cycle
	
	    	    if [[ "$cycle" == "$last_completed_cycle" ]]; 
	    	    then
		        break 2
	    	    else  
		        ref_cycles+=$'\n'
	    	    fi
	        done 
    	    done
	
    	    # Compare actual against ref
    	    missing_cycles=$(comm -23 <(echo "$ref_cycles") <(echo "$actual_cycles"))	
	    num_missing_cycles=$(echo $missing_cycles | wc -w)

	    # Write missing cycles to file
	    if [[ "$num_missing_cycles" -gt 0 ]];
	    then
	        ((err_count+=1))
	        file=$REPORT_DIR/$suite'_missing.txt'
	        echo "$missing_cycles" > $file 
	    fi
	
        else 
	    num_missing_cycles="X"
        fi
    fi
	
    # Report 
    suite_report=$(echo $suite,$status,$final_cycle,$last_completed_cycle,)
    suite_report+=$(echo $run_len,$num_cycles,$num_missing_cycles) 
    echo $suite_report >> $REPORT_DIR/$REPORT_FILE
	
done < <(cut -d "," -f1,5,8-11 $SUITE_STATUS | tail -n +2)

# Report status
echo "Info: Missing cycles in $err_count suites." >&2
exit $err_count





