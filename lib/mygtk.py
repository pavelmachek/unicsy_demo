#!/usr/bin/python3
import sys

is3 = False

def setup2():
    import pygtk
    pygtk.require('2.0')
    #print("Fell back to pygtk 2")

def setup3():
    global is3
    # This needs python3-gi
    # May need python3-cairo-dev, python3-gi-cairo.
    from gi import pygtkcompat

    pygtkcompat.enable() 
    pygtkcompat.enable_gtk(version='2.0')
    #print("Having pygtk 3")
    #is3 = True


def setup_try():
  try:
    setup3()
  except:
    setup2()

def setup_2on2():
    if sys.version_info[0] > 2:
        setup3()
    else:
        setup2()

def setup():
    setup_2on2()

