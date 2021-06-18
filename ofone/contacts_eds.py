#!/usr/bin/python3
# https://github.com/kupferlauncher/kupfer/issues/39
# sudo apt install python3-vobject
# https://developer.gnome.org/libedbus-private/stable/gdbus-org.gnome.evolution.dataserver.AddressBook.html

import os
import dbus
import subprocess
import hashlib
import vobject
from collections import defaultdict
from subprocess import call

def detect_abook():

    __all__ = (
            "HOME",
            "XDG_DATA_HOME",
    )

    # Always points to the user's home directory
    HOME = os.path.expanduser("~")
    XDG_DATA_EVOLUTION = os.environ.get("XDG_DATA_HOME", os.path.join(HOME, ".local", "share", "evolution", "addressbook"))

    addressbook_uids = []
    for dir in os.listdir(XDG_DATA_EVOLUTION):
      addressbook_uids += [dir]  #To-do: Don't include trash folder

#we should loop through each addessbook but as example I am using a single adb.
#addressbook_uid = addressbook_uids[1]
#addressbook_uid = "be9ba530cf805cc8bf8891209984c1b09bdbf169"
addressbook_uid = "system-address-book"

#get eds factory bus
bus = dbus.SessionBus()
proxy = bus.get_object("org.freedesktop.DBus", 
                       "/")
iface = dbus.Interface(proxy, "org.freedesktop.DBus")

bus_names = iface.ListActivatableNames()
eds_adb = list(filter(lambda x:'org.gnome.evolution.dataserver.AddressBook' in x, bus_names))
EDS_FACTORY_BUS = eds_adb[0]

#get eds subprocess bus
proxy = bus.get_object(EDS_FACTORY_BUS, "/org/gnome/evolution/dataserver/AddressBookFactory")
iface = dbus.Interface(proxy, "org.gnome.evolution.dataserver.AddressBookFactory")

print("Adressbook uid: ", addressbook_uid)
EDS_SUBPROCESS_OBJ_PATH, EDS_SUBPROCESS_BUS  = iface.OpenAddressBook(addressbook_uid)

#Now that we got the required bus names and object path we can get contact pass-ids
proxy = bus.get_object(EDS_SUBPROCESS_BUS, EDS_SUBPROCESS_OBJ_PATH)
iface = dbus.Interface(proxy, "org.gnome.evolution.dataserver.AddressBook")

iface.Open() #otherwise it may fail

def dump_contacts(iface):
    contact_pass_ids = iface.GetContactListUids("") #this will give contact_pass_ids

    contact_final_obj = {}
    for contact_pass_id in contact_pass_ids:
        #Lets form contact_uid from pass_id
        contact_uid = "eds:" + addressbook_uid + ":" + contact_pass_id
        #We also know individual id is just sha1 hash of uid, so
        m = hashlib.sha1()
        m.update((contact_uid).encode('utf-8'))
        contact_individual_id = m.hexdigest()
        print (contact_individual_id)
        print ("\n")

        #we get contact vcard and parse it using python3-vobject
        contact_vcard = iface.GetContact(contact_pass_id)
        print ("vcard: ", contact_vcard)
        vcard = vobject.readOne( contact_vcard )
        full_name = vcard.contents['fn'][0].value
        email_ids = [email.value for email in vcard.contents['email']]
        contact_final_obj[contact_individual_id] = (full_name, email_ids)

    print (contact_final_obj)

def delete_all(iface):
    contact_pass_ids = iface.GetContactListUids("") #this will give contact_pass_ids

    # This removes everything
    iface.RemoveContacts(contact_pass_ids, 0)

def create(iface):
    created_ids = iface.CreateContacts(["""
FN:Dbus Hacker
TEL;TYPE=CELL:800123456
"""], 0)

def sync_all(iface):
    import contactsdb
    db = contactsdb.ContactsDb()
    db.load_org()
    for a in db.contacts:
        name, num = a
        vcard = """
FN:%s
TEL;TYPE=CELL:%s
NOTE:import from org
""" % (name, num)
        ids = iface.CreateContacts([vcard], 0)
        print(ids)

#dump_contacts(iface)
#delete_all(iface)
#create(iface)
sync_all(iface)

