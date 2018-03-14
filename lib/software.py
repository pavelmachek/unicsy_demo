#!/usr/bin/python2
# -*- python -*-

from __future__ import print_function

import math
import time
import os
import sys

def sy(s):
    return os.system(s)

class Software:
    def __init__(m):
        m.mate = True

    def detect(m):
        m.os_name = "unknown"
        n = '/etc/debian_version'
        if os.path.exists(n):
            m.os_name = "debian"
            v = open(n).readline()
            m.os_version = v[:-1]
            v = m.os_version.split(".")
            m.os_version_major = int(v[0])
            m.os_version_minor = int(v[1])

    def build_command(m, name, cmd):
        if m.mate:
            return  " -t %s -e '%s'" % (name, cmd)
        else:
            return  " -T %s -e '%s'" % (name, cmd)

    def build_script(m, name, cmd):
        return m.build_command(name, 'sh -c "%s; xmessage %s failed; sleep 1h"' % (cmd, cmd))

    def run_terminal(m, cmd2, name="terminal"):
        if m.mate:
            cmd = "mate-terminal "
        else:
            cmd = "xfce4-terminal "

        cmd += m.build_command(name, 'sh -c "%s"' % cmd2)
        print('cmd: ', cmd)
        #cmd += " &"
        os.system(cmd)

    def run_map(m):
        if os.fork() == 0:
            m.run_terminal("/my/tui/lib/client.py -q", "GPS")
            os.system("foxtrotgps")
            sys.exit(0)

sw = Software()

if __name__ == "__main__":
    sw.detect()
    print(sw.os_name, sw.os_version, sw.os_version_major, sw.os_version_minor)
    #sw.run_terminal("/my/tui/lib/client.py -q", "GPS")
    #sw.run_terminal("find /")
    sw.run_map()
