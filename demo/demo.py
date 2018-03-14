#!/usr/bin/env python2
# -*- python -*-
# Not to be ran as root.

import sys
sys.path += [ "/usr/share/unicsy/lib" ]
import mygtk
mygtk.setup()

import gtk
import os
import rotatable
import hardware
import gobject
import re
import time
import math
import power

# iw dev wlan0 set power_save on
# iw dev wlan0 get power_save

class Power(power.Power):
    pass

if __name__ == "__main__":
    test = Power()
    test.basic_main_window()
    test.tick()
    gtk.main()

