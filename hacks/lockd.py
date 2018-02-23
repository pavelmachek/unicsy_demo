#!/usr/bin/python3

from __future__ import print_function

import sys
sys.path += [ "/usr/share/unicsy/lib" ]

import os
import subprocess
import watchdog

class Locker:
    def __init__(m):
        m.wd = watchdog.Watchdog("screen")

    def screen_off(m):
        os.system("echo 1 > /sys/kernel/debug/pm_debug/enable_off_mode")
        m.wd.write("off", "")

    def screen_on(m, complete = True):
        os.system("echo 0 > /sys/kernel/debug/pm_debug/enable_off_mode")
        m.wd.write("on", "")

    def on_screensaver(m):
        m.screen_off()

    def run_loop(m):
        events = subprocess.Popen(["xscreensaver-command", "-watch"], bufsize=1, stdout=subprocess.PIPE)
        while True:
            l = events.stdout.readline()
            print("Got event", l)
            l = str(l)
            split = l.split(" ")
            if split[0] == "b'BLANK":
                m.on_screensaver()
            elif split[0] == "b'LOCK":
                m.on_screensaver()
            elif split[0] == "b'UNBLANK":
                m.screen_on(False)
            else:
                print("Got unknown event, ", split[0])

class TtyLocker(Locker):
    def __init__(m):
        Locker.__init__(m)
        m.lock_tty = 8
        m.l_tty = "/dev/tty%d" % m.lock_tty
        # 2 works for postmarketos
        m.x_tty = 7
        os.system("sudo chmod 666 "+m.l_tty)

    def screen_off(m):
        print("Screensppppaver activated")
        os.system("sudo chvt %d" % m.lock_tty)
        open(m.l_tty, "w").write("Screen locked")
        os.system("date > "+m.l_tty)
        os.system("TERM=linux setterm -blank force < %s > %s" % (m.l_tty, m.l_tty))
        os.system("TERM=linux sudo setterm -blank force < %s > %s" % (m.l_tty, m.l_tty))
        Locker.screen_off(m)

    def screen_on(m, complete = True):
        Locker.screen_on(m)
        os.system("sudo chvt %d" % m.x_tty)
        if complete:
            os.system("xscreensaver-command -deactivate")

    def run_unlock(m):
        while True:
            print("Waiting for enter")
            os.system("read A < %s" % m.l_tty)
            print("Got enter")
            m.screen_on()

    def run(m):
        if os.fork():
            m.run_loop()
        else:
            m.run_unlock()

class XLocker(Locker):
    def __init__(m):
        Locker.__init__(m)

    def screen_off(m):
        Locker.screen_off(m)
        os.system('xinput set-prop "TSC2005 touchscreen" "Device Enabled" 0')

    def screen_on(m, complete = True):
        Locker.screen_on(m)
        os.system('xinput set-prop "TSC2005 touchscreen" "Device Enabled" 1')
        if complete:
            os.system("xscreensaver-command -deactivate")

    def run(m):
        m.run_loop()

if __name__ == "__main__":
    #l = TtyLocker()
    l = XLocker()
    l.run()
    #l.screen_off()
