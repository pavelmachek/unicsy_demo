#!/usr/bin/python

from __future__ import print_function

import sys
sys.path += [ "/usr/share/unicsy/lib" ]

import socket
import os
import glib
import time

class Phone:
    def line_matches(m, line, match):
        l = len(match)
        #print("have (",line,") match (", match, ")", l)
        return line[:l] == match

    def line_matches_list(m, line, match):
        if not m.line_matches(line, match):
            return None
        l = len(match)
        line = line[l:]
        return map(int, line.split(","))

    def line_matches_int(m, line, match):
        if not m.line_matches(line, match):
            return None
        l = len(match)
        line = line[l:]
        return int( line.split(",")[0] )

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
        if v:
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
        if v:
            m.signal_strength = v
            m.network_updated()
            return

        if  m.line_matches(line, "RING") or m.line_matches(line, "+CRING: VOICE"):
            print("!!! incoming call")
            m.call_started("unknown", "unknown", "incoming")
            return

        if m.line_matches(line, "+CMT: "):
            f = line[7:]
            s = f.split('"')
            args = {}
            args['Sender'] = s[0]
            args['SentTime'] = s[2]
            m.expect_message = args

    def process_byte(m, r):
        #print("Got character ", r)
        if ord(r) == 13:
            return None
        if ord(r) != 10 and ord(r) < 32:
            print(".... Received strange character ", ord(r))

        #print("Got>>> ", r)
        if r != '\n':
            m.line_buf += r
        else:
            line = m.line_buf
            m.line_buf = ""
            if line != "":
                m.log("<" + line + "_")
                #print("<" + line + "_")
                return line
        return None

# +CMT: "+420604334013",,"18/04/01,17:15:07+08"
# Testovaci aprilova zprava
#
    def data_ready(m, a, b, c):
        r = m.at.read(1)
        line = m.process_byte(r)
        if line:
            m.line_ready(line)
        return True

    def run(m):
        m.at.write("ATI"+m.l)
        while True:
            r = m.at.read(1)
            print(r[0], end='')

    def command(m, s):
        #m.log(">>> "+ s)
        print(">>> ", s)
        m.at.write(s + m.l)
        #time.sleep(.3)
        #if m.expect_next != "":
        #    print("New expectation, but old one was not yet met", m.expect_next, m.expect_reason)
        m.expect_reason = "Command was sent"
        m.expect_next = "OK"
        #m.data_ready(None, None, None)

    def blocking(m, cmd, exp):
        m.command(cmd)
        while True:
            r = m.at.read(1)
            line = m.process_byte(r)
            if line:
                if line == exp:
                    return
                #print("U?> ", line)
                m.line_ready(line)

    def open(m):
        m.open_file()
        m.expect_message = None
        m.expect_next = ""
        m.expect_reason = ""
        m.line_buf = ""
        # | glib.IO_OUT | glib.IO_PRI | glib.IO_ERR | glib.IO_HUP
        glib.io_add_watch(m.at, glib.IO_IN, m.data_ready, m)
        m.l = "\r"

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
        os.system("sudo chown user /dev/ttyUSB4")
        os.system("stty 0:0:8bd:0:3:1c:7f:15:4:0:1:0:11:13:1a:0:12:f:17:16:0:0:0:0:0:0:0:0:0:0:0:0:0:0:0:0 < /dev/ttyUSB4")
        m.at = open("/dev/ttyUSB4", "r+", 0)
        print("Opened", m.at)

    def powercycle(m):
        bus = "/sys/bus/platform/drivers/"
        phone = "phy-mapphone-mdm6600"
        ohci = "ohci-platform"
        os.system("sudo chown user "+bus+phone+"/unbind")
        os.system("sudo chown user "+bus+phone+"/bind")
        os.system("sudo chown user "+bus+ohci+"/unbind")
        os.system("sudo chown user "+bus+ohci+"/bind")
        os.system("echo 4a064800.ohci > "+bus+ohci+"/unbind")
        os.system("echo usb-phy@1 > "+bus+phone+"/unbind")
        os.system("echo usb-phy@1 > "+bus+phone+"/bind")
        os.system("echo 4a064800.ohci > "+bus+ohci+"/bind")
        # With sleep 3, modem is initialized, but +CSMS (etc) still fails
        time.sleep(10)

class ModemCtrl(PhoneUSB):
    def __init__(m):
        m.registration = {}
        m.signal_strength = 0
        m.network = ""

    def modem_init(m, pdu=0):
        m.open()
        m.registration = {}
        m.blocking("ATE0Q0V1", "OK")
        # CVHU fails otherwise?
        m.blocking("AT+CFUN=1", "OK")
        time.sleep(15)
        #m.command("AT+CREG=2")
        # Format 0: PDU, 1: text
        if pdu:
            m.blocking("AT+CMGF=0", "OK")
        else:
            m.blocking("AT+CMGF=1", "OK")        
        # Forward messages to me.        
        m.blocking("AT+CNMI=1,2,2,1,0", "OK")
        m.blocking("AT+CSMS=0", "OK")
        m.blocking("AT+CGSMS=3", "OK")
        #m.command('AT+CPMS="ME","ME","ME"')
        # 1 -- advanced system
        # Allow terminating voice calls with ATH.
        m.blocking("AT+CVHU=0", "OK")
        
    def modem_init_ofono(m):
        m.open()
        m.registration = {}
        m.blocking("ATE0Q0V1", "OK")
        # For voice calls
        m.blocking("AT+CVHU=0", "OK")
        m.blocking("AT+CFUN=1", "OK")
        m.blocking("AT+CGMI", "OK")
        m.blocking("AT+CGMR", "OK")
        m.blocking("AT+CPIN?", "OK")
        m.blocking("AT+CSCS?", "OK")
        m.blocking("AT+CUSD=1", "OK")
        m.blocking("AT+CAOC=2", "OK")
        m.blocking("AT+CSMS=?", "OK")
        m.blocking("AT+CSCS=?", "OK")
        m.blocking("AT+CREG=2", "OK")
        m.blocking("AT+CSMS=1", "OK")
        m.blocking("AT+CPBS=?", "OK")
        m.blocking("AT+CSMS?", "OK")
        m.blocking("AT+CMGF=?", "OK")
        m.blocking("AT+CMER=3,0,0,1", "OK")
        m.blocking("AT+CPMS=?", "OK")
        m.blocking("AT+CREG?", "OK")
        m.blocking("AT+CMGF=0", "OK")
        m.blocking("AT+COPS=3,2", "OK")
        m.blocking("AT+COPS?", "OK")
        m.blocking('AT+CPMS="ME","ME","ME"', "OK")
        m.blocking("AT+COPS=3,0", "OK")
        m.blocking("AT+COPS?", "OK")
        m.blocking('AT+CPMS="ME","ME","ME"', "OK")
        m.blocking("AT+CNMI=?", "OK")
        m.blocking("AT+CNMI=1,2,2,1,0", "OK")
        m.blocking("AT+CMGL=4", "OK")
        m.blocking("AT+CGSMS=3", "OK")
        m.blocking("AT+COPS?", "OK")

    def startup(m):
        m.online_modem()

    def answer_all(m):
        m.command("ATA")

    def online_modem(m):
        m.command("AT+CFUN=1")

    def offline_modem(m):
        m.command("AT+CFUN=0")

    def dial_number(m, number, hide_callerid = ""):
        m.command("ATD"+number+";")
        m.call_started("unknown", "unknown", "outgoing")

    def hangup_all(m):
        m.command("ATH")

    def send_ussd(m, ussdstring):
        fail()
        
    def send_sms(m, number, message):
        at = 'AT+CMGS="'+number+'"\r'
        print("sms>>> ", at)
        m.at.write(at)
        time.sleep(.1)
        m.command(message+chr(0x1a))

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
    m = ModemCtrl()
    m.powercycle()
    m.modem_init(pdu=1)
    m.run()
