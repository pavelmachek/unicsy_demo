#!/usr/bin/python2

from __future__ import print_function

import sys
sys.path += [ "/usr/share/unicsy/lib" ]

import time
import os
import hardware
import watchdog

def sy(s):
    os.system(s)

class Startup:
    def __init__(m):
        m.wd = watchdog.StartupWatchdog()

    def run(m):
        print("Unicsy/root starting up")

        wd = m.wd
        debian = hardware.hw.debian

        if debian:
            os.chdir('/my/tui/ofone')

        if hardware.hw.n900:
            # Enable hardware control from non-root, for tefone etc.
            hardware.enable_access('/sys/power/state')
            # keyd needs /dev/input access
            hardware.enable_access('/dev/input/event6')
            hardware.enable_access('/dev/input/event5')
            hardware.enable_access('/dev/input/event1')
            hardware.enable_access('/dev/input/event0')
            
        # power management
        sy('sudo mount /dev/zero -t debugfs /sys/kernel/debug/')
        sy('sudo chmod 755 /sys/kernel/debug')
        hardware.enable_access('/sys/kernel/debug/pm_debug/enable_off_mode')
        # This allows us to configure network. It is also extremely bad idea
        hardware.enable_access('/etc/resolv.conf')

        hardware.hw.startup()

s = Startup()
s.run()

