#!/usr/bin/env python3

import os
import re
import json
import sys

class Contact:
    def __init__(m, raw):
        m.name, m.number = raw
        m.multiple_match = 0
        m.unknown = 0

    def fmt(m):
        return m.name + " " + m.number

    def matches_number(m, number):
        if len(number) < 9:
            return m.number == number
        return m.number[-9:] == number[-9:]

class ContactsDb:
    def __init__(m):
        m.contacts = None

    def load_json(m):
        try:
            f = open("contacts.json")
        except:
            m.contacts = [ [ "Emergency", "112" ],
                           [ "Telecom", "800123456" ],
                           [ "Student agency", "800100300" ] ]
        if not m.contacts:
            m.contacts = json.load(f)

    def add_contact(m, name, num):
        #print(name.encode('utf8'), num)
        m.contacts += [ [ name, num ] ]
        
    def load_org(m):
        m.contacts = []
        fn = os.environ['HOME']+"/contacts.org"
        if not os.path.exists(fn):
            return
        if sys.version_info[0] == 2:
            f = open(fn)
        else:
            f = open(fn, encoding='UTF-8')
        last_name = ""
        for l in f.readlines():
            l = l[:-1]
            if l == "":
                continue
            if l[0] == "*":
                last_name = re.sub("^\** ", "", l)
                continue
            if re.match("^:PHONE:", l) or re.match("^:CELL:", l):
                num = re.sub(":[A-Z]*: ", "", l)
                m.add_contact(last_name, num)

    def from_number(m, number):
        match = None
        for raw in m.contacts:
            c = Contact(raw)
            if c.matches_number(number):
                if match:
                    match.multiple_match += 1
                else:
                    match = c
        return match

class ContactsCheck(ContactsDb):
    def add_contact(m, name, num):
        c = m.from_number(num)
        if c:
            print("Duplicate contact", name.encode('utf8'), c.name.encode('utf8'))
                          
        super().add_contact(name, num)

if __name__ == "__main__":
    db = ContactsCheck()
    db.load_org()
    print(db.from_number("299149009").fmt())
