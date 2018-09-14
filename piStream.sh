#!/bin/bash

#TODO: Need to exit gracefully after ctl-c command, w/o broken pipe message
#TODO: Should quit ssh after issuing command (probably need to use nohup or screen)

#set -x		#This should be set for debugging all scrips

#Kill netcat on the server side, otherwise the camera continues to run and this script can't run again
function finish {
	echo "Stopping $0..."
	echo "Cleaning up..."
	ssh pi@$streamIp 'sudo pkill nc && exit' #TODO: Confirm this command is working
	echo "Stream from $streamIp closed."
}

#Check for ip address and port args
if [ "$#" -ne 6 ]; then
	echo -e "\nERROR: Incorrect arguments to $0"
	echo -e "USAGE: $0 <Pi IP addr> <dest port> <width> <height> <fps> <compression>\n"
	exit
fi

trap finish EXIT			#Clean up if script is exited

streamIp=$1				#Store args, startCam.sh has already validated them
port=$2
width=$3
height=$4
fps=$5
comp=$6
localIp=$(hostname -I | awk '{ print $1 }')	#Store IP address of this machine

#Check if pi has camera connected
camStatus=$(ssh -o ConnectTimeout=15 pi@$streamIp "vcgencmd get_camera | awk -F= '{print \$3}'")

if [[ $camStatus == 0 ]]; then
	echo -e "Error: No camera connected at $1."
	exit
fi

#Start ssh session and video stream
echo "Starting video stream from $streamIp..."

#ConnectTimeout option might not be necessary
ssh -v -o ConnectTimeout=10 \
	-o ServerAliveInterval=30 \
	-o ServerAliveCountMax=120 \
	pi@$streamIp \
	"raspivid -vf -n -w $width -h $height -fps $fps -o - -t 0 -b 2000000 -qp $comp \
	| nc $localIp $port" &

#TODO: maybe check return value of command above
	#if (returnValue != success)
		#echo "Error: Cannot start video stream from $ip

for i in {1..10}				#Primitive timeout counter for nc command
do
	if grep -F "Connection from $streamIp" output.txt | grep "received"; then
		echo "Opening live video viewer..."
		break
	else
		sleep 1
	fi

	if [ $i == 10 ]; then
		echo -e "Error: Netcat connection failed."
		exit
	fi
done

#This should be removed and startCam.sh should wait and trap kill all related process at end
wait	#Wait for netcat to terminate or be terminated
echo "SSH command finished"
