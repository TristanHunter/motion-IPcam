#!/bin/bash

#TODO: Add error handling
#TODO: Add trap to kill netcat on exit, confirm if this is necessary

#set -x

port=$1
camName=$2		#Name should not have file extension

fifoName='fifo'$2	#Create unique fifo name for every camera

if [ -p  $fifoName ]
then
	echo -n "Removing $fifoName..."
	rm $fifoName
	echo "Done"
fi

#Handle error with making fifo
echo -n "Making new fifo $fifoName..."
mkfifo $fifoName
echo "Done"

#Handle error with starting nc
echo -e "Starting netcat..."
nc -l -p $port > $fifoName -v
echo "Successfully started netcat listener."	#This is only printed in output.txt after nc is killed
