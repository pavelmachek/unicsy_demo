#!/bin/bash
(
echo "Unicsy starting up" > /tmp/delme.unicsy.log
cd /home/user
sudo chmod 666 /dev/input/by-path/platform-vibrator-event
#sudo OFONO_AT_DEBUG=1 OFONO_QMI_DEBUG=1 /my/ofono/src/ofonod -n -d -p motmdm,udevng,motorolamodem,atmodem,qmimodem,mail-history,droid,g1 > /home/user/ofonod.log 2>&1 &
#sudo /my/tui/d4/poll_usb  > /home/user/poll_usb.log 2>&1 &

( for i in `seq 100`; do
      echo $i
      sleep .4
      done
      ) | yad --progress --auto-close

GTK2_RC_FILES= /usr/share/unicsy/ofone/ofone -p -s < /dev/null > /tmp/delme.ofono.log 2>&1
) &
