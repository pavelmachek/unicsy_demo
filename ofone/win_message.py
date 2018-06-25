#!/usr/bin/python3
# -*- python -*-
# Not to be ran as root.

import sys
sys.path += [ "/usr/share/unicsy/lib" ]
import mygtk
mygtk.setup()

import gtk
import gobject

import rotatable

class MessageWindow(rotatable.SubWindow):
    def __init__(m, msg):
        rotatable.SubWindow.__init__(m)
        m.basic_window()
        m.call_button.set_label(m.middle(msg))
        m.window.show_all()

    def interior(m):
        table = gtk.Table(6,6,True)

        button = m.font_label("")
        button.set_line_wrap(True)
        m.call_button = button
        table.attach(button, 0,6,0,5)

        _, button = m.font_button("Close")
        button.connect("clicked", lambda _: m.close())
        table.attach(button, 5,6,5,6)
        return table


