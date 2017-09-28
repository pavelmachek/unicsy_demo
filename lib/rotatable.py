#!/usr/bin/env python3

import sys
sys.path += [ "../maemo" ]
import mygtk
mygtk.setup()

import gtk
import os
import pango

# On N900, when used by single hand, right portion of screen is usable
# in horizontal mode, and whole screen is usable in vertical mode,
# with bottom portions maybe being slightly easier to access.

class TouchWidgets:
    def __init__(m):
        pass

    def big(m, s):
        return '<span size="xx-large">%s</span>' % s

    def middle(m, s):
        return '<span size="x-large">%s</span>' % s
    
    def small(m, s):
        return '<small>%s</small>' % s

    def font_label(m, s):
        w = gtk.Label(s)
        w.set_use_markup(True)
        return w
        
    def font_button(m, s):
        w = m.font_label(s)
        w1 = gtk.Button()
        w1.add(w)
        return w, w1

    def font_entry(m, size = 32, font=""):
        e = gtk.Entry()
        e.modify_font(pango.FontDescription("sans "+str(size)))
        return e

class Rotatable(TouchWidgets):
    def __init__(m):
        TouchWidgets.__init__(m)
        m.vertical = 0
        if os.getenv("VERTICAL"):
            m.vertical = 1
        m.main_window = 0
        m.window = None

    def aux_interior(m):
        table = gtk.Table(4,4,True)
        return table

    def main_interior(m):
        table = gtk.Table(4,4,True)
        return table

    def interior(m):
        if not m.vertical:
            table = gtk.Table(1,2,True)
            table.attach(m.aux_interior(), 0,1,0,1)
            table.attach(m.main_interior(), 1,2,0,1)
        else:
            table = gtk.Table(2,1,True)
            table.attach(m.aux_interior(), 0,1,0,1)
            table.attach(m.main_interior(), 0,1,1,2)
        return table
    
    def basic_window(m):
        window = gtk.Window(gtk.WINDOW_TOPLEVEL)
        if not m.vertical:
            window.set_default_size(800, 400)
        else:
            window.set_default_size(400, 800)
        window.set_border_width(3)
        m.window = window
        table = m.interior()

        window.add(table)
        window.show_all()
        m.window.connect("delete-event", lambda _, _1: m.hide())

    def show(m):
        if m.window:
            m.window.show_all()
            return
        m.basic_window()

    def hide(m):
        print("Hiding window")
        if m.main_window:
            gtk.main_quit()
        m.window.hide()
        return True

    def basic_main_window(m):
        m.basic_window()
        m.main_window = 1

class TestWindow(Rotatable):
    sx = 5
    sy = 6

    def test_interior(m):
        table = gtk.Table(m.sx,m.sy,False)
        for x in range(m.sx):
            for y in range(m.sy):
                w = gtk.Label('<span size="xx-large">%d</span> %d\n<small>foo</small>' % (x,y))
                w.set_use_markup(True)
                w1 = gtk.Button()
                w1.add(w)
                table.attach(w1, x, x+1, y, y+1)
        
        return table
    
    def main_interior(m):
        return m.test_interior()

    def aux_interior(m):
        return m.test_interior()

class SubWindow(Rotatable):
    def dial(m):
        print("Should dial ", m.number)

if __name__ == "__main__":
    test = TestWindow()
    test.basic_main_window()
    gtk.main()
