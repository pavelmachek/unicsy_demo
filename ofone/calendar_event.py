#!/usr/bin/python
# -*- python -*-

import sys
sys.path += [ "/usr/share/unicsy/lib" ]
import notify
import win_message

tone = notify.NotifyInterface()
t = sys.argv[1]
a = sys.argv[2]
tone.calendar_event(t, a)
mw = win_message.MessageWindow(t + ": " + a)
mw.main_window = 1
mw.gtk_main()
