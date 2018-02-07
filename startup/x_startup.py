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
        print("Unicsy starting up")

        wd = m.wd
        debian = True

        try:
            os.chdir('/my/tui/ofone')
        except:
            debian = False
            print("Not on debian")

        if debian:
            sy('../vfone/win_lock startup &')
            wd.progress(1, "sound")
            sy('sudo ./ztime')
            sy('sudo alsactl restore -f audio/alsa.playback.loud')
            sy('mplayer /my/tui/ofone/audio/message.mp3 &')
            
            os.system("""
xinput --set-prop --type=float "TSC200X touchscreen" "Coordinate Transformation Matrix"  1.10 0.00 -0.05  0.00 1.18 -0.10  0.00 0.00 1.00
xinput --set-prop --type=int "TSC200X touchscreen" "Evdev Axis Inversion" 0 1
xinput --set-prop --type=float "TSC2005 touchscreen" "Coordinate Transformation Matrix"  1.10 0.00 -0.05  0.00 1.18 -0.10  0.00 0.00 1.00
xinput --set-prop --type=int "TSC2005 touchscreen" "Evdev Axis Inversion" 0 1
xbindkeys -f /my/xbindkeysrc
# FIXME
""")

        wd.progress(10, "hardware")
        p = "/usr/share/unicsy/"

        sy("sudo "+p+"startup/root_startup")
        
        # Enable autosleep
        # instructions are at
        # http://lists.infradead.org/pipermail/linux-arm-kernel/2014-April/250019.html

        if debian:
            wd.progress(15, "power management")
            sy('sudo ./run')
            time.sleep(2)

            wd.progress(20, "screensaver")
            sy('xscreensaver &')

        try:
            os.chdir('/my/ofono/test')
        except:
            print("ofono unavailable")

        if debian:
            wd.progress(30, "modem enable")
            sy('./enable-modem')
            time.sleep(1)
            wd.progress(40, "modem online")
            sy('./online-modem')
            time.sleep(1)

        def build_command(name, cmd):
            if m.mate:
                return  " --tab -t %s -e '%s'" % (name, cmd)
            else:
                return  " --tab -T %s -e '%s'" % (name, cmd)

        def build_script(name, cmd):
            return build_command(name, 'bash -c "%s; xmessage %s failed; sleep 1h"' % (cmd, cmd))

        wd.progress(40, "daemons")
        
        # FIXME: some daemons should run as root
        m.mate = True
        if m.mate:
            cmd = "mate-terminal "
        else:
            cmd = "xfce4-terminal "

        pmos_sudo = ""
        if not debian:
            pmos_sudo = "sudo "

        cmd += build_script('1_tefone',  '/my/tui/ofone/tefone')
        cmd += build_script('2_battery', p+'monitor/batmond')
        cmd += build_script('3_monitor', p+'monitor/mond')
        if debian:
            cmd += build_script('4_keys',    p+'hacks/keyd')
        cmd += build_script('5_ofone',   pmos_sudo+p+'ofone/ofone')
        if debian:
            cmd += build_script('6_cmtspeech', '/my/libcmtspeechdata/run')
            cmd += build_script('7_lockd',   p+'hacks/lockd.py')
            cmd += build_script('8_gps3',    '/my/tui/ofone/gps_run')
            cmd += build_script('9_wifi',    '/my/tui/ofone/wifid.py')
        cmd += build_script('0_panel', p+'desktop/panel.py')

#        cmd += build_command('term1', 'bash')
#        cmd += build_command('term2', 'bash')
#        cmd += build_command('term3', 'bash')

        print("Unicsy executing command ", cmd)

        sy(cmd)

        # Allow win_lock to live for a while.
        time.sleep(120000)

s = Startup()
s.run()

#/usr/lib/vino/vino-server &
# (use xvnc4viewer 192.168.1.8 to connect)
