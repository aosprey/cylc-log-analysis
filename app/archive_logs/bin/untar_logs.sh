#!/bin/bash 
set -e

# Untar job logs copied over from puma2, and delete the tar file. 

echo "Archive dir: $ARCHIVE_DIR"
echo "Report dir: $REPORT_DIR"

cd $REPORT_DIR

for file in u-*.txt
do
    echo $file
    suite=$(echo $file | cut -c1-7)
    echo "Extracting $suite logs"
    cd $ARCHIVE_DIR/$suite

    # Just put logs in latest dir if more than one exists
    logdir=$(ls | grep log | tail -n1) 
   
    mv job* $logdir 
    cd $logdir 
    for file in job*tar.gz 
    do 
	echo "Extracting $file"
        tar -zxf $file
	rm $file
    done

done

# Clean up
rm $REPORT_DIR/*missing*.txt 
