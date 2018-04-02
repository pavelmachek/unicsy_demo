#!/usr/bin/python

from __future__ import print_function

import sys
sys.path += [ "/usr/share/unicsy/lib" ]

import socket
import os
import glib

class Phone:
    def line_matches(m, line, match):
        l = len(match)
        return line[:l] == match

    def line_matches_list(m, line, match):
        if not m.line_matches(line, match):
            return None
        l = len(match)
        line = line[l:]
        return map(int, line.split(","))

    def line_matches_int(m, line, match):
        l = m.line_matches_list(line, match)
        if not l:
            return -1
        return l[0]

    def line_ready(m, line):
        if m.expect_next != "":
            if m.expect_next != line:
                print("!!! Expected ", m.expect_next, " got ", line, " -- reason ", m.expect_reason)
            m.expect_next = ""
            m.expect_reason = ""
            return

        if m.expect_message:
            m.incoming_message(line, m.expect_message)
            m.expect_message = None

        v = m.line_matches_int(line, "+CREG: ")
        if v != -1:
            if v == 0:
                m.network = ""
            elif v == 1:
                m.network = "Home network"
            elif v == 3:
                m.network = "Denied"
            elif v == 5:
                m.network = "Roaming"
            else: m.network = "?? network"
            m.network_updated()
            return
            
        v = m.line_matches_int(line, "+CSQ: ")
        if v != -1:
            m.signal_strength = v
            m.network_updated()
            return

        if m.line_matches(line, "+CRING: VOICE"):
            m.call_started("unknown", "unknown", "incoming")
            return

        if m.line_matches(line, "+CMT: "):
            f = line[7:]
            s = f.split('"')
            args = {}
            args['Sender'] = s[0]
            args['SentTime'] = s[2]
            m.expect_message = args

# +CMT: "+420604334013",,"18/04/01,17:15:07+08"
# Testovaci aprilova zprava
#
    def data_ready(m, a, b, c):
        r = m.at.read(1)
        print("Got character ", r)
        if ord(r) == 13:
            return True
        if ord(r) < 32:
            print(".... Received strange character ", ord(r))

        #print("Got>>> ", r)
        if r != '\n':
            m.line_buf += r
        else:
            line = m.line_buf
            print("Data ready>>> ", m.line_buf)
            m.line_buf = ""
            m.log(line)
            m.line_ready(line)
            
        return True

    def run(m):
        m.at.write("ATI\n")
        while True:
            r = m.at.read(1)
            print(r[0], end='')

    def command(m, s):
        #m.log(">>> "+ s)
        print(">>> ", s)
        m.at.write(s + "\r\n")
        if m.expect_next != "":
            print("New expectation, but old one was not yet met", m.expect_next, m.expect_reason)
        m.expect_reason = "Command was sent"
        m.expect_next = "OK"

    def open(m):
        m.open_file()
        m.expect_message = None
        m.expect_next = ""
        m.expect_reason = ""
        m.line_buf = ""
        # | glib.IO_OUT | glib.IO_PRI | glib.IO_ERR | glib.IO_HUP
        glib.io_add_watch(m.at, glib.IO_IN, m.data_ready, m)
        

class PhoneSim(Phone):
    def open_file(m):
        s = socket.socket()
        address = '127.0.0.1'
        port = 12345  # port number is a number, not string
        try:
            s.connect((address, port))
            # originally, it was
            # except Exception, e:
            # but this syntax is not supported anymore.
            m.at = s.makefile("r+", 0)
        except Exception as e:
                print("something's wrong with %s:%d. Exception is %s" % (address, port, e))
        #finally:
        #       s.close()

class PhoneUSB(Phone):
    def open_file(m):
        m.at = open("/dev/ttyUSB4", "r+", 0)
        print("Opened", m.at)

class ModemCtrl(PhoneUSB):
    def __init__(m):
        m.registration = {}
        m.signal_strength = 0
        m.network = ""
        m.open()
        m.modem_init()

    def modem_init(m):
        m.registration = {}
        m.command("ATE0")
        m.command("AT+CVHU=0")
        m.command("AT+CMGF=1")

    def startup(m):
        m.online_modem()

    def answer_all(m):
        m.command("ATA")

    def online_modem(m):
        m.command("AT+CFUN=4")

    def offline_modem(m):
        m.command("AT+CFUN=0")

    def dial_number(m, number, hide_callerid = ""):
        m.command("ATD"+number+";")

    def hangup_all(m):
        m.command("ATH")

    def send_ussd(m, ussdstring):
        fail()
        
    def send_sms(m, number, message):
        fail()

    def connect_internet(m):
        fail()

    def disconnect_internet(m):
        fail()

    def message(m, s):
        print(s)

    def log(m, s):
        print(s)

    def incoming_message(m, msg, args):
        pass

    def network_registration(m, name, value):
        m.registration[name] = value
        m.network_updated()

    def network_updated(m):
        m.network_details(m.signal_strength, m.network, "")

    def network_details(m, signal_strength, summary, details):
        print("Signal", signal_strength, "summary", summary)

    def list_operators(m):
        res = []
        operators = m.netreg.GetOperators()
        for path, properties in operators:
            for key in properties.keys():
                if key in ["Name"]:
                    name = properties["Name"]
                    print("Operator:", name)
                    res += [ name ]
        #print(ops[0])
        return res

    def no_network(m):
        m.registration = {}
        m.signal_strength = 0
        m.network = ""
        m.network_updated()

if __name__ == "__main__":
    m = PhoneSim()
    m.open()
    m.run()
