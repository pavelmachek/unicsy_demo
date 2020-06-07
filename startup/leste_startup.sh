#!/bin/bash
cd /home/user

( for i in `seq 100`; do
      echo $i
      sleep .2
      done
      ) | yad --progress --auto-close

/usr/share/unicsy/ofone/ofone -p -s < /dev/null > /tmp/delme.ofono.log 2>&1
