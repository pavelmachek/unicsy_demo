#!/usr/bin/python2

import sys
sys.path += [ "/usr/share/unicsy/lib" ]
import mygtk
mygtk.setup()

import gtk
import os
import pango
import rotatable
import hardware
import gobject
import time
import watchdog

class PhonePanel(rotatable.Panel):
    def bar_button(m, t, t2):
        bu = gtk.Button()
        b = gtk.VBox()
        wl = m.font_label(t)
        b.add(wl)
        wb = gtk.ProgressBar()
        wb.set_fraction(.5)
        wb.set_text(t2)
        b.add(wb)
        bu.add(b)
        return wl, wb, bu
            
    def interior(m):
        m.wd = watchdog.PhoneWatchdog()
        table = gtk.Table(1,12, True)

        # Battery % / voltage -> power settings
        # Signal -> phone settings 
        # Date / time
        # Messages waiting / silent mode
        # Network connection
        # Cpu load? -> running application list.
        # Disk free -> all apps?
        # Button to hide the panel?
        # Weather?
        # Lock screen?
        
        m.signal_text, m.signal_bar, w = m.bar_button("??", "??")
        table.attach(w, 0, 3, 0, 1)

        m.battery_text, m.battery_bar, w = m.bar_button("??", "??")
        table.attach(w, 9, 12, 0, 1)
        
        m.time_label, w1 = m.font_button(m.middle("??")+'\n'+"??")
        table.attach(w1, 8, 9, 0, 1)

        _, w1 = m.font_button(m.middle("^")+'\n'+"hide")
        table.attach(w1, 7, 8, 0, 1)
        w1.connect("clicked", lambda _: m.hide_window())

        _, w1 = m.font_button(m.middle("off")+'\n'+"power")
        table.attach(w1, 6, 7, 0, 1)
        w1.connect("clicked", lambda _: os.system("sudo poweroff"))

        _, w1 = m.font_button(m.middle("lock")+'\n'+"screen")
        table.attach(w1, 5, 6, 0, 1)
        w1.connect("clicked", lambda _: os.system("xscreensaver-command -lock"))

        _, w1 = m.font_button(m.middle("apps")+'\n'+"% disk")
        table.attach(w1, 3, 4, 0, 1)
        w1.connect("clicked", lambda _: os.system("/my/tui/ofone/win_apps.py &"))
 
        _, w1 = m.font_button(m.middle("run")+'\n'+"% cpu")
        table.attach(w1, 4, 5, 0, 1)
        #w1.connect("clicked", lambda _: os.system("xscreensaver -lock")) FIXME: task mgr
 
        #w, w1 = m.font_button(m.middle("wifi")+'\n30%')
        #table.attach(w1, 3, 4, 0, 1)

        #w, w1 = m.font_button(m.middle(".33G")+'\napps')
        #table.attach(w1, 4, 5, 0, 1)

        #w, w1 = m.font_button(m.middle("70%")+'\ncpu')
        #table.attach(w1, 5, 6, 0, 1)

        #w, w1 = m.font_button(m.middle("2")+'\nsms')
        #table.attach(w1, 6, 7, 0, 1)

        #w, w1 = m.font_button(m.middle("11C")+'\nrain')
        #table.attach(w1, 7, 8, 0, 1)

        test.tick()
        return table
        return gtk.Label("foo")

    def hide_window(m):
        m.window.hide()
        for i in range(20):
            gtk.main_iteration()
        time.sleep(5)
        m.window.show_all()



    def tick_time(m):
        if m.time_label:
            dt = time.localtime()
            t = "%d:" % dt.tm_hour + m.middle("%02d" % dt.tm_min)
            t += "\n"
            t += "%d.%d." % (dt.tm_mday, dt.tm_mon)
            m.time_label.set_text(t)
            m.time_label.set_use_markup(True)

    def tick_battery(m):
        b = hardware.hw.battery
        try:
            b.run()
        except:
            b.volt3 = 6.66
            b.perc3 = -666
            b.perc2 = -666
            b.current = -100
            b.status = "Not charging"

        if b.perc2:
            p = b.perc2
            s = ' (hw, %d %%, %2.2fV)' % (b.perc3, b.volt3)
        else:
            p = b.perc3
            s = ' est %2.2fV' % b.volt3            

        s = ('%d%%' % p) + s

        m.battery_text.set_text(s)
        if p > 100: p = 100
        m.battery_bar.set_fraction(p / 100.)

        if b.current > 0:
            m.battery_bar.set_text("Charging %d mA" % b.current)
        else:
            s = "Disch %d mA" % -b.current
            if b.status != "Not charging":
                s += "!!!"
            m.battery_bar.set_text(s)

    def tick_phone(m):
        m.wd.update()
        if False and m.wd.status != "ok":
            m.signal_text.set_text(m.wd.status)
            m.signal_bar.set_text("no signal")
            m.signal_bar.set_fraction(0)
            return
        
        m.signal_text.set_text(m.wd.network)
        m.signal_bar.set_text(m.wd.status)
        m.signal_bar.set_fraction(m.wd.signal / 100.)

    def tick(m):
        print("Tick tock")
        m.tick_battery()
        m.tick_time()
        m.tick_phone()
        gobject.timeout_add(3000, lambda: m.tick())

if __name__ == "__main__":
    test = PhonePanel()
    test.basic_main_window()
    gtk.main()

