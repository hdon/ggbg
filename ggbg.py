#!/usr/bin/python
import os, sys, select, gtk, gtk.glade, gobject, socket

#class GSocket(socket.socket):
#    def __init__(self):
#        socket.socket.__init__(self, socket.AF_INET, socket.SOCK_STREAM)
#        self.iochannel = gobject.IOChannel(self.fileno())
#        gobject.io_add_watch(self.iochannel)

class GGBG:
    def destroy(self, widget, data=None):
        gtk.main_quit()

    def delete_event(self, widget, event, data=None):
        return False

    def __init__(self):
        self.gladeXML = gtk.glade.XML("ggbg.glade")
        self.window = self.gladeXML.get_widget('window1')
        self.gladeXML.get_widget('button1').connect("clicked", self.button1)
        self.window.connect("delete_event", self.delete_event)
        self.window.connect("destroy", self.destroy)
        self.window.show_all()

    def connect(self, addr):
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        gobject.io_add_watch(
            self.sock,
            gobject.IO_IN | gobject.IO_HUP,
            self.recv)
        print 'connect()', self.sock.connect(addr) # host, port

    def button1(self, widget, data=None):
        self.connect(('localhost', 13111))

    def recv(self, sock, evt, data=None):
        if evt == gobject.IO_HUP:
            print 'disconnected!'
        elif evt == gobject.IO_IN:
            data = sock.recv(10)
            print 'received data', data

    def main(self):
        gtk.main()

