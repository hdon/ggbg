#!/usr/bin/python
import os, sys, select, gtk, gtk.glade, gobject, socket, goocanvas
from gtk import keysyms
from games.mtg.game import MtgGame

#class GSocket(socket.socket):
#    def __init__(self):
#        socket.socket.__init__(self, socket.AF_INET, socket.SOCK_STREAM)
#        self.iochannel = gobject.IOChannel(self.fileno())
#        gobject.io_add_watch(self.iochannel)

def imgload(f):
    '''Return a goocanvas.Image for a given path or file object'''
    if isinstance(f, str):
        f = open(f,'rb')
    loader = gtk.gdk.pixbuf_loader_new()
    loader.write(f.read())
    pbuf = loader.get_pixbuf()
    loader.close()
    img = goocanvas.Image()
    img.set_property('pixbuf', pbuf)
    img.set_property('x', 0)
    img.set_property('y', 0)
    return img

def tell(sock, msg1, msg2=''):
    msg = msg1 + msg2
    if len(msg) > 260 or len(msg) <= 0:
        raise IndexError("message length too long (0 < %d < 260)" % len(msg))
    sock.send(chr(len(msg)-5) + msg)

class GGBG:
    def destroy(self, widget, data=None):
        gtk.main_quit()

    def delete_event(self, widget, event, data=None):
        return False

    def __init__(self):
        self.sock = None
        self.net_packet_buffer = ''
        self.net_packet_len_remaining = 0

        self.gladeXML = gtk.glade.XML("ggbg.glade")
        self.window = self.gladeXML.get_widget('window1')
        self.gladeXML.signal_autoconnect({
            'do_connect': self.do_connect,
            'do_chat': self.do_chat,
            'on_chat_entry_key_press_event': self.on_chat_entry_key_press_event
        })
        #self.gladeXML.get_widget('send_chat_button').connect("clicked", self.button1)
        self.game_area = self.gladeXML.get_widget('game_area')
        self.game_root = self.game_area.get_root_item()
        self.chat_entry = self.gladeXML.get_widget('chat_entry')
        self.chat_history = self.gladeXML.get_widget('chat_history')
        self.chat_history_scroller = self.gladeXML.get_widget('chat_history_scroller')
        self.window.connect("delete_event", self.delete_event)
        self.window.connect("destroy", self.destroy)
        self.window.show_all()

        self.game = MtgGame(self.game_root, imgload)

    def connect(self, addr):
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        gobject.io_add_watch(
            self.sock,
            gobject.IO_IN | gobject.IO_HUP,
            self.recv)
        print 'connect()', self.sock.connect(addr) # host, port

    def on_chat_entry_key_press_event(self, widget, event, *data):
        if event.keyval == keysyms.Return:
            self.do_chat(widget, event, *data)

    def do_connect(self, widget):
        dialog = self.gladeXML.get_widget('connect_dialog')
        resp = dialog.run()
        dialog.hide()
        if resp == gtk.RESPONSE_OK:
            host = self.gladeXML.get_widget('host_name_entry').get_text()
            self.connect((host, 13111))

    def do_chat(self, widget, *data):
        msg = self.chat_entry.get_text()
        if self.sock:
            tell(self.sock, 'CHAT' + msg)
        self.chat_entry.set_text('')
        self.print_to_chat_history('\nscrub: %s' % msg)

    def print_to_chat_history(self, text):
        history = self.chat_history.get_buffer()
        history.insert(history.get_end_iter(), text)

    def disconnect(self):
        self.sock.close()
        self.sock = None
        self.net_packet_len_remaining = 0
        self.net_packet_buffer = ''

    def recv(self, sock, evt, data=None):
        #gobject.io_add_watch(
        #    self.sock,
        #    gobject.IO_IN | gobject.IO_HUP,
        #    self.recv)
        if evt == gobject.IO_HUP:
            print 'disconnected!'
            self.disconnect()
        elif evt == gobject.IO_IN:
            if self.net_packet_len_remaining == 0:
                data = sock.recv(1)
                if not data:
                    print 'apparent disconnection'
                    self.disconnect()
                    return False
                self.net_packet_len_remaining = ord(data)+5
            more = sock.recv(self.net_packet_len_remaining)
            if not more:
                print 'apparent disconnection'
                self.disconnect()
                return False
            self.net_packet_buffer += more
            self.net_packet_len_remaining -= len(more)
            if self.net_packet_len_remaining == 0:
                print 'received packet:', self.net_packet_buffer
                self.handle_packet(self.net_packet_buffer[:4], self.net_packet_buffer[4:])
                self.net_packet_buffer = ''
        return True

    def handle_packet(self, code, data):
        if code == 'CHAT':
            self.print_to_chat_history('\n' + data)
        else:
            print 'unknown packet type "%s"' % code

    def main(self):
        gtk.main()

