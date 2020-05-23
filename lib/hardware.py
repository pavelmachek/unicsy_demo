#!/usr/bin/python2
# -*- python -*-

# Vibrations need "joystick" package

from __future__ import print_function

import math
import time
import os
import sys

def sy(s):
    return os.system(s)

def enable_access(s):
    # This is getting _lists_ of names, so chown is not easy
    #sy("sudo chown $USER "+s)
    # 666 does not work well, as someone uses it on directories?!
    sy("sudo chmod 777 "+s)

class Test:
    def write(m, s, v):
        f = open(s, "w")
        f.write(v)
        f.close()

    def write_root(m, s, v):
        enable_access(s)
        return m.write(s, v)

    def read(m, s):
        if not os.path.exists(s):
            return None
        f = open(s, "r")
        try:
            r = f.read()
        except:
            # Sometimes file exist but read returns error.
            # cat time_to_full_now
            # cat: time_to_full_now: No data available
            return None
        f.close()
        return r

    def read_int(m, s):
        v = m.read(s)
        if v is None:
            return -1
        return int(v)

    def startup(m):
        pass

    def probe(m):
        pass

    def probe_paths(m, b, l):
        for p in l:
            if os.path.exists(b+p):
                return b+p

class Battery(Test):
    hotkey = "b"
    name = "Battery"

    def probe(m):
        m.battery_full = None
        m.battery_empty = None
        m.battery_35V = None        
        m.battery_4V = None
        m.charge_now = None
        m.design_full_V = 4.2
        # N900 has 1320mAh battery.
        if m.hw.d4:
            m.design_full_V = 4.35
        m.battery = m.probe_paths("/sys/class/power_supply/",
                                  [ 'bq27200-0', 'bq27521-0', 'tcpm-source-psy-0-0052', 'battery' ])
        m.charger = m.probe_paths("/sys/class/power_supply/",
                                  [ 'bq24150a-0', 'bq24153-0', 'bq25890-charger', 'usb' ])

    def percent_to_42v(m, v):
        u = 0.0387-(1.4523*(3.7835-v))
        if u < 0:
            return max(  ((v - 3.3) / (3.756 - 3.300)) * 19.66, 0) 
        return 19.66+100*math.sqrt(u)

    def percent(m, v):
        return 100*m.percent_to_42v(v)/m.percent_to_42v(m.design_full_V)

    def fmt(m, v):
        if v is None:
            return "???"
        return "%d" % v

    def guess_charge(m, known_val, known_perc, capacity):
        if known_val:
            c_4 = m.charge_now - known_val + known_perc * capacity
            c_4p = (100 * c_4) / capacity
            return ("capacity %.0f mAh cap %s mAh %s %%" %
        	    (capacity, m.fmt(c_4), m.fmt(c_4p)))

        return ""

    def run(m):
        volt = m.read_int(m.battery+"/voltage_now") / 1000000.
        perc = m.percent(volt)
        
        status = m.read(m.charger+"/status")[:-1]
        b_status = m.read(m.battery+"/status")[:-1]

        current = m.read_int(m.charger+"/charge_current")
        limit = m.read_int(m.charger+"/current_limit")

        charge_now = m.read_int(m.battery+"/charge_now") / 1000
        charge_full = m.read_int(m.battery+"/charge_full") / 1000
        if charge_now < 0:
            charge_now = -m.read_int(m.battery+"/charge_counter") / 1000

        if b_status == "Full":
            m.battery_full = charge_now
        if b_status == "Empty": # FIXME: this will never trigger on d4
            if not m.battery_empty:
                m.battery_empty = m.charge_now # Take _previous_ value
            elif m.battery_empty < charge_now:
                # And we don't want to overwrite it with hardware value
                # realizing battery is now empty
                m.battery_empty = m.charge_now
            

        #perc2 = m.read_int(m.battery+"/capacity")
        # Buggy in v4.4
        perc2 = 0
        if charge_full >= 0:
            perc2 = int((charge_now * 100.) / charge_full)

        charge_design = m.read_int(m.battery+"/charge_full_design") / 1000
        # FIXME: volt2 from the other sensor on N900?
        volt2 = volt
        current2 = m.read_int(m.battery+"/current_now") / 1000.
        current_avg = m.read_int(m.battery+"/current_avg") / 1000.
        charge_counter = m.read_int(m.battery+"/charge_counter") / 1000.

        if m.battery_35V is None and volt < 3.5:
            m.battery_35V = charge_now
        if volt < 3.5 and charge_now > m.battery_35V:
            m.battery_35V = charge_now
        
        if m.battery_4V is None and volt > 4.:
            m.battery_4V = charge_now
        if volt > 4. and charge_now < m.battery_4V:
            m.battery_4V = charge_now

        # http://www.buchmann.ca/Chap9-page3.asp
        # 0.49 ohm is between "poor" and "fail".
        # 0.15 ohm is between "excelent" and "good".
        # at 3.6V.
        if m.hw.n900:
            resistance = 0.33 # Suitable for old N900
        else:
            resistance = 0.08
        volt3 = volt + (current2 / 1000. * resistance)
        perc3 = m.percent(volt3)

        print("Battery (%.2fV) %.2fV" % (volt, volt3), \
              "(%d%%) %d%% %d%%" % (int(perc), int(perc3), perc2), \
              "%d/%d mAh" % (charge_now, charge_full), \
              status, b_status, \
              "%d %d %d/%d mA" % (int(-current2), int(-current_avg), current, limit),
              "%s %d %s mAh" % (m.fmt(m.battery_empty), charge_now, m.fmt(m.battery_full)),
              file=sys.stderr )
        m.perc = perc
        m.perc2 = perc2
        m.perc3 = perc3
        m.volt = volt
        m.volt2 = volt2
        m.volt3 = volt3
        m.b_status = b_status
        m.status = status
        m.current = -current2 # >0 : charging
        m.current_avg = -current_avg
        m.charge_counter = -charge_counter # increases: charging
        m.charge_now = charge_now
        m.max_battery_current = current
        m.charger_limit = limit

    def wall(m, s):
        os.system("echo %s | wall" % s)

    def shutdown(m, s):
        os.system("sudo /sbin/shutdown -h now")
        m.wall(s)
        
    def handle_protect(m):
        # N900:
        # Battery 3.14V 3.23V 3.33V 0% 0% 35% 632/1797 mAh Not charging -454/650/100 mA
        # Battery 3.16V 3.19V 3.34V 0% 0% 6% 111/1797 mAh Not charging -423/650/100 mA
        # Battery 2.94V 3.04V 3.13V 0% 0% 5% 97/1797 mAh Not charging -454/650/100 mA
        # Battery 2.88V 2.98V 3.09V 0% 0% 5% 96/1797 mAh Not charging -481/650/100 mA
        # Battery 2.88V 2.96V 3.08V 0% 0% 5% 93/1797 mAh Not charging -476/650/100 mA
        # Battery 2.82V 2.90V 3.04V 0% 0% 5% 91/1797 mAh Not charging -511/650/100 mA

        # N900:
        # Shutdown at 2.95V / 3.15V was too late -- system could not boot up next time.
        # Shutdown at 3.20V / 3.40V seems to be too early -- system shuts down with > 60% battery.
        # At steady state, 3.2V / 3.4V seems to be right point. Voltage goes steadily down, quickly, at that moment

        s = None
        
        raw_warn, adj_warn, raw_shut, adj_shut = 3.40, 3.50, 3.30, 3.40
        if hw.n900:
            raw_warn, adj_warn, raw_shut, adj_shut = 3.20, 3.40, 3.16, 3.30

        if m.volt < raw_warn:
            m.wall("Raw voltage low, warning")
            s = "warning"
        if m.volt3 < adj_warn:
            m.wall("Adjusted voltage low, warning")
            s = "warning"            

        if m.volt < raw_shut:
            m.shutdown("Raw voltage low, shutdown")
            s = "critical"
        # When transitioning from charger to battery discharge, ampermeter
        # lags behind, and produces < 3.55V for a while
        if m.volt3 < adj_shut:
            m.shutdown("Adjusted voltage low, shutdown")
            s = "critical"
        return s
        

    def summary(m):
        if m.volt < 3.3:
            return "critical"
        if m.status == "Charging":
            if m.volt2 > 4.100 and m.current > -35 and m.current < 40:
                return "full"
            if m.current > 0:
                return "charging"
            return "discharging"
        if m.perc3 < 30:
            return "low"
        return "ok"

    def fast_charge(m, limit=1800):
        sy("echo %d > %s/current_limit" % (limit, m.charger))
        print("Fast charge on, %d mA" % limit)

    def startup(m):
        if m.hw.n900:
            # Disable yellow battery light:
            m.write_root(m.charger+'/stat_pin_enable', '0')
            # Enable charger control from non-root
            enable_access(m.charger+'/current_limit')
            m.fast_charge(500)
        if m.hw.d4:
            #m.write_root(m.charger + "/constant_charge_current", "532000")
            #m.write_root(m.charger + "/constant_charge_voltage", "4100000")
            m.write_root(m.charger + "/charge_control_limit", "0")

class ChargeBattery(Battery):
    hotkey = "B"
    name = "chargeBattery"

    def run(m):
        m.fast_charge()

class LED(Test):
    def set_bright(m, s, v):
        f = open(m.path + s + "/brightness", "w")
        f.write(str(int(v*m.scale)))
        f.close()

class Torch(LED):
    hotkey = "o"
    name = "Torch"
    path = "/sys/class/leds/led-controller:"
    scale = 1.0

    def set(m, val):
        m.set_bright("flash", val)

    def set_indicator(m, val):
        m.set_bright("indicator", val)

    def run(m):
        vals = (0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 20, 30, 40, 50, 0)
        for v in vals:
            m.set(v)
            m.set_indicator(255)
            time.sleep(.3)
            m.set_indicator(0)
            time.sleep(.3)


class LEDs(LED):
    hotkey = "l"
    name = "LEDs"
    scale = 0.1

    def __init__(m):
        m.white = ''
        m.path = ''
        m.short = False

    def probe(m):
        m.path='/sys/class/leds/'
        if os.path.exists(m.path+"status-led"):
            m.white = "status-led"
        if os.path.exists(m.path+"lp5523:r"):
            m.path += "lp5523:"
            m.short = True
        if os.path.exists(m.path+"status-led:red"):
            m.path += "status-led:"
            m.short = False

    def startup(m):
        enable_access(m.path+"*/brightness")

    # D4 has also:
    # /sys/class/leds/button-backlight
    # for touchscreen buttons.

    def set(m, val):
        (r, g, b) = val
        if m.white:
            m.set_bright(m.white, (r+g+b)/3)
        if m.short:
            m.set_bright("r", r)
            m.set_bright("g", g)
            m.set_bright("b", b)
        else:
            m.set_bright("red", r)
            m.set_bright("green", g)
            m.set_bright("blue", b)

    def kbd_backlight(m, val):
        if m.hw.n900:
            for i in range(1, 7):
                m.set_bright("kb%d" % i, val)

    def all_off(m):
        m.set( (1, 1, 1) )
        m.kbd_backlight(1)
        m.set( (0, 0, 0) )
        m.kbd_backlight(0)

    def run(m):
        vals = ((255, 255, 0),
                (255, 0, 0),
                (0, 0, 180),
                (255, 118, 0),
                (0, 154, 37),
                (0, 0, 0))
        for v in vals:
            m.set(v)
            m.kbd_backlight(0)
            time.sleep(.3)
            m.kbd_backlight(255)

class AccelLED(LEDs):
    hotkey = "L"
    name = "accelLed"
    a_path = "/sys/class/i2c-adapter/i2c-2/2-0032/"
    fw_path = "/sys/class/firmware/lp5523/"

    led_kb = 0x111100011
    blue =   0x000010000
    green =  0x000001000
    red =    0x000000100

    def program_engine_new(m, eng, leds, program):
        m.write(m.a_path + "select_engine", str(eng))
        m.write(m.fw_path + "loading", "1")
        m.write(m.fw_path + "data", program)
        m.write(m.fw_path + "loading", "0")
        m.write(m.a_path + "run_engine", str(eng))

    def program_engine(m, eng, leds, program):
        m.write(m.a_path + "engine%d_mode" % eng, "load")
        m.write(m.a_path + "engine%d_load" % eng, program)
        m.write(m.a_path + "engine%d_leds" % eng, "%09x" % leds)
        m.write(m.a_path + "engine%d_mode" % eng, "run")

    def disable_engine(m, eng):
        m.write(m.a_path + "engine%d_mode" % eng, "disabled")

    def run(m):
        m.all_off()
        m.program_engine(1, m.blue, "9d8040ff7e0040007e00a001")

    def all_off(m):
        for eng in range(1,4):
            m.disable_engine(eng)
        LEDs.all_off(m)

    def startup(m):
        enable_access("/sys/class/i2c-adapter/i2c-2/2-0032/*")

class Backlight(Test):
    hotkey = "c"
    name = "baCklight"
    scale = 0.1

    def probe(m):
        m.path = "/sys/class/backlight/"
        p = os.listdir(m.path)
        if p:
            m.path += p[0]
            m.path += "/brightness"

    def startup(m):
        enable_access(m.path)

    def n900_to_d4(m, val):
        if val < 2:
            return 0
        r = math.log(val) / math.log(2)
        r = r*20 + 50
        return int(r)

    def set(m, i):
        if m.hw.d4:
            i = m.n900_to_d4(i)
        if i < 0:
            i = 255
        if i > 255:
            i = 255
        m.write(m.path, str(i))

    def run(m):
        m.write(m.path, "0")        
        i = 1
        while i < 255:
            m.set(i)
            i *= 2
            time.sleep(.3)

class LightSensor(Test):
    hotkey = "i"
    name = "lIght_sensor"

    def probe(m):
        m.directory = m.probe_paths( "/sys/bus/i2c/drivers",
                                [ "/tsl2563/2-0029/iio:device1/",
                                  "/isl29028/1-0044/iio:device1/",
                                  "/isl29028/1-0044/iio:device2/" ] )
        if not m.directory:
            m.directory = "/dev/zero/no"
        if m.directory:
            m.path = m.directory + "in_illuminance"
            if os.path.exists( m.path + "0_input" ):
                m.path += "0"

    def get_illuminance(m):
        scale = m.read_int(m.path + "_scale")
        val = m.read_int(m.path + "_input")
        if scale == -1:
            return val
        else:
            return int( (2000.*3.5*val)/scale )

    def get_ired_raw(m):
        return m.read_int(m.directory + "in_intensity_both_raw")

    def run(m):
        i = 0
        while i < 10:
            print("Light sensor says", m.get_illuminance())
            i += 1
            time.sleep(1)

class LightSettings:
    def __init__(m, backlight, keyboard, name, led_scale = 0.2):
        m.backlight = backlight
        m.keyboard = keyboard
        m.led_scale = led_scale
        m.name = name

class LightAdjustment:
    def __init__(m):
        m.lightSensor = hw.light_sensor
        m.backlight = hw.backlight
        m.keyboard = hw.leds
        m.very_dark = LightSettings(6, 180, "very dark", 0.01)
        m.dark_in_dark_room = LightSettings(8, 180, "dark in dark room", 0.05)
        m.somehow_dark_room = LightSettings(10, 180, "somehow dark room", 0.05)
        m.dark_room = LightSettings(20, 255, "dark room", 0.1)
        m.night_room = LightSettings(40, 10, "night room", 0.1)
        m.cloudy_day_room = LightSettings(128, 10, "cloudy day room", 0.1)
        m.sunlight = LightSettings(99999, 10, "sunlight")
        m.error = LightSettings(255, 255, "error")

        m.sleep_test = LightSettings(128, 10, "sleep test", 0.1)

    def get_settings(m):
        try:
            illum = m.lightSensor.get_illuminance()
            ired = m.lightSensor.get_ired_raw()
        except:
            return m.error
        print("Illuminance ", illum, "ired", ired)
        if illum == 0:
            if ired == 0:
                return m.very_dark
            if ired < 5:
                return m.dark_in_dark_room
            return m.somehow_dark_room
        if illum < 5:
            return m.dark_room
        if illum < 20:
            return m.night_room
        if illum < 100:
            return m.cloudy_day_room
        # 950 ... sunny day, inside room
        # 10000..100000, ired 324000 ... direct sun
        return m.sunlight
        
    def run(m, is_test, is_active = True, is_open = True):
        if not is_test:
            now = m.get_settings()
        else:
            now = m.sleep_test
        m.now = now
        print(now.name)

        keyboard = now.keyboard
        backlight = now.backlight

        if not (is_active and is_open):
            keyboard = 0

        # kernel automatically turns off the backlight, no need to do it here

        m.keyboard.kbd_backlight(keyboard)
        m.backlight.set(backlight)
        print("keyboard/backlight", keyboard, backlight, "active", is_active, is_open)

class Vibrations(Test):
    hotkey = "v"
    name = "Vibrations"

    def probe(m):
        m.path = m.probe_paths("/dev/input/by-path/",
                               [ "platform-vibrator-event",
                                 "platform-48070000.i2c-platform-twl4030-vibra-event" ])
    def startup(m):
        enable_access(m.path)
    
    def on(m, t):
        print("fftest at ", m.path)
        # fftest on N900 can not handle "too long" paths.
        sy("(echo 5; sleep %f; echo -1) | fftest /proc/self/fd/3 3< %s" % (t, m.path))

    def run(m):
        m.on(.15)

class Audio(Test):
    hotkey = "a"
    name = "Audio"

    def say(m, s):
        sy("echo '%s' | sh -c 'time festival --tts'" % s)

    def run(m):
        print("Running festival")
        m.mixer_ringing()
        m.say('Come shall then well bload? Then well bload shell when blaight!')
        m.mixer_call()
        m.say('This is phone call test. Does it work?')
        m.mixer_headphones()
        m.say('Headphones. I hope you have them connected.')
        m.mixer_ringing()

        # amixer set PCM 100
        # 10%+
        # amixer -D pulse sset Master mute
        # pactl set-sink-volume 0 100% 
        # pactl should allow above 100%

    def volume_change(m, v):
        if v > 0:
            s = "%d%%+" % v
        else:
            s = "%d%%-" % -v
        sy("sudo amixer set PCM " + s)

    def set_mixer(m, name):
        #sy("sudo alsactl restore -f /usr/share/unicsy/audio/nokia-n900/alsa.playback." + name)
        sy("sudo alsactl restore -f /usr/share/unicsy/audio/"+m.hw.code_name+"/alsa.playback." + name)

    def mixer_call(m):
        m.set_mixer("call")
        
    def mixer_call_loud(m):
        m.set_mixer("call.loud")

    def mixer_headphones(m):
        m.set_mixer("wired.headphones")

    def mixer_ringing(m):
        m.set_mixer("speaker")

    def run_microphone(m):
        print("Recording")
        sy("parec /tmp/delme.audio & REC=$!; sleep 10; kill $REC")
        print("Playback")
        sy("pacat /tmp/delme.audio")

class Camera(Test):
    hotkey = "r"
    name = "cameRa"
    yavta = "sudo /my/tui/yavta/yavta"
    def __init__(m):
        subdev = "/dev/v4l-subdev%d"
        m.focus = subdev % 8
        m.flash = subdev % 9
        m.flash_fd = None

    def set_control(m, dev, control, val, tail = ""):
        sy(m.yavta + (" --set-control '0x%x %d' " % (control, val)) + dev + " " + tail)
    
    def set_forever(m, dev, control, val):
        m.set_control(dev, control, val, " --sleep-forever &")

    def set_light(m, on):
        if on:
            m.flash_fd = open(m.flash)
            m.set_control(m.flash, 0x009c0901, 2)
        else:
            m.set_control(m.flash, 0x009c0901, 0)
            m.flash_fd = None

    def run(m):
        sy("sudo camera/back.sh &")
        time.sleep(5)
        print("flash?")
        m.set_forever(m.focus, 0x009a090a, 1023)
        time.sleep(1)
        m.set_control(m.focus, 0x009a090a, 0)
        sy("sudo killall yavta")
        m.set_light(1)
        time.sleep(1)
        m.set_light(0)

class Temperature(Test):
    hotkey = "t"
    name = "Temperature"

    def read_battery_temp(m):
        v = m.read_int(m.battery_path)
        if m.hw.n900:
            return (v / 10.) - 7.5
        return (v / 10.)

    # Charger in case of N900
    def read_board_temp(m):
        v = m.read_int(m.board_path)
        if m.hw.n900:
            return (v / 10.) - 7.5
        return (v / 1000.)

    # FIXME: this is probably wrong. thermal_zone0/temp seems to correspond to 
    # /sys/class/hwmon/hwmon0/temp1_input, which is bq27200-0
    # If we get three thermal zones, 0 is CPU (+20 Celsius?), 1 and 2 is chargers.
    def read_cpu_temp0(m):
        temp = "/sys/devices/virtual/thermal/thermal_zone0/temp"
        v =  m.read_int(temp) / 1000.
        if m.hw.n900:
            v = v - 21.5
        return v

    def probe(m):
        m.battery_path = m.probe_paths("/sys/class/power_supply/",
                                  [ 'rx51-battery/temp', 'battery/temp' ])
        m.board_path = m.probe_paths("/",
                                     [ "/sys/class/power_supply/bq27200-0/temp",
                                       "/sys/class/hwmon/hwmon0/temp1_input" ])
        
    def run(m):
        print("Battery temperature", m.read_battery_temp())
        print("Board/charger temperature", m.read_board_temp())
        print("CPU temperature", m.read_cpu_temp0())

class Accelerometer(Test):
    hotkey = "m"
    name = "acceleroMeter"

    def position(m):
        if not m.use_iio:
            # This works on N900, but it looks the world is moving
            # to the other driver.
            r = m.read(m.directory+"/position")
            if r is None:
                return (0., 0., 0.)
            r = r[1:-2]
            s = r.split(",")
            return list(map(lambda x: float(int(x)/1044.), s))
        x = m.read_int(m.directory+"/in_accel_x_raw")
        y = m.read_int(m.directory+"/in_accel_y_raw")
        z = m.read_int(m.directory+"/in_accel_z_raw")
        s = (x, y, z)
        return list(map(lambda x: float(int(x)/1044.), s))
        
    def run(m):
        print(m.position())
        time.sleep(1)
        print(m.position())
        time.sleep(1)
        print(m.position())

    def probe(m):
        m.directory = "/sys/devices/platform/lis3lv02d"
        if os.path.exists(m.directory):
            m.use_iio = False
            return

        m.use_iio = True
        m.directory = m.probe_paths( "", [ "/sys/bus/iio/devices/iio:device0" ])
        m.write_root(m.directory+"/sampling_frequency", "100")

class GPS(Test):
    hotkey = "g"
    name = "Gps"

    def run(m):
        if m.hw.n900:
            os.system("echo ofono must be running and modem connected for this.")        
            os.system("sudo ./gps3 -d")
        if m.hw.d4:
            os.system("sudo /my/libqmi/src/qmicli/qmicli -d /dev/cdc-wdm1 --pds-start-gps | nc -u 127.0.0.1 5000 &")
        os.system("/my/tui/lib/client.py")
            
    def startup(m):
        if m.hw.d4:
            os.system("sudo killall gpsd; sleep 1; /usr/sbin/gpsd udp://127.0.0.1:5000")
        
class GPRS(Test):
    hotkey = "s"
    name = "gprS"

    def run(m):
        if m.hw.n900:
            print("use ofono to start GPRS")
            
        if m.hw.d4:
            print("gprs?")
            os.system("sudo qmicli -d /dev/cdc-wdm0 --wds-follow-network --wds-start-network=apn=internet.t-mobile.cz & sleep 1")
            os.system("sudo route del default")
            os.system("sudo ifconfig wwan0 up")
            os.system("sudo dhclient wwan0")

class Touchscreen(Test):
    hotkey = "u"
    name = "toUchscreen"

    def run(m):
        pass

    def enabled(m, on):
        dev = "Atmel maXTouch Touchscreen"
        if m.hw.n900:
            dev = "TSC2005 touchscreen"
        sy('xinput set-prop "%s" "Device Enabled" %d' % (dev , on))
            
class Hardware:
    def __init__(m):
        m.battery = Battery()
        m.backlight = Backlight()
        m.light_sensor = LightSensor()
        m.vibrations = Vibrations()
        m.audio = Audio()
        m.camera = Camera()
        m.temperature = Temperature()
        m.led = AccelLED()
        m.accelerometer = Accelerometer()
        m.leds = LEDs()
        m.torch = Torch()
        m.gps = GPS()
        m.gprs = GPRS()
        m.touchscreen = Touchscreen()
        m.all = [ m.battery, m.backlight, m.light_sensor, m.vibrations, 
                  m.audio, m.camera, m.temperature, m.led, m.accelerometer,
                  m.torch, m.leds, m.gps, m.gprs, m.touchscreen ]

        m.detect()
        m.hw_probe()
        
        for o in m.all:
            o.hw = m
            o.probe()

    def hw_probe(m):
        m.debian = os.path.exists('/my/tui/ofone')
        m.n900 = m.code_name == "nokia-rx51"
        m.d4 = m.code_name == "motorola-xt894"
        #print("Have hardware: n900 d4: ", m.n900, m.d4)
            
    def startup(m):
        for o in m.all:
            o.startup()

    def detect(m):
        m.code_name = "unknown"
        m.real_name = "Unknown Linux"
        l = open('/proc/cpuinfo').readlines()
        for l1 in l:
            if l1[:8] == "Hardware":
                s = l1.split(":")
                s = s[1]
                s = s[1:-1]
                #print("Have hardware", s)
                if s == "Nokia RX-51 board":
                    m.code_name = "nokia-rx51"
                    m.real_name = "Nokia N900"
                    return
                if s == "Generic OMAP36xx (Flattened Device Tree)":
                    if os.path.exists('/sys/devices/platform/68000000.ocp/48058000.ssi-controller/ssi0/port0/n950-modem'):
                        m.code_name = "nokia-rm680"
                        m.real_name = "Nokia N950"
                        return
                    if os.path.exists('/sys/devices/platform/68000000.ocp/48058000.ssi-controller/ssi0/port0/n9-modem'):
                        m.code_name = "nokia-rm696"
                        m.real_name = "Nokia N9"
                        return
                if s == "Generic OMAP4 (Flattened Device Tree)":
                    if os.path.exists('/sys/devices/platform/44000000.ocp/48098000.spi/spi_master/spi0/spi0.0/cpcap_battery.0') or \
                       os.path.exists('/sys/devices/platform/44000000.ocp/48000000.interconnect/48000000.interconnect:segment@0/48098000.target-module/48098000.spi/spi_master/spi0/spi0.0/cpcap_battery.0'):
                        m.code_name = "motorola-xt894"
                        m.real_name = "Motorola Droid 4"
                        return
        l = open('/sys/firmware/devicetree/base/compatible').readlines()
        print(l[0][:21])
        if 'purism,librem5-devkit' == l[0][:21]:
            m.code_name = "librem5-devkit"
            m.real_name = "Librem 5 devkit"
            return
        print("Unknown hardware! You'll need to implement detection.")

hw = Hardware()

if __name__ == "__main__":
    b = hw.battery
    b.run()

if __name__ == "__main__":
    hw.detect()
    print(hw.code_name, hw.real_name)
