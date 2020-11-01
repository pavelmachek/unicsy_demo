#!/usr/bin/python
# -*- python -*-

import sys
sys.path += [ "/usr/share/unicsy/lib" ]

import subprocess
import time
import os
import signal
import hardware

class MediaPlayer:
    def __init__(m):
        m.player = 0
        if False:
            m.audio = "/my/tui/ofone/audio/"
            m.play_cmd = [ 'mplayer' ]
        else:
            if True:
                m.audio = "/usr/share/unicsy/tones/"
                m.t_ring = "CALL.wav"
                m.t_sms = "SMS.wav"
                m.t_alarm = "ALARM.wav"
                m.t_fallback = "fallback.wav"
            else:
                m.audio = "/usr/share/sounds/"
                m.t_ring = "ui-wake_up_tune.wav"
                
            m.play_cmd = [ '/usr/bin/aplay' ]
            if hardware.hw.d4:
                m.play_cmd += [ '-D', 'plughw:CARD=Audio,DEV=0' ]

    def playback_finished(m):
        if not m.player:
            return 1
        if m.player.poll() is None:
            return 0
        return 1

    def mediaPlay(m, file):
        if not m.playback_finished():
            m.player.send_signal(signal.SIGTERM)
        null = open('/dev/null', 'r+')
        m.player = subprocess.Popen(m.play_cmd + [ file ], stdin=subprocess.PIPE, stdout=null, stderr=null, shell=False, cwd=None, env=None)

    def mediaPlayPause(m):
        if m.player:
            m.player.send_signal(signal.SIGSTOP)

class NotifyInterface(MediaPlayer):
    def start_notify(m, detail, t):
        #m.mediaPlay(m.audio+"message.mp3")
        hardware.hw.vibrations.run_bg()
        hardware.hw.audio.mixer_ringing()
        if detail == "sms":
            m.mediaPlay(m.audio+m.t_sms)
        elif detail == "calendar":
            m.mediaPlay(m.audio+m.t_alarm)
        elif detail == "call":
            m.mediaPlay(m.audio+m.t_ring)
        else:
            m.mediaPlay(m.audio+m.t_fallback)
            
    def stop_notify(m, detail):
        m.mediaPlayPause()
        
    def sms(m, event):
        print("Incoming SMS")
        m.start_notify("sms", event)

    def calendar_event(m, title, detail):
        print("Calendar event")
        m.start_notify("calendar", (title, detail))

    def call_incoming(m, number):
        print("Incoming call")
        #m.mediaPlay(m.audio+"ringtone.mp3")
        m.start_notify("call", number)

    def end_incoming(m, reason):
        print("Incoming call no longer")
        m.stop_notify(reason)

    def call_starts(m):
        hardware.hw.audio.mixer_call()

    def call_ends(m):
        hardware.hw.audio.mixer_ringing()

if __name__ == "__main__":
    m = MediaPlayer()
    hardware.hw.vibrations.run_bg()
    hardware.hw.audio.mixer_ringing()
    m.mediaPlay(m.audio+m.t_ring)
    time.sleep(5)
    m.mediaPlayPause()

