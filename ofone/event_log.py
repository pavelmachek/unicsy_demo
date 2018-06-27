#!/usr/bin/env python3

import json
import mailbox
import email.utils
import sys
import copy

class EventLog:
    def __init__(m):
        m.events = []
        f = None
        try:
            f = open("events.json")
        except:
            print("Can't open events.json")
        if f == None:
            return
        m.events = json.load(f)
        print("Have %d events:" % len(m.events))

    def save(m):
        f = open("events.json", "w")
        f.write(json.dumps(m.events))

    def updated(m):
        pass

    def add_event(m, extra = {}):
        m.events += [ copy.deepcopy(extra) ]
        m.save()
        m.updated()

    def add_message(m, extra):
        m.add_event(extra)

    def add_call(m, t, number, extra = {}):
        call = extra
        call['number'] = number
        call['type' ] = t
        m.add_event(call)

    def add_missed_call(m, number):
        m.add_call("missed", number)

class EventMbox(EventLog):
    def save_message(m, event):
        num = event['Sender']
        from_addr = email.utils.formataddr(('', num))

        mbox = mailbox.mbox('events.mbox')
        mbox.lock()

        try:
            msg = mailbox.mboxMessage()
            msg['From'] = from_addr
            msg['Subject'] = event['message']
            msg.set_payload(event['message'])
            mbox.add(msg)
            mbox.flush()
        finally:
            mbox.unlock()

    def add_message(m, extra):
        m.save_message(extra)
        m.add_event(extra)

if __name__ == "__main__":
    elog = EventMbox()
    for e in elog.events:
        if e['type'] != 'sms':
            continue
        elog.save_message(e)
        


