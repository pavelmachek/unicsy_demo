#!/usr/bin/python3
# -*- python -*-

import sys
sys.path += [ "../maemo" ]

import android
import time
import os

global droid
droid = android.Android()

class NotifyInterface:
    def sms(m, event):
        print("Incoming SMS")
        droid.mediaPlay("audio/message.mp3")

    def call_incoming(m, number):
        print("Incoming call")
        #droid.mediaPlay("/my2/04 Stopa 4.wma")
        droid.mediaPlay("audio/ringtone.mp3")

    def end_incoming(m, reason):
        print("Incoming call no longer")
        droid.mediaPlayPause()

    def call_starts(m):
        os.system("sudo alsactl restore -f audio/alsa.playback.call")

    def call_ends(m):
        os.system("sudo alsactl restore -f audio/alsa.playback.loud")

def selftest():
    droid.mediaPlay("/my2/04 Stopa 4.wma")
    time.sleep(20)
    droid.mediaPlayPause()

