#!/usr/bin/python3

import os
import subprocess

class LockControl:
    def screen_off(m):
        os.system("xscreensaver-command -activate")

    def screen_on(m):
        os.system("xscreensaver-command -deactivate")
