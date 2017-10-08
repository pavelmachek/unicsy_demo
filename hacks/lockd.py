#!/usr/bin/python3

from __future__ import print_function

import sys
sys.path += [ "/usr/share/unicsy/lib" ]

import os
import subprocess
import watchdog

class TtyLocker:
    def __init__(m):
        m.wd = watchdog.Watchdog("screen")
        m.lock_tty = 8
        m.l_tty = "/dev/tty%d" % m.lock_tty
        # 2 works for postmarketos
        m.x_tty = 7
        os.system("sudo chmod 666 "+m.l_tty)

    def screen_off(m):
        print("Screensaver activated")
        os.system("sudo chvt %d" % m.lock_tty)
        open(m.l_tty, "w").write("Screen locked")
        os.system("date > "+m.l_tty)
        os.system("echo 1 > /sys/kernel/debug/pm_debug/enable_off_mode")
        os.system("TERM=linux setterm -blank force < %s > %s" % (m.l_tty, m.l_tty))
        os.system("TERM=linux sudo setterm -blank force < %s > %s" % (m.l_tty, m.l_tty))
        m.wd.write("off", "")

    def screen_on(m, complete = True):
        os.system("echo 0 > /sys/kernel/debug/pm_debug/enable_off_mode")
        os.system("sudo chvt %d" % m.x_tty)
        m.wd.write("on", "")
        if complete:
            os.system("xscreensaver-command -deactivate")

    def on_screensaver(m):
        m.screen_off()

    def run_unlock(m):
        while True:
            print("Waiting for enter")
            os.system("read A < %s" % m.l_tty)
            print("Got enter")
            m.screen_on()

    def run(m):
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

if __name__ == "__main__":
    l = TtyLocker()
    if os.fork():
        l.run()
    else:
        l.run_unlock()

    #l.screen_off()
