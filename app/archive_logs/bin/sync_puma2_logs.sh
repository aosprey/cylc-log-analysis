#!/usr/bin/bash

# Sync missing log cycle dirs from puma2.
# Copies tarred up logs to Jasmin.
# They need to be untarred in next step.

set -e

echo "Suite status: $SUITE_STATUS"
echo "Archive dir: $ARCHIVE_DIR"
echo "Report dir: $REPORT_DIR"
echo "Sci host: $SCI_HOST"

# Pull in log reports 
scp $SCI_HOST:$REPORT_DIR/log_report.csv . 
scp $SCI_HOST:$REPORT_DIR/*missing* .

for file in u-*.txt
do
    
    suite=$(echo $file | cut -c1-7) 
    user=$(grep $suite $SUITE_STATUS | cut -d',' -f2)

    puma2_log_dir=/home/n02/n02/$user/cylc-run/$suite/log
    jasmin_dir=$ARCHIVE_DIR/$suite/

    job_files=''
    for cycle in $(cat $file)
    do 
	job_file=$puma2_log_dir/job-$cycle.tar.gz

	if [[ -f $job_file ]];
	then 
	    job_files+=$job_file' '
	fi 
    done
    
    echo "Syncing $suite"
    scp $job_files sci5:$jasmin_dir
    
done


