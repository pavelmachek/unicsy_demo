#!/usr/bin/python3
# -*- python -*-
import dbus
import dbus.mainloop.glib
# For python2, see https://dbus.freedesktop.org/doc/dbus-python/doc/tutorial.html#the-qt-main-loop
# "backwards compatibility"
import dbus.glib
import time
import subprocess

global mw

_dbus2py = {
        dbus.String : str,
        dbus.UInt32 : int,
        dbus.Int32 : int,
        dbus.Int16 : int,
        dbus.UInt16 : int,
        dbus.UInt64 : int,
        dbus.Int64 : int,
        dbus.Byte : int,
        dbus.Boolean : bool,
        dbus.ByteArray : str,
        dbus.ObjectPath : str
    }

def dbus2py(d):
        t = type(d)
        if t in _dbus2py:
                return _dbus2py[t](d)
        if t is dbus.Dictionary:
                return dict([(dbus2py(k), dbus2py(v)) for k, v in d.items()])
        if t is dbus.Array and d.signature == "y":
                return "".join([chr(b) for b in d])
        if t is dbus.Array or t is list:
                return [dbus2py(v) for v in d]
        if t is dbus.Struct or t is tuple:
                return tuple([dbus2py(v) for v in d])
        return d

def pretty(d):
        d = dbus2py(d)
        t = type(d)

        if t in (dict, tuple, list) and len(d) > 0:
                if t is dict:
                        d = ", ".join(["%s = %s" % (k, pretty(v))
                                        for k, v in d.items()])
                        return "{ %s }" % d

                d = " ".join([pretty(e) for e in d])

                if t is tuple:
                        return "( %s )" % d

        if t is str:
                return "%s" % d

        return str(d)

def property_changed(name, value, path, interface):
        iface = interface[interface.rfind(".") + 1:]
        mw.log("property {%s} [%s] %s = %s" % (iface, path, name, pretty(value)))
        if iface == "Modem":
            mw.modem_changed(name, value)
        if iface == "NetworkRegistration":
            mw.network_registration(name, value)
        if iface == "VoiceCall":
            mw.call_changed(path, name, value)
        if iface == "ConnectionContext" and name == "Active":
            # Display some indication that GPRS is active?
            mw.connection_active(value)
        if iface == "ConnectionContext" and name == "Settings":
            interface = str(value["Interface"])
            addr = str(value["Address"])
            DNS = value["DomainNameServers"]
            print("Connected to the internet, my IP address is "+addr+".")
            subprocess.check_call(["/usr/bin/sudo", "/sbin/ifconfig", interface, addr, "up"])
            time.sleep(1)
            subprocess.call(      ["/usr/bin/sudo", "/sbin/route", "del", "default"])
            subprocess.check_call(["/usr/bin/sudo", "/sbin/route", "add", "default", "gw", addr])
            print("dns says", DNS, str(DNS[0]))
            #dns1, dns2 = DNS.split(" ")
            open("/etc/resolv.conf", "w").write("nameserver "+str(DNS[0]))

def added(name, value, member, path, interface):
        iface = interface[interface.rfind(".") + 1:]
        mw.log("added {%s} [%s] %s %s" % (iface, member, name, pretty(value)))
        if iface == "VoiceCallManager" and member == "CallAdded":
            mw.call_started(name, value['LineIdentification'], value['State'])

def removed(name, member, path, interface):
        iface = interface[interface.rfind(".") + 1:]
        mw.log("removed {%s} [%s] %s" % (iface, name, member))
        if iface == "VoiceCallManager":
            print("Call ended")
            mw.call_ended(name)

def event(member, path, interface):
        iface = interface[interface.rfind(".") + 1:]
        mw.log("event {%s} [%s] %s" % (iface, path, member))

def message(msg, args, member, path, interface):
        iface = interface[interface.rfind(".") + 1:]
        mw.log("message {%s} [%s] %s %s (%s)" % (iface, path, member,
                                        msg, pretty(args)))
        if member == "IncomingMessage":
            mw.incoming_message(msg, args)

def ussd(msg, member, path, interface):
        iface = interface[interface.rfind(".") + 1:]
        mw.log("ussd {%s} [%s] %s %s" % (iface, path, member, msg))

def value(value, member, path, interface):
        iface = interface[interface.rfind(".") + 1:]
        mw.log("value {%s} [%s] %s %s" % (iface, path, member, str(value)))

def start_ofono():
        loop = dbus.mainloop.glib.DBusGMainLoop(set_as_default=True)
        print("Setting main loop")
        print(loop)
        print("done")
        bus = dbus.SystemBus()


        bus.add_signal_receiver(property_changed,
                                bus_name="org.ofono",
                                signal_name = "PropertyChanged",
                                path_keyword="path",
                                interface_keyword="interface")

        for member in ["IncomingBarringInEffect",
                        "OutgoingBarringInEffect",
                        "NearMaximumWarning"]:
                bus.add_signal_receiver(event,
                                        bus_name="org.ofono",
                                        signal_name = member,
                                        member_keyword="member",
                                        path_keyword="path",
                                        interface_keyword="interface")

        for member in ["ModemAdded",
                        "ContextAdded",
                        "CallAdded",
                        "MessageAdded"]:
                bus.add_signal_receiver(added,
                                        bus_name="org.ofono",
                                        signal_name = member,
                                        member_keyword="member",
                                        path_keyword="path",
                                        interface_keyword="interface")

        for member in ["ModemRemoved",
                        "ContextRemoved",
                        "CallRemoved",
                        "MessageRemoved"]:
                bus.add_signal_receiver(removed,
                                        bus_name="org.ofono",
                                        signal_name = member,
                                        member_keyword="member",
                                        path_keyword="path",
                                        interface_keyword="interface")

        for member in ["DisconnectReason", "Forwarded", "BarringActive"]:
                bus.add_signal_receiver(value,
                                        bus_name="org.ofono",
                                        signal_name = member,
                                        member_keyword="member",
                                        path_keyword="path",
                                        interface_keyword="interface")

        for member in ["IncomingBroadcast", "EmergencyBroadcast",
                        "IncomingMessage", "ImmediateMessage"]:
                bus.add_signal_receiver(message,
                                        bus_name="org.ofono",
                                        signal_name = member,
                                        member_keyword="member",
                                        path_keyword="path",
                                        interface_keyword="interface")

        for member in ["NotificationReceived", "RequestReceived"]:
                bus.add_signal_receiver(ussd,
                                        bus_name="org.ofono",
                                        signal_name = member,
                                        member_keyword="member",
                                        path_keyword="path",
                                        interface_keyword="interface")
        
class ModemCtrl:
    def __init__(m):
        pass

    def modem_init(m):
        global mw
        mw = m

        start_ofono()

        m.registration = {}
        m.bus = dbus.SystemBus()
        m.manager = dbus.Interface(m.bus.get_object('org.ofono', '/'),
                        'org.ofono.Manager')
        m.modems = m.manager.GetModems()
        if not m.modems[0][0]:
            print("No modem detected")
            raise "Don't know how to continue"
        m.path = m.modems[0][0]
        print("Connecting modem %s..." % m.path)
        m.modem = dbus.Interface(
                m.bus.get_object('org.ofono', m.path), 'org.ofono.Modem')

    def startup(m):
        m.online_modem()
        time.sleep(5)
        reg = dbus.Interface(
                m.bus.get_object('org.ofono', m.path), 'org.ofono.NetworkRegistration')
        m.vcm = dbus.Interface(
                m.bus.get_object('org.ofono', m.path), 'org.ofono.VoiceCallManager')
        m.ussd = dbus.Interface(
                m.bus.get_object('org.ofono', m.path), 'org.ofono.SupplementaryServices')
        m.connman = dbus.Interface(
                m.bus.get_object('org.ofono', m.path), 'org.ofono.ConnectionManager')
        m.mm = dbus.Interface(
                m.bus.get_object('org.ofono', m.path), 'org.ofono.MessageManager')
        m.netreg = reg
        m.registration = reg.GetProperties()
        m.network_updated()

    def answer_all(m):
        mgr = m.vcm
        calls = mgr.GetCalls()

        for path, properties in calls:
                state = properties["State"]
                print("[ %s ] %s" % (path, state))

                if state != "incoming":
                        continue

                call = dbus.Interface(m.bus.get_object('org.ofono', path),
                                                'org.ofono.VoiceCall')

                call.Answer()

    def online_modem(m):
        m.modem.SetProperty("Powered", dbus.Boolean(1), timeout = 120)
        m.modem.SetProperty("Online", dbus.Boolean(1), timeout = 120)

    def offline_modem(m):
        m.modem.SetProperty("Online", dbus.Boolean(0), timeout = 120)

    def dial_number(m, number, hide_callerid = ""):
        return m.vcm.Dial(number, hide_callerid)

    def hangup_all(m):
        m.vcm.HangupAll()

    def send_ussd(m, ussdstring):
        properties = m.ussd.GetProperties()
        state = properties["State"]

        print("State: %s" % (state))

        if state == "idle":
            result = m.ussd.Initiate(ussdstring, timeout=100)
            print(result[0] + ": " + result[1])
            m.message(result[0] + ": " + result[1])
        elif state == "user-response":
            m.message("ussd expects user response, not implemented " +
                      m.ussd.Respond(ussdstring, timeout=100))
        else:
            m.message("something unexpected with ussd, not implemented")

    def send_sms(m, number, message):
        try:
            # Delivery reports seem to fail _first time afterofonod starts_?!
            m.mm.SetProperty("UseDeliveryReports", dbus.Boolean(True))
        except:
            print("Could not set deliver reports")
        if len(message) > 160:
            raise("message too long")
        path = m.mm.SendMessage(number, message)
        print("Message sent as ", path)

    def connect_internet(m):
        connman = m.connman
        contexts = connman.GetContexts()
        path = "";

        for i, properties in contexts:
                if properties["Type"] == "internet":
                        path = i
                        break

        if path == "":
                path = connman.AddContext("internet")
                print("Created new context %s" % (path))
        else:
                print("Found context %s" % (path))

        context = dbus.Interface(m.bus.get_object('org.ofono', path),
                                        'org.ofono.ConnectionContext')

        apn = "internet.t-mobile.cz"
        if 1:
                context.SetProperty("AccessPointName", apn)
                print("Setting APN to %s" % apn)

        context_idx = 0

        contexts = connman.GetContexts()

        context = dbus.Interface(m.bus.get_object('org.ofono', path),
                                 'org.ofono.ConnectionContext')

        try:
                context.SetProperty("Active", dbus.Boolean(1), timeout = 100)
        except dbus.DBusException as e:
                print("Error activating %s: %s" % (path, str(e)))
                exit(2)

    def disconnect_internet(m):
        m.connman.DeactivateAll()

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
        m.network = ""
        signal_strength = -1
        ss = "???"
        s = ''
        for a in m.registration:
            label = a
            if label == "MobileCountryCode": label = "MCC"
            if label == "MobileNetworkCode": label = "MNC"
            if label == "LocationAreaCode": label = "LAC"
            if label == "Strength":
                print(a, type(m.registration[a]), m.registration[a])
                signal_strength = int(dbus.Byte(m.registration[a]))
                ss = "%d %%" % signal_strength
                s += label + ": "+ss+"\n"
                continue
            s += label + ":" + pretty(m.registration[a]) + "\n"

        if "Name" in m.registration and m.registration["Status"] == "registered" \
           and signal_strength > 0:
            summary = m.registration["Name"]
            m.network = summary
        else:
            summary = "(no network)"

        m.network_details(signal_strength, summary, s)

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
        m.network_updated()

    def modem_changed(m, name, value):
        if name == "Powered":
            m.no_network()
        if name == "Online":
            m.no_network()

    def connection_active(m, value):
        if value == False:
            m.no_network()

if __name__ == "__main__":
    mc = ModemCtrl()
    mc.modem_init()
    mc.startup()
    print(mc.list_operators())
    mc.connect_internet()
