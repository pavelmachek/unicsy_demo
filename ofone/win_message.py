#!/usr/bin/python2
# -*- python -*-
# Not to be ran as root.

import sys
sys.path += [ "/usr/share/unicsy/lib" ]
import mygtk
mygtk.setup()

import gtk
import gobject

import rotatable
import pango

class MessageWindow(rotatable.SubWindow):
    def __init__(m, msg):
        rotatable.SubWindow.__init__(m)
        m.basic_window()
#        m.call_button.set_label(m.middle(msg))
	m.call_button.insert_at_cursor(msg)
        m.window.show_all()

    def interior(m):
        table = gtk.Table(6,6,True)

        buf = gtk.TextBuffer()
        view = gtk.TextView(buf)
        view.modify_font(pango.FontDescription("sans 22"))
        view.set_wrap_mode(gtk.WRAP_WORD)
        scrolled = gtk.ScrolledWindow()
        scrolled.set_policy(gtk.POLICY_AUTOMATIC, gtk.POLICY_AUTOMATIC)
        scrolled.add(view)

#        button.set_line_wrap(True)
        m.call_button = buf
        table.attach(scrolled, 0,6,0,5)

        _, button = m.font_button(m.big("Close"))
        button.connect("clicked", lambda _: m.close())
        table.attach(button, 5,6,5,6)
        return table

if __name__ == "__main__":
    win = MessageWindow("Phones should run similar software computers do, and applications should be portable between the two. Important data should be kept in plain-text file formats.")
    gtk.main()
