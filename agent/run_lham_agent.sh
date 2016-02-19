#! /bin/bash

python_v=/usr/bin/python
run_interval=10  #Can be read from config file in future version, in Minutes.


ran_time_set=$(( run_interval * 4 / 5 * 60 ))  #Random seconds, always be 4/5 of $run_interval.
ran_time=$(( RANDOM % ran_time_set )).$(( RANDOM % 1000 )) 

if [ "$1" != "--no-sleep" ]; then
    sleep $ran_time
fi

[ ! -f $python_v ] &&  echo "===> ERROR: $python_v not found." && exit 1
$python_v /usr/local/lham_agent/lham_agent client >> /var/log/lham_agent.log 2>&1
