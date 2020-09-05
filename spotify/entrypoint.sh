#!/bin/bash

uid=$1
re='^[0-9]+$'

if [ -z $uid ]; then
  uid=1000
elif [[ ! $uid =~ $re ]]; then
  echo "error: Invalid user uid: $uid"
  exit 1
fi

useradd -u $uid -m -G games,lock,network,users,video,uucp,storage,optical,input,disk,audio -s /bin/bash docker

sudo -i -u docker PULSE_SERVER=/run/pulse/native spotify
