#! /bin/bash

python_v=/usr/bin/python2.6
ran_time=$(( RANDOM % 480 )).$(( RANDOM % 1000 )) 

sleep $ran_time

[ ! -f $python_v ] &&  echo "===> ERROR: $python_v not found." && exit 1
$python_v /usr/local/lham_agent/lham_agent client >> /var/log/lham_agent.log 2>&1
