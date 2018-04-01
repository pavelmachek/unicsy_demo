#!/usr/bin/env python3

import sys
sys.path += [ "../maemo" ]
import mygtk
mygtk.setup()

import gtk
import re
import rotatable
import contactsdb
import os

class Contacts(rotatable.SubWindow):
    def __init__(m):
        rotatable.SubWindow.__init__(m)
        m.number = ""
        m.search = ""
        m.labels = [ " ",
                     ".", "abc", "def",
                     "ghi", "jkl", "mno",
                     "pqrs", "tuv", "wxyz" ]
        m.db = contactsdb.ContactsDb()
        m.db.load_org()

    def dial(m):
        print("Should dial "+m.number)
        os.system("chromium 'http://m.mobilecity.cz/?a=0&d="+m.number+"'")

    def update_label(m):
        m.dial_button.set_label('<span size="xx-large">%s</span>' % m.number)

    def update(m):
        m.update_label()
        m.search = ""
        for i in range(len(m.number)):
            digit = int(m.number[i])
            c = m.labels[digit]
            if c == " " and i==0:
                c = "^"
            if digit > 1:
                c = "["+c+"]"
            m.search += c

        print("Searching for ", m.search)
        m.hbox.remove(m.scrolled)
        m.add_scrolled(m.db.contacts)

    def dial_key(m, widget, key):
        print("Got key ", key)
        m.number += key
        m.update()

    def back_key(m):
        m.number = m.number[:-1]
        m.update()

    def back_all(m):
        m.number = ""
        m.update()

    def create_button(m, d):
        l = m.big('%d' % d) + m.labels[d]
        _, button = m.font_button(l)
        return button

    def dial_pad(m):
        table = gtk.Table(5, 3, True)

        m.dial_button, button = m.font_button("(dial)")
        table.attach(button, 0, 3, 0, 1)
        button.connect("clicked", lambda s: m.dial())

        for i in range(9):
            d = ((i+1)%10)
            button = m.create_button(d)
            x = i % 3
            y = i / 3 + 1
            table.attach(button, x, x+1, y, y+1)
            button.connect("clicked", m.dial_key, str(d))

        button = m.create_button(0)
        table.attach(button, 1, 2, 4, 5)
        button.connect("clicked", m.dial_key, str(0))

        _, button = m.font_button(m.big('*'))
        table.attach(button, 0, 1, 4, 5)
        button.connect("clicked", m.dial_key, '*')
        
        _, button = m.font_button(m.big('#'))
        table.attach(button, 2, 3, 4, 5)
        button.connect("clicked", m.dial_key, '#')

        return table

    def contact_key(m, widget, label):
        m.number = label
        m.update()

    def selection_changed(m, tree_selection) :
        print("Selection changed")
        (model, pathlist) = tree_selection.get_selected_rows()
        for path in pathlist:
            tree_iter = model.get_iter(path)
            value = model.get_value(tree_iter, 1)
            m.number = value
        m.update_label()

    def contact_list(m, contacts):
        #print(help(gtk))
        store = gtk.ListStore(str, str)

        for (name, number) in contacts:
            if not re.search(m.search, name.lower()):
                continue
            store.append([m.big(name) + '\n' + number, number])

        view = gtk.TreeView(store)
        tvcolumn = gtk.TreeViewColumn('Name')
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

        tree_selection = view.get_selection()
        tree_selection.set_mode(gtk.SELECTION_SINGLE)
        tree_selection.connect("changed", m.selection_changed)

        m.list_view = view

        return view
    
    def add_scrolled(m, contacts):
        m.scrolled = scrolled = gtk.ScrolledWindow()
        scrolled.add(m.contact_list(contacts))
        scrolled.show_all()
        m.hbox.add(scrolled)

    def aux_interior(m):
        table = gtk.Table(5, 3, True)
        
        m.hbox = gtk.HBox()
        m.add_scrolled(m.db.contacts)
        table.attach(m.hbox, 0, 3, 0, 4)

        _, w = m.font_button(m.big("&lt;&lt;"))
        table.attach(w, 0, 1, 4, 5)
        w.connect("clicked", lambda s: m.back_key())

        _, w = m.font_button(m.big("&lt;&lt;&lt;"))
        table.attach(w, 1, 2, 4, 5)
        w.connect("clicked", lambda s: m.back_all())

        _, w = m.font_button(m.big("Close"))
        table.attach(w, 2, 3, 4, 5)
        w.connect("clicked", lambda s: m.hide())
        return table

    def main_interior(m):
        return m.dial_pad()

if __name__ == "__main__":
    contacts = Contacts()
    contacts.basic_main_window()
    gtk.main()    
