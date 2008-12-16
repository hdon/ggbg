#!/usr/bin/python
import os, sys, serial, select, string, gtk, gtk.glade, gobject

class GGBG:
    def destroy(self, widget, data=None):
        gtk.main_quit()

    def delete_event(self, widget, event, data=None):
        return False

    def __init__(self):
        self.gladeXML = gtk.glade.XML("ggbg.glade")
        self.window = self.gladeXML.get_widget('window1')
        #self.REL_mode_arrow = self.gladeXML.get_widget('REL_mode_arrow')
        #self.gladeXML.get_widget('button1').connect("clicked", self.hello)
        self.window.connect("delete_event", self.delete_event)
        self.window.connect("destroy", self.destroy)
        self.window.show_all()

    def main(self):
        gtk.main()

