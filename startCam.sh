#!/bin/bash

#Could probably be rewritten without output.txt file?

#TODO add timeout/collect errors

#TODO: kill all associated programs on exit, this script only has to kill camFunctions.py

#TODO:
# Problem is on line 24
# Netcat command from ./ncStreamClient.sh doesnt print "Listening on..." line to output.txt
# Once all lines have been read the program stops instead of calling ./piStream.sh

#set -x

ip=$1
port=$2
camName=$3

echo "Starting $camName..."

echo "Starting ./ncStreamClient.sh..."
echo "Redirecting stderr and stdout to ./output.txt..."
./ncStreamClient.sh $port $camName &> output.txt &

echo "Starting ./camFunctions.py..."
#python ./MotionDetecTest.py &
python ./camFunctions.py & #> output.txt &

sleep 2

while read line
do
    echo $line
    if [ "$line" = "Listening on [0.0.0.0] (family 0, port $2)" ]
    then
	echo "Calling piStream.sh to start video to pipe..."
	sleep 1
	./piStream.sh $ip $port '640' '480' '20' '0'
    fi
done < output.txt

#TODO: there should be a message here or in loop above if NetCat doesn't listen
echo "$camName stopped."

