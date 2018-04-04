#!/usr/bin/python3
# -*- python -*-
# Not to be ran as root.

import sys
sys.path += [ "/usr/share/unicsy/lib" ]
import mygtk
mygtk.setup()

import gtk
import rotatable

class CallWindow(rotatable.SubWindow):
    def call_started(m, name, number, state):
        m.call_name = name
        m.call_number = number
        m.basic_window()        
        m.call_button.set_label(m.big("Starting call with "+number))
        
    def call_ended(m, name):
        m.hide()
        if name != m.call_name:
            print("Unknown call ended (%s vs %s)" % (name, m.call_name))
        m.call_name = None
        m.call_number = None
        m.call_button.set_label(m.big("Call ended"))
    
    def call_changed(m, name, property, value):
        if name != m.call_name:
            print("Unknown call changed (%s vs %s)" % (name, m.call_name))
        if property == "State" and value == "alerting":
            m.call_button.set_label(m.big("Ringing "+m.call_number))
        if property == "State" and value == "active":
            m.call_button.set_label(m.big("Call with "+m.call_number))
        if property == "State" and value == "disconnected":
            m.call_button.set_label(m.big("Disconnected from "+m.call_number))
            m.call_ended(name)
    
    def interior(m):
        table = gtk.Table(6,6,True)

        button = m.font_label("Call with ... ")
        m.call_button = button
        table.attach(button, 0,6,0,1)

        button = m.font_label("(details)")
        m.call_detail = button
        table.attach(button, 0,6,1,2)

        return table

