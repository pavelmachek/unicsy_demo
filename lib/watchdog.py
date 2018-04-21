import os
import time

class FakePos:
    pass

class Watchdog:
    def __init__(m, key):
        #m.mydir = os.getenv("HOME") + "/herd/wd/"
        m.mydir = "/usr/share/unicsy/wd/"
        m.enabled = os.path.isdir(m.mydir)
        m.key = key
        m.mypath = m.mydir+m.key
        m.timeout = 45

    def write(m, summary, details):
        if m.enabled:
            open(m.mypath, "w").write(summary + "\n" + details)

    def read(m):
        if not m.enabled:
            return None
        if not os.path.isfile(m.mypath):
            return None
        if time.time() - os.stat(m.mypath).st_mtime > m.timeout:
            return None
        # If mtime is newer than current time, there's probably something
        # very wrong with the clock.
        if time.time() < os.stat(m.mypath).st_mtime - 5:
            return None
        try:
            p = open(m.mypath, "r")
        except:
            return None
        return p.readlines()

class LocationWatchdog(Watchdog):
    def __init__(m):
        Watchdog.__init__(m, "loc")
        m.pos = FakePos()
        m.timeout = 999999999

    def read_loc(m):
        l = m.read()
        if not l:
            m.pos = None
            return None
        lat_lon = l[0].split(' ')
        lat_lon = lat_lon[0:2]
        m.pos.lat, m.pos.lon = tuple(map(float, lat_lon))
        m.pos.name = l[0].split('#')[-1]
        return [ m.pos ]

class LocationsWatchdog(Watchdog):
    def __init__(m):
        Watchdog.__init__(m, "wifiloc")
        m.pos = FakePos()
        m.timeout = 999999999

    def read_loc(m):
        r = m.read()
        all = []
        for l in r:
            print("line", l, "end")
            if l == "\n" or l == "":
                continue
            m.pos = FakePos()
            lat_lon = l.split(' ')
            lat_lon = lat_lon[0:2]
            m.pos.lat, m.pos.lon = tuple(map(float, lat_lon))
            all += [ m.pos ]
        return all

class ScreenWatchdog(Watchdog):
    def __init__(m):
        Watchdog.__init__(m, "screen")
        m.timeout = 999999999

    def is_active(m):
        try:
            r = m.read()[0][:-1]
        except:
            return True
        if r == "on":
            return True
        if r == "off":
            return False
        return None

class KeyWatchdog(Watchdog):
    def __init__(m):
        Watchdog.__init__(m, "key")
        m.timeout = 999999999

    def is_open(m):
        try:
            r = m.read()[0][:-1]
        except:
            return True
        if r == "open":
            return True
        if r == "closed":
            return False
        return None

class TrackWatchdog(Watchdog):
    def __init__(m):
        Watchdog.__init__(m, "track")
        m.timeout = 30

class StartupWatchdog(Watchdog):
    def __init__(m):
        Watchdog.__init__(m, "startup")
        m.timeout = 30

    def progress(m, percent, phase):
        m.write(str(percent), phase)

class PhoneWatchdog(Watchdog):
    def __init__(m):
        Watchdog.__init__(m, "phone")
        m.reset()

    def reset(m):
        m.status = "watchdog"
        m.network = ""
        m.signal = 0

    def update(m):
        r = m.read()
        if not r:
            m.reset()
            return
        s = map(lambda x: x[:-1], r)
        print(s)
        m.status = s[0]
        m.network = s[2]
        m.signal = int(s[3])
        
class Alert:
    def __init__(m, priority, pattern, base, key, color = [0., 1., 1.]):
        # priority: 0 .. highest (overdischarging battery etc.)
        #           9 .. lowest  (everything ok)
        m.priority = priority
        m.key = key
        m.short = base + " " + key
        m.pattern = pattern
        m.color = color

class Monitor:
    def add_alert(m, a):
        m.alerts[a.key] = a

    def run(m):
        alerts = []
        r = m.wd.read()
        if not r:
            return [ m.watchdog ]
        s = r[0]
        if s[-1] == "\n":
            s = s[:-1]
            if s in m.alerts:
                return [ m.alerts[s] ]
        print(m.name, ": unknown state (%s)" % s)
        return [ m.error ]

class BatteryMonitor(Monitor):
    def __init__(m):
        s = "battery"
        m.name = s
        m.wd = Watchdog(s)
        m.alerts = {}
        m.watchdog = Alert(0, "cXmXyX", s, "watchdog")
        m.error    = Alert(0, "gXbXrX", s, "error")
        m.add_alert( Alert(1, "r.xX..", s, "discharging", [0., .5, 1.] ) )
        m.add_alert( Alert(5, "y.xX..", s, "charging",    [1., 1., 0.] ) )
        m.add_alert( Alert(8, "g.xXx.", s, "full",        [.3, 1., 0.] ) )
        m.add_alert( Alert(5, "r|    ", s, "low",         [1., 0., 0.] ) )
        m.add_alert( Alert(9, "g|    ", s, "ok",          [0., .3, 0.] ) )

class PhoneMonitor(Monitor):
    def __init__(m):
        s = "phone"
        m.name = s
        m.wd = Watchdog(s)
        m.alerts = {}
        m.watchdog = Alert(1, "c.yxmX", s, "watchdog")
        m.error    = Alert(1, "g.bxrX", s, "error")
        m.add_alert( Alert(4, "r|    ", s, "no signal",   [0., 0., 0.] ) )
        m.add_alert( Alert(3, "g X X ", s, "events",      [0., 0., 1.] ) )
        m.add_alert( Alert(9, "g|    ", s, "ok",          [0., .3, 0.] ) )

class TrackMonitor(Monitor):
    def __init__(m):
        s = "track"
        m.name = s
        m.wd = TrackWatchdog()
        m.alerts = {}
        m.watchdog = Alert(9, "g|    ", s, "ok")
        m.error    = Alert(8, "g.bxrX", s, "error")
        m.add_alert( Alert(6, "w.xX..", s, "recording",   [1., 1., 1.] ) )
        m.add_alert( Alert(5, "y.xX..", s, "no gps",      [1., 1., 0.] ) )
    
class AllMonitors:
    def __init__(m):
        m.monitors = {}
        m.monitors['battery'] = BatteryMonitor()
        m.monitors['phone']   = PhoneMonitor()
        m.monitors['track']   = TrackMonitor()        
        m.alerts_on = {}

    def update_alerts(m):
        alerts = []
        for mo in m.monitors:
            mon = m.monitors[mo]
            a = mon.run()
            m.alerts_on[mo] = a
            alerts += a

        m.alerts = alerts

    def worst_from(m, alerts):
        min_priority = 10
        for a in alerts:
            print(a.priority, a.short)
            if a.priority < min_priority:
                min_priority = a.priority
        for a in alerts:
            if min_priority == a.priority:
                break
        return a

    def worst_alert(m):
        return m.worst_from(m.alerts)
