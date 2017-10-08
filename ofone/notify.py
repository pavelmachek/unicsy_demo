#!/usr/bin/python3
# -*- python -*-

import sys
sys.path += [ "../maemo" ]

import subprocess
import time
import os
import signal

class MediaPlayer:
    player = 0
    audio = "/my/tui/ofone/audio/"

    def playback_finished(self):
        if not self.player:
            return 1
        if self.player.poll() is None:
            return 0
        return 1

    def mediaPlay(self, file):
        if not self.playback_finished():
            self.player.send_signal(signal.SIGTERM)
        self.player = subprocess.Popen([ 'mplayer', file ], stdin=subprocess.PIPE)

    def mediaPlayPause(self):
        if self.player:
            self.player.send_signal(signal.SIGSTOP)

class NotifyInterface(MediaPlayer):
    def sms(m, event):
        print("Incoming SMS")
        m.mediaPlay(m.audio+"message.mp3")

    def call_incoming(m, number):
        print("Incoming call")
        #droid.m.mediaPlay("/my2/04 Stopa 4.wma")
        m.mediaPlay(m.audio+"ringtone.mp3")

    def end_incoming(m, reason):
        print("Incoming call no longer")
        m.mediaPlayPause()

    def call_starts(m):
        os.system("sudo alsactl restore -f %s/alsa.playback.call" % m.audio)

    def call_ends(m):
        os.system("sudo alsactl restore -f %s/alsa.playback.loud" % m.audio)

if __name__ == "__main__":
    m = MediaPlayer()
    m.mediaPlay(m.audio+"ringtone.mp3")
    time.sleep(5)
    m.mediaPlayPause()

