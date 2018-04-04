#!/usr/bin/env python3

import sys
sys.path += [ "/usr/share/unicsy/lib" ]
import mygtk
mygtk.setup()

import gtk
import contactsdb
import event_log
import rotatable
import textwrap
import re

class Event:
    def __init__(m, event, db = None):
        m.event = event
        if 'Sender' in m.event:
            m.number = str(m.event['Sender'])
        elif 'number' in m.event:
            m.number = str(m.event['number'])
        else:
            m.number = '(unknown?)'
        m.contact = None
        if db:
            m.contact = db.from_number(m.number)
        if not m.contact:
            m.contact = contactsdb.Contact( [ "(unknown)", m.number ] )
            m.contact.unknown = 1
        
    def fmt(m):
        e = m.event
        s = m.event["type"] + " " + m.contact.fmt()
        if e['type'] == "sms":
            s += " " + str(e["message"])
        return s

class ViewEvents(rotatable.SubWindow):
    def __init__(m, contacts_db):
        rotatable.SubWindow.__init__(m)
        m.detail = None
        m.list_view = None
        m.contacts_db = contacts_db
        m.number = None

        m.scrolled = gtk.ScrolledWindow()
        m.filter = None
        m.filter_number = None

    def event_list(m, events):
        store = gtk.ListStore(str, str, str)

        for ev in events:
            e = Event(ev, m.contacts_db)
            if m.filter and e.event['type'] != m.filter:
                continue
            if m.filter_number and e.number != m.filter_number:
                continue
            text = ''
            if e.event['type'] != 'sms':
                text += m.big(e.event['type'] + " ")
                
            text += m.big(e.contact.fmt() + " ")
            if e.event['type'] == 'sms':
                s = str(e.event['message'])
                s = textwrap.fill(s, 70)
                text += '\n' + m.middle(s)

            date = '???'            
            if "SentTime" in e.event:
                date = e.event["SentTime"]
                date = re.sub("T", "\n", date)
                date = re.sub("[+-][0-9][0-9][0-9][0-9]", "", date)
            store.append([e.number, date, text])

        view = gtk.TreeView(store)

        if False:
            tvcolumn = gtk.TreeViewColumn('Number')
            view.append_column(tvcolumn)
            # create a CellRendererText to render the data
            cell = gtk.CellRendererText()
            # add the cell to the tvcolumn and allow it to expand
            tvcolumn.pack_start(cell, True)
            # set the cell "text" attribute to column 0 - retrieve text
            # from that column in treestore
            tvcolumn.add_attribute(cell, 'markup', 0)
            # Allow sorting on the column
            tvcolumn.set_sort_column_id(0)

        if True:
            tvcolumn = gtk.TreeViewColumn('Date')
            view.append_column(tvcolumn)
            # create a CellRendererText to render the data
            cell = gtk.CellRendererText()
            # add the cell to the tvcolumn and allow it to expand
            tvcolumn.pack_start(cell, True)
            # set the cell "text" attribute to column 0 - retrieve text
            # from that column in treestore
            tvcolumn.add_attribute(cell, 'markup', 1)
            # Allow sorting on the column
            tvcolumn.set_sort_column_id(1)

        if True:
            tvcolumn = gtk.TreeViewColumn('Event')
            view.append_column(tvcolumn)
            # create a CellRendererText to render the data
            cell = gtk.CellRendererText()
            # add the cell to the tvcolumn and allow it to expand
            tvcolumn.pack_start(cell, True)
            # set the cell "text" attribute to column 0 - retrieve text
            # from that column in treestore
            tvcolumn.add_attribute(cell, 'markup', 2)
            # Allow sorting on the column
            tvcolumn.set_sort_column_id(2)

        tree_selection = view.get_selection()
        tree_selection.set_mode(gtk.SELECTION_SINGLE)
        tree_selection.connect("changed", m.selection_changed)

        m.list_view = view
        return view
        
    def update(m, events):
        m.events = events
        m.do_update()

    def do_update(m):
        events = m.events
        if m.list_view:
            m.scrolled.remove(m.list_view)
        m.scrolled.add(m.event_list(events))
        m.scrolled.show_all()

    def set_filter(m, f):
        m.filter = f
        m.filter_number = None
        m.do_update()

    def set_filter_number(m):
        m.filter_number = m.number
        m.do_update()

    def interior(m):
        table = gtk.Table(6,6,True)
        table.attach(m.scrolled, 0,6,0,5)
        
        button = gtk.Button("(number)")
        m.dial_button = button
        button.connect("clicked", lambda _: m.dial())
        table.attach(button, 0,1,5,6)

        _, button = m.font_button(m.big("all"))
        button.connect("clicked", lambda _: m.set_filter(None))
        table.attach(button, 1,2,5,6)

        _, button = m.font_button(m.big("sms"))
        button.connect("clicked", lambda _: m.set_filter("sms"))
        table.attach(button, 2,3,5,6)

        _, button = m.font_button(m.big("missed"))
        button.connect("clicked", lambda _: m.set_filter("missed"))
        table.attach(button, 3,4,5,6)
        
        _, button = m.font_button(m.big("number"))
        button.connect("clicked", lambda _: m.set_filter_number())
        table.attach(button, 4,5,5,6)

        _, button = m.font_button(m.big("Close"))
        button.connect("clicked", lambda _: m.hide())
        table.attach(button, 5,6,5,6)
        return table

    def selection_changed(m, tree_selection):
        (model, pathlist) = tree_selection.get_selected_rows()
        for path in pathlist:
            for i in path:
                tree_iter = model.get_iter(path)
                value = model.get_value(tree_iter, 0)
                m.number = value

        m.dial_button.set_label(m.number)
    
def main():
    gtk.main()
    return 0

if 0:
    list = []
    e = {}
    e['type'] = "sms"
    e['sender'] = "123456"
    e['text'] = "Hello, world! One day, we'll have full desktop distributions running on our cellphones, and will write each application just once, not once for desktop and once for mobile."
    list += [ e ]

    e = {}
    e['type'] = "sms"
    e['sender'] = "567823"
    e['text'] = "Androids are nice, there's nothing wrong with Android. Its just... that there's too much non-free software on pretty much every Android handset. Good luck to Cyanogen, but I still prefer Linux."
    list += [ e ]

    e = {}
    e['type'] = "missed"
    e['sender'] = "234567"
    e['text'] = ""
    list += [ e ]

if __name__ == "__main__":
    elog = event_log.EventLog()
    db = contactsdb.ContactsDb()
    db.load_org()
    win = ViewEvents(db)
    win.basic_main_window()
    win.update(elog.events)    
    main()
