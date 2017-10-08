#!/usr/bin/python

import time
import os

print("Unicsy starting up")
os.system("""
xinput --set-prop --type=float "TSC200X touchscreen" "Coordinate Transformation Matrix"  1.10 0.00 -0.05  0.00 1.18 -0.10  0.00 0.00 1.00
xinput --set-prop --type=int "TSC200X touchscreen" "Evdev Axis Inversion" 0 1
xinput --set-prop --type=float "TSC2005 touchscreen" "Coordinate Transformation Matrix"  1.10 0.00 -0.05  0.00 1.18 -0.10  0.00 0.00 1.00
xinput --set-prop --type=int "TSC2005 touchscreen" "Evdev Axis Inversion" 0 1
xbindkeys -f /my/xbindkeysrc

mate-terminal --tab -t startup -e 'bash -c "/my/tui/ofone/xa"'
""")

#/usr/lib/vino/vino-server &
# (use xvnc4viewer 192.168.1.8 to connect)

time.sleep(10)
print("Unicsy starting up")
time.sleep(10)
print("Unicsy should be done")
