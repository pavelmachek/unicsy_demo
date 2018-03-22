#!/usr/bin/python3
# -*- python -*-
import math
import time
import os

def sy(s):
    return os.system(s)

def enable_access(s):
    sy("sudo chmod 666 "+s)

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
        r = f.read()
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
        m.battery = m.probe_paths("/sys/class/power_supply/",
                                  [ 'bq27200-0', 'bq27521-0' ])
        m.charger = m.probe_paths("/sys/class/power_supply/",
                                  [ 'bq24150a-0', 'bq24153-0' ])

    def percent(m, v):
        u = 0.0387-(1.4523*(3.7835-v))
        if u < 0:
            return max(  ((v - 3.3) / (3.756 - 3.300)) * 19.66, 0) 
        return 19.66+100*math.sqrt(u)

    def run(m):
        volt = int(m.read(m.battery+"/voltage_now"))
        volt /= 1000000.
        perc = m.percent(volt)
        
        status = m.read(m.charger+"/status")[:-1]
        current = int(m.read(m.charger+"/charge_current"))
        limit = int(m.read(m.charger+"/current_limit"))

        try:
            charge_now = int(m.read(m.battery+"/charge_now")) / 1000
            charge_full = int(m.read(m.battery+"/charge_full")) / 1000
            #perc2 = int(m.read(m.battery+"/capacity"))
            # Buggy in v4.4
            perc2 = int((charge_now * 100.) / charge_full)
        except:
            # bq27x00-battery 2-0055: battery is not calibrated! ignoring capacity values
            charge_now = 0
            charge_full = 0
            perc2 = 0
        charge_design = m.read_int(m.battery+"/charge_full_design") / 1000
        volt2 = m.read_int(m.battery+"/voltage_now") / 1000000.
        current2 = m.read_int(m.battery+"/current_now") / 1000.

        # http://www.buchmann.ca/Chap9-page3.asp
        # 0.49 ohm is between "poor" and "fail".
        # 0.15 ohm is between "excelent" and "good".
        # at 3.6V.
        resistance = 0.43
        volt3 = volt + (current2 / 1000. * resistance)
        perc3 = m.percent(volt3)

        print("Battery %.2fV %.2fV %.2fV" % (volt, volt2, volt3), \
              "%d%% %d%% %d%%" % (int(perc), int(perc3), perc2), \
              "%d/%d mAh" % (charge_now, charge_full), \
              status, \
              "%d/%d/%d mA" % (int(-current2), current, limit) )
        m.perc = perc
        m.perc2 = perc2
        m.perc3 = perc3
        m.volt = volt
        m.volt2 = volt2
        m.volt3 = volt3
        m.status = status
        m.current = -current2
        m.max_battery_current = current
        m.charger_limit = limit

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
        m.fast_charge(500)

class ChargeBattery(Battery):
    hotkey = "B"
    name = "chargeBattery"

    def run(m):
        m.fast_charge()

class LEDs(Test):
    hotkey = "l"
    name = "LEDs"
    path = "/sys/class/leds/lp5523:"
    scale = 0.1

    def __init__(m):
        m.white = ''

    def probe(m):
        if os.path.exists(m.path+"status-led"):
            m.white = "status-led"

    def set_bright(m, s, v):
        f = open(m.path + s + "/brightness", "w")
        f.write(str(int(v*m.scale)))
        f.close()
        
    def set(m, val):
        (r, g, b) = val
        if m.white:
            m.set_bright(m.white, (r+g+b)/3)
        m.set_bright("r", r)
        m.set_bright("g", g)
        m.set_bright("b", b)

    def kbd_backlight(m, val):
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
        sy("sudo chown pavel /sys/class/i2c-adapter/i2c-2/2-0032/*")

class Backlight(Test):
    hotkey = "c"
    name = "baCklight"
    scale = 0.1

    def probe(m):
        m.path = "/sys/class/backlight/"
        p = os.listdir(m.path)
        m.path += p[0]
        m.path += "/brightness"

    def set(m, i):
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
    path = "/sys/bus/i2c/drivers/tsl2563/2-0029/iio:device1/"

    def get_illuminance(m):
        try:
            return int(m.read(m.path + "in_illuminance0_input"))
        except:
            return -1

    def get_ired_raw(m):
        try:
            return int(m.read(m.path + "in_intensity_both_raw"))
        except:
            return -1

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
        m.keyboard = LEDs()
        m.very_dark = LightSettings(6, 180, "very dark", 0.01)
        m.dark_in_dark_room = LightSettings(8, 180, "dark in dark room", 0.05)
        m.somehow_dark_room = LightSettings(10, 180, "somehow dark room", 0.05)
        m.dark_room = LightSettings(20, 255, "dark room", 0.1)
        m.night_room = LightSettings(40, 10, "night room", 0.1)
        m.cloudy_day_room = LightSettings(128, 10, "cloudy day room", 0.1)
        m.sunlight = LightSettings(255, 10, "sunlight")
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
    
    def on(m, t):
        sy("(echo 5; sleep %f; echo -1) | sudo fftest /dev/input/event2" % t)

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
        sy("sudo alsactl restore -f /usr/share/unicsy/audio/nokia-n900/alsa.playback." + name)

    def mixer_call(m):
        m.set_mixer("call")

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
        temp = "/sys/devices/platform/n900-battery/power_supply/rx51-battery/temp"
        v = m.read(temp)
        if v is None:
            return -274
        return (int(v) / 10.) - 7.5

    def read_charger_temp(m):
        temp = "/sys/devices/platform/68000000.ocp/48072000.i2c/i2c-2/2-0055/power_supply/bq27200-0/temp"
        v = m.read(temp)
        if v is None:
            return -274
        return (int(v) / 10.) - 7.5

    # FIXME: this is probably wrong. thermal_zone0/temp seems to correspond to 
    # /sys/class/hwmon/hwmon0/temp1_input, which is bq27200-0
    # If we get three thermal zones, 0 is CPU (+20 Celsius?), 1 and 2 is chargers.
    def read_cpu_temp0(m):
        temp = "/sys/devices/virtual/thermal/thermal_zone0/temp"
        return int(m.read(temp)) / 1000. - 21.5

    def run(m):
        print("Battery temperature", m.read_battery_temp())
        print("Charger temperature", m.read_battery_temp())
        print("CPU temperature", m.read_cpu_temp0())

class Accelerometer(Test):
    hotkey = "m"
    name = "acceleroMeter"

    def position(m):
        r = m.read("/sys/devices/platform/lis3lv02d/position")
        if r is None:
            return (0., 0., 0.)
        r = r[1:-2]
        s = r.split(",")
        return list(map(lambda x: float(int(x)/1044.), s))
        
    def run(m):
        print(m.position())
        sy("cat /sys/devices/platform/lis3lv02d/position")
        time.sleep(5)
        print(m.position())
        sy("cat /sys/devices/platform/lis3lv02d/position")

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
        m.all = [ m.battery, m.backlight, m.light_sensor, m.vibrations, 
                  m.audio, m.camera, m.temperature, m.led, m.accelerometer ]
        for o in m.all:
            o.probe()

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
                print("Have hardware", s)
                if s == "Nokia RX-51 board":
                    m.code_name = "nokia-rx51"
                    m.real_name = "Nokia N900"
                if s == "Generic OMAP36xx (Flattened Device Tree)":
                    if os.path.exists('/sys/devices/platform/68000000.ocp/48058000.ssi-controller/ssi0/port0/n950-modem'):
                        m.code_name = "nokia-rm680"
                        m.real_name = "Nokia N950"
                    if os.path.exists('/sys/devices/platform/68000000.ocp/48058000.ssi-controller/ssi0/port0/n9-modem'):
                        m.code_name = "nokia-rm696"
                        m.real_name = "Nokia N9"

hw = Hardware()

if __name__ == "__main__":
    b = hw.battery
    b.run()

if __name__ == "__main__":
    hw.detect()
    print(hw.code_name, hw.real_name)
