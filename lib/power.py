#!/usr/bin/env python2
# -*- python -*-
# Not to be ran as root.

import sys
sys.path += [ "/usr/share/unicsy/lib" ]
import mygtk
mygtk.setup()

import gtk
import os
import rotatable
import hardware
import gobject
import watchdog
import re
import time
import math

# iw dev wlan0 set power_save on
# iw dev wlan0 get power_save

class Power(rotatable.SubWindow):
    def __init__(m):
        rotatable.SubWindow.__init__(m)
        m.monitors = watchdog.AllMonitors()
        m.battery = hardware.hw.battery
        m.time_label = None

    def keyboard_light(m, button, name):
        l = hardware.hw.leds
        if button.get_active():
            l.kbd_backlight(255)
        else:
            l.kbd_backlight(0)

    def back_light(m, button, name):
        l = hardware.hw.backlight
        if button.get_active():
            l.set(255)
        else:
            l.set(100)

    def fast_charge(m, button, name):
        m.battery.fast_charge()

    def monitor_interior(m, table):
        m.battery_monitor = w = gtk.Label("battery")
        table.attach(w, 0,1, 0,3)

        m.worst_monitor = w = gtk.Label("worst")
        table.attach(w, 1,3, 0,3)

        m.phone_monitor = w = gtk.Label("phone")
        table.attach(w, 3,4, 0,3)

    def sensors_interior(m, table):
        m.accel_label = w = gtk.Label("Accel")
        table.attach(w, 0,2, 5,6)

        m.accel_1 = w = gtk.ProgressBar()
        table.attach(w, 2,4, 5,6)
        m.accel_2 = w = gtk.ProgressBar()
        table.attach(w, 2,4, 6,7)
        m.accel_3 = w = gtk.ProgressBar()
        table.attach(w, 0,2, 6,7)

        m.illum_label = w = gtk.Label("Light")
        table.attach(w, 0,2, 7,8)
        m.illum_ired = w = gtk.ProgressBar()
        table.attach(w, 2,4, 7,8)
        m.illum_visible = w = gtk.ProgressBar()
        table.attach(w, 0,4, 8,9)

        w = gtk.Label("Battery")
        table.attach(w, 0,1, 9,10)
        w = gtk.Label("Board")
        table.attach(w, 0,1, 10,11)
        w = gtk.Label("CPU")
        table.attach(w, 0,1, 11,12)

        m.battery_temp_bar = w = gtk.ProgressBar()
        table.attach(w, 1,4, 9,10)
        m.board_temp_bar = w = gtk.ProgressBar()
        table.attach(w, 1,4, 10,11)
        m.cpu_temp_bar = w = gtk.ProgressBar()
        table.attach(w, 1,4, 11,12)

    def main_interior(m):
        table = gtk.Table(15,4,True)

        m.control_buttons(table)

        w = gtk.CheckButton('keyboard\nlight')
        w.connect("toggled", m.keyboard_light, "")
        table.attach(w, 0,1, 3,5)

        w = gtk.CheckButton('backlight')
        w.connect("toggled", m.back_light, "")
        table.attach(w, 1,2, 3,5)

        w = gtk.CheckButton('RGB\nLED')
        m.led_checkbox = w
        table.attach(w, 2,3, 3,5)
        
        #w = gtk.CheckButton('torch\n(impl)')
        #table.attach(w, 2,3, 3,5)

        m.sensors_interior(table)

        _, w = m.font_button(m.big('Close'))
        w.connect("clicked", lambda _: m.hide())

        table.attach(w, 3,4, 0,3)
        return table

    def battery_interior(m, table):
        w = gtk.Label("Battery charge")
        m.battery_text = w
        table.attach(w, 0,4, 3,4)

        w = gtk.ProgressBar()
        m.battery_bar = w
        table.attach(w, 0,4, 4,5)

        w = gtk.Label("Current [mA]")
        m.current_text = w
        table.attach(w, 0,4, 5,6)
            
        w = gtk.ProgressBar()
        m.current_bar = w
        table.attach(w, 0,4, 6,7)

        w = gtk.Label("(status text)")
        m.status_text = w
        table.attach(w, 0,4, 7,15)

    def audio_test(m):
        hardware.hw.audio.mixer_ringing()
        os.system( 'aplay -D plughw:CARD=Audio,DEV=0 /usr/share/unicsy/tones/fallback.wav' )

    def control_buttons(m, table):
        _, w = m.big_button('Re', 'start')
        w.connect("clicked", lambda _: os.system("sudo /sbin/reboot"))
        table.attach(w, 0,1, 0,3)

        _, w = m.big_button('off', 'power')
        w.connect("clicked", lambda _: os.system("sudo shutdown -h now"))
        table.attach(w, 1,2, 0,3)
        
        _, w = m.big_button('Fast', 'charge')
        w.connect("clicked", m.fast_charge, "")
        table.attach(w, 2,3, 0,3)


        _, w = m.big_button('Audio', 'play')
        w.connect("clicked", lambda _: os.system("aplay /usr/share/sounds/alsa/Front_Center.wav"))
        table.attach(w, 0,1, 12,15)
        
        _, w = m.big_button('Vibra', 'tions')
        w.connect("clicked", lambda _: hardware.hw.vibrations.on(.30))
        table.attach(w, 1,2, 12,15)
        
        _, w = m.big_button('Tefone', 'tests')
        w.connect("clicked", lambda _: os.system("mate-terminal -e /usr/share/unicsy/demo/tefone &"))
        table.attach(w, 2,3, 12,15)

        _, w = m.big_button('Audio', 'test')
        w.connect("clicked", lambda _: m.audio_test())
        table.attach(w, 3,4, 12,15)
        
    def aux_interior(m):
        table = gtk.Table(15,4,True)
        m.battery_interior(table)
        m.monitor_interior(table)
        return table

    def tick_alerts(m):
        m.monitors.update_alerts()
        m.battery_monitor.set_text( "battery\n"+m.monitors.worst_from(m.monitors.alerts_on["battery"]).key )
        m.phone_monitor.set_text( "phone\n"+m.monitors.worst_from(m.monitors.alerts_on["phone"]).key )
        a = m.monitors.worst_alert()
        s = a.short
        s = re.sub(" ", "\n", s)
        if a.priority >= 9:
            m.worst_monitor.set_text("")
        elif a.priority >= 5:
            m.worst_monitor.set_text(s)
        else:
            m.worst_monitor.set_text(s)
            m.worst_monitor.set_use_markup(True)

    def tick_battery(m):
        b = m.battery
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

        s = ('Battery %d%%' % p) + s

        m.battery_text.set_text(s)
        if p >= 0 and p <= 100.:
            m.battery_bar.set_fraction(p / 100.)
        else:
            m.battery_bar.set_fraction(1.)            

        if b.current > 0:
            m.current_text.set_text("Charging at %d mA, limits %d / %d mA" % (b.current, b.max_battery_current, b.charger_limit))
            if mygtk.is3:
                m.current_bar.set_inverted(False)
            if b.current >= 0 and b.current < 650.:
                m.current_bar.set_fraction(b.current / 650.)
            else:
                m.current_bar.set_fraction(1.)
        else:
            s = "Discharging at %d mA" % -b.current
            if b.status != "Not charging":
                s += ", status " + b.status
            m.current_text.set_text(s)
            if mygtk.is3:
                m.current_bar.set_inverted(True)
            m.current_bar.set_fraction(-b.current / 650.)

    def tick_status_text(m):
        s = ''
        s += '' + ''.join(os.popen("date").readlines())
        s += 'kernel ' + ''.join(os.popen("uname -r").readlines())
        #s += ''.join(os.popen("/my/ofono/test/list-operators | grep Name").readlines())
        s += ''.join(os.popen("uname -r").readlines())
        #s += ''.join(os.popen("/sbin/ifconfig | grep -1 wlan0 | sed 's/Link.*//' | sed 's/Bcast.*//'").readlines())
        #s += ''.join(os.popen("calendar -f ~/bin/calendar").readlines())
        #s += ''.join(os.popen("/sbin/ifconfig | grep -1 usb0 | sed 's/Link.*//' | sed 's/Bcast.*//'").readlines())
        #s += ''.join(os.popen("/sbin/ifconfig | grep -1 wlan0 | sed 's/Link.*//' | sed 's/Bcast.*//'").readlines())
        #s += 'debian ' + ''.join(os.popen("cat /etc/debian_version").readlines())
        s += 'alpine ' + ''.join(os.popen("cat /etc/alpine-release").readlines())

        m.status_text.set_text(s)

    def tick_time(m):
        if m.time_label:
            dt = time.localtime()
            t = "%d:%02d" % (dt.tm_hour, dt.tm_min)
            t = m.big(t)
            t += "\n"
            t += "%d.%d.%d" % (dt.tm_mday, dt.tm_mon, dt.tm_year)
            m.time_label.set_text(t)
            m.time_label.set_use_markup(True)

    def update_temperature(m, bar, temp):
        bar.set_text("%.1f C" % temp)
        f = (temp - 20.) / 60.
        if f < 0: f = 0
        if f > 1: f = 1
        bar.set_fraction(f)

    def tick_sensors(m):
        def xlog(v):
            if v < 0.1:
                return 0
            return math.log(v)

        illum = hardware.hw.light_sensor
        v = illum.get_illuminance()
        i = illum.get_ired_raw()
        m.illum_label.set_text("Light %d ired %d" %
                               (v, i) )
        m.illum_ired.set_fraction(xlog(i)/20)
        m.illum_visible.set_fraction(xlog(v)/20)

        accel = hardware.hw.accelerometer
        x, y, z = accel.position()

        m.accel_label.set_text("Accel %.2f %.2f %.2f" % (x, y, z))
        m.accel_1.set_fraction(abs(x)/1.3)
        m.accel_2.set_fraction(abs(y)/1.3)
        m.accel_3.set_fraction(abs(z)/1.3)

        temp = hardware.hw.temperature
        m.update_temperature(m.board_temp_bar, temp.read_board_temp())
        m.update_temperature(m.battery_temp_bar, temp.read_battery_temp())
        m.update_temperature(m.cpu_temp_bar, temp.read_cpu_temp0())

    def tick_rgb(m):
        if m.led_checkbox.get_active():
            accel = hardware.hw.accelerometer
            val = map(lambda x: abs(x)*250, accel.position())
            hardware.hw.led.set(val)

    def tick(m):
        m.tick_alerts()
        m.tick_battery()
        m.tick_status_text()
        m.tick_sensors()
        m.tick_rgb()

        m.time_tick = gobject.timeout_add(3000, lambda: m.tick())

    def show(m):
        rotatable.SubWindow.show(m)
        m.tick()

    def hide(m):
        rotatable.Subwindow.hide(m)
        gobject.source_remove(m.time_tick)

if __name__ == "__main__":
    test = Power()
    test.basic_main_window()
    test.tick()
    gtk.main()

