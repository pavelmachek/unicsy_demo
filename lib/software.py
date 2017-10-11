#!/usr/bin/python2
# -*- python -*-

from __future__ import print_function

import math
import time
import os

def sy(s):
    return os.system(s)

class Software:
    def __init__(m):
        pass

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

sw = Software()

if __name__ == "__main__":
    sw.detect()
    print(sw.os_name, sw.os_version, sw.os_version_major, sw.os_version_minor)
