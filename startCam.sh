#!/bin/bash

#Could probably be rewritten without output.txt file?

#TODO add timeout/collect errors

#TODO: kill all associated programs on exit, this script only has to kill camFunctions.py

#TODO:
# Problem is on line 24
# Netcat command from ./ncStreamClient.sh doesnt print "Listening on..." line to output.txt
# Once all lines have been read the program stops instead of calling ./piStream.sh

#set -x

#USAGE: ./startCam 192.168.0.28 5777 Cam1 640 480 20 22:00:00 0

ip=$1
port=$2
camName=$3
width=$4
height=$5
fps=$6
backup_time=$7
comp_factor=$8	#set to 0 for no compression

echo "Starting $camName..."

echo "Starting ./ncStreamClient.sh..."
echo "Redirecting stderr and stdout to ./output.txt..."
./ncStreamClient.sh $port $camName &> output.txt &

echo "Starting ./camFunctions.py..."
#python ./MotionDetecTest.py &
python ./camFunctions.py $camName $height $width $fps $backup_time & #> output.txt &

sleep 2

while read line
do
    echo $line
    if [ "$line" = "Listening on [0.0.0.0] (family 0, port $2)" ]
    then
	echo "Calling piStream.sh to start video to pipe..."
	sleep 1
	./piStream.sh $ip $port $width $height $fps $comp_factor
    fi
done < output.txt

#TODO: there should be a message here or in loop above if NetCat doesn't listen
echo "$camName stopped."

