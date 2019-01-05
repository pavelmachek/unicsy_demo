#!/usr/bin/python2
import time
import sys
sys.path += [ "/usr/share/unicsy/lib" ]
import rainbow
import socket

class ColorDisplay:
    def sleep(m, v):
        time.sleep(v)

    def done(m):
        pass

class LinuxLed(ColorDisplay):
    scales = (1., 1., 1.)
    def write(m, s, v):
        f = open(m.path + s + "/brightness", "w")
        scaled = int(v*m.scale)
        if v>0 and scaled == 0:
            scaled = 1
        f.write(str(scaled))
        f.close()

    def change_color(m, val):
        val = map(lambda x: int((x**2.2)*255), val)
        (r, g, b) = val
        #print("Values ", r, g, b)
        (red, green, blue) = m.names
        (r_, g_, b_) = m.scales
        m.write(red, r*r_)
        m.write(green, g*g_)
        m.write(blue, b*b_)

class LedN900(LinuxLed):
    #scales = (1., 0.5, 0.3)
    scales = (1., 0.39, 0.11)
    # Other variant is 255, 90, 50
    def __init__(m):
        m.path = "/sys/class/leds/lp5523:"
        m.scale = 1.0
        m.names = ( "r", "g", "b" )

class LedSony(LinuxLed):
    def __init__(m):
        m.path = "/sys/class/leds/0003:054C:03D5.0006:"
        m.scale = 1.0
        m.names = ( "red", "green", "blue" )

class LedEsp(ColorDisplay):
    def __init__(m):
        m.scale = 1.0
        print("Waiting for connection")

        sock = socket.socket()
        sock.bind(('', 10007))
        sock.setsockopt(socket.IPPROTO_TCP, socket.TCP_NODELAY, 1)
        sock.listen(1)
        s2 = sock.accept()
        m.fd, addr = s2
        print("Got connection from", addr)

    def write(m, s):
        print(s)
        m.fd.send(s)
        m.sleep(.1)

    def change_color(m, c):
        s = "p 0.001 %.3f %.3f %.3f\n" % c
        m.write(s)

    def pattern(m, args):
        s = "p"
        for f in args:
            s += " %.3f" % f
        s += "\r"
        m.write(s)

class GtkColorDisplay(ColorDisplay):
    def __init__(m):
        #import mygtk
        #mygtk.setup()
        import gtk
        global gtk
        m.win = gtk.Window()
        m.win.connect("destroy", gtk.main_quit)

        m.btn = gtk.Button("test")
        m.win.add(m.btn)
        m.win.show_all()
        m.paint()

    def paint(m):
        for i in range(10):
            gtk.main_iteration(False)

    def change_color(m, color):
        (r, g, b) = color
        
        map = m.btn.get_colormap()
        color = map.alloc_color(int(r*65535), int(g*65535), int(b*65535))

        #copy the current style and replace the background
        style = m.btn.get_style().copy()
        style.bg[gtk.STATE_NORMAL] = color

        #set the button's style to the one you created
        m.btn.set_style(style)
        #m.btn.queue_draw()
        m.paint()

    def done(m):
        gtk.main()

class Test:
    def __init__(m, d):
        #m.d = GtkColorDisplay()
        #m.d = LedSony()
        #m.d = LedN900()
        m.d = d
        m.d.change_color((0, 0, 0))

class SimpleTest(Test):
    def run(m):
        m.d.sleep(1)
        m.d.change_color((1., 0, 0))

        m.d.sleep(1)
        m.d.change_color((0, 1., 0))

        m.d.sleep(1)
        m.d.change_color((0, 0, 1.))

        m.d.done()

class RainbowTest(Test):
    def run(m):
        for i in range(380, 780):
            c = rainbow.wl_to_rgb_gamma(i)
            print("Have color", c)
            m.d.change_color(c)
            m.d.sleep(.01)

class GraphTest(Test):
    def interp1(m, old, new, perc):
        res = old + (perc * (new-old))
        return res*1.

    def interp(m, old, new, perc):
        v = [0,0,0]
        for i in range(3):
            v[i] = m.interp1(old[i], new[i], perc)
        return v        
        
    def run(m):
        graph = m.graph
        c = (0, 0, 0)
        while 1:
            if not graph:
                break
            r,g,b,time = graph[:4]
            n = (r, g, b)
            graph = graph[4:]
            t = 0.
            time = time * m.timescale
            if c != n:
                while t < time:
                    m.d.change_color(m.interp(c, n, t/time))
                    t += 10
                    # FIXME !
                    m.d.sleep(0.01)
            else:
                m.d.change_color(c)
                m.d.sleep(time / 1000.)
            c = n

class Charging(GraphTest):
    graph = [ 0, 0, 0, 0,
              0, 0, 0, 1000,
              .25, .25, 0, 500,
              .25, .25, 0, 1000,
              .50, .50, 0, 500,
              .50, .50, 0, 1000,
              .75, .75, 0, 500,
              .75, .75, 0, 1000,
              1., 1., 0, 500,
              1., 1., 0, 1000,
              0, 0, 0, 100 ]
    timescale = 1/8.
    
class Indigo(GraphTest):
    graph = [ 0, 0, 0, 1000,
              111/255., 0, 1., 1000 ]
    timescale = 1/8.

class White(GraphTest):
    graph = [ 1., 1., 1., 0,
              1., 1., 1., 1000,
              .99, 1., 1., 1000,              
    ]

    timescale = 1.

class StringTest(GraphTest):
    scale2 = 1/8.
    timescale = 1.

    def add(m, rgb, t1, t2):
        rgb = list(rgb)
        m.graph += rgb + [ t1*m.scale2 ]
        m.graph += rgb + [ t2*m.scale2 ]

    def addi(m, intensity, t1 = 0., t2 =1000.):
        rgb = map(lambda x: x*intensity, m.color)
        m.add(rgb, t1, t2)

    def prepare(m, s):
        m.color = [1., 0., 0.]

        m.graph = []
        for i in s:
            if i == " ":
                m.addi(0.)
            elif i == ".":
                m.addi(0.2)
            elif i == "-":
                m.addi(0.4)
            elif i == "x":
                m.addi(0.6)
            elif i == "#":
                m.addi(0.8)
            elif i == "X":
                m.addi(1.0)
            elif i == "|":
                m.addi(1.0, 0, 100)

            elif i == "r":
                m.color = [1., 0., 0.]
            elif i == "g":
                m.color = [0., 1., 0.]
            elif i == "b":
                m.color = [0., 0., 1.]
            elif i == "c":
                m.color = [0., 1., 1.]
            elif i == "m":
                m.color = [1., 0., 1.]
            elif i == "y":
                m.color = [1., 1., 0.]
            elif i == "w":
                m.color = [1., 1., 1.]

            else:
                print("unknown character ", i)

class PatternTest(Test):
    def run(m):
        l = m.d
        while True:
            l.change_color((0, 1, 0))
            l.sleep(.5)
            l.change_color((0, 0, 0))
            l.sleep(.5)
            pulse = [ 1., 0, 0, 0,
                      1., 0, 0, 0,
                      1., .6, .3, .3 ]
            #l.pattern(pulse)
            l.sleep(10)

class ClockTest(Test):
    def run(m):
        while True:
            dt = list(time.localtime())            
            h, mi = dt[3], dt[4]
            print(h, mi)            
            mi /= 15

            graph = [ 0.1, 0, 0, 0 ]
            if h < 6:
                basic = [ 0.01, 0, 0 ]
            elif h < 23:
                basic = [ 0, 0.01, 0 ]
            else:
                basic = [ 0, 0, 0.01 ]

            graph = [ .1 ] + basic
            graph = [ 5 ] + basic            

            for i in range(h/5):
                graph += [ 0.1, 0, 0, 0.2 ]
                graph += [ 0.1, 0, 0, 0 ]                
            for i in range(h%5):
                graph += [ 0.4, 0, 0.2, 0 ]
                graph += [ 0.4, 0, 0, 0 ]                
                
            for i in range(mi):
                graph += [ 0.2, 0.4, 0, 0 ]
                graph += [ 0.2, 0, 0, 0 ]                

            m.d.pattern(graph)
            time.sleep(60)

class WhiteTest(Test):
    def run(m):
        v = 0.0
        while True:
            m.d.change_color((v, v, v))
            time.sleep(.01)
            v += 0.001
            if v > 1:
                v = 0

if __name__ == "__main__":
    # GtkColorDisplay
    t = WhiteTest(LedN900())
    #t = PatternTest(LedN900())
    #t = ClockTest(LedEsp())
    #t = PatternTest(LedEsp())
    #t = StringTest(LedEsp())
    #t.prepare("g X     ")
    #t.prepare("g |   X   ")
#t.prepare("g X#x-.  ")
    #t.prepare("g X#x-. b X#x-.  ")
#t.prepare("m X#x-.  ")
#t = SimpleTest()
    #t = RainbowTest(LedEsp())
#t = Indigo()
#t = White()
#t = Charging()
    t.run()
    t.run()
    t.run()
    t.run()

