#!/usr/bin/python
import os, sys, select, socket
from select import select as select_call
from greenlet import greenlet

HOST = ''
try:
    COMMAND = sys.argv[0]
    PORT = int(sys.argv[1])
except:
    PORT = 13111

def select(r, w, e, t=None):
    '''a select() wrapper that allows tuples to represent sockets'''

    x = r or w or e
    if not x: return [],[],[]
    x = x[0]

    for i in range(len(x)): # identify proper tuple index 
        #print 'type check', i, type(x[i])
        if isinstance(x[i], socket.socket):
            break

    if r: ra = zip(*r)[i]
    else: ra = ()
    if w: wa = zip(*w)[i]
    else: wa = ()
    if e: ea = zip(*e)[i]
    else: ea = ()

    r2, w2, e2 = select_call (ra, wa, ea, t)
    return (filter(lambda a:a[i] in r2, r),
            filter(lambda a:a[i] in w2, w),
            filter(lambda a:a[i] in e2, e))

def tell(sock, msg1, msg2=''):
    msg = msg1 + msg2
    if len(msg) > 260:
        raise IndexError("message length too long (%d > 256)" % len(msg))
    sock.send(chr(len(msg)-5) + msg)

def broadcast(msg1, msg2=''):
    global socks
    msg = msg1 + msg2
    if len(msg) > 260:
        raise IndexError("message length too long (%d > 256)" % len(msg))
    for sock, greenlet, hostname in socks[1:]:
        tell(sock, msg)

# Greenlet responsible for client interaction
def client(sock):
    tell(sock, 'CHAT', 'Welcome to the server!')
    buf = '' # packet buffer
    bytes_remaining = 0
    greenlet.getcurrent().parent.switch(None)
    while 1:

        # Received a partial packet; return control to parent greenlet while we wait for the rest of it
        if bytes_remaining:
            print 'SWITCH: if bytes_remaining'
            greenlet.getcurrent().parent.switch(None)

        # In between incoming packets
        else:
            # A packet was completed?
            if buf:
                # Pass message packet up to parent greenlet
                print 'SWITCH: if buf'
                greenlet.getcurrent().parent.switch(buf[:4], buf[4:])
                buf = ''

        # A packet is beginning...
        if (not bytes_remaining) and (not buf):
            # When parent greenlet returns to us, we have a new data ready
            buf = sock.recv(1)
            # Check for disconnect
            if len(buf) == 0:
                raise socket.error(107, 'apparent disconnection')
            bytes_remaining = ord(buf)+5
            buf = ''
            # Check that there is no more data available before returning control
            print
            print 'select_call()'
            r, w, e = select_call([sock], [], [], 0)
            print 'select_call() returned'
            print
            if not r:
                print 'SWITCH: if not r'
                greenlet.getcurrent().parent.switch(None)
            
        # Receive more data
        more = sock.recv(bytes_remaining)
        # Check for disconnect
        if not more:
            raise socket.error(107, 'apparent disconnection (packet dropped)')
        # Pump message packet buffering
        buf += more
        bytes_remaining -= len(more)

def main():
    global socks
    socks = [(server, greenlet.getcurrent(), HOST or '*')]

    while 1:
        r, w, e = select(socks, [], socks)
                
        for sock in e:
            print 'error on', sock
        for sock, proc, addr in r:
            try:
                if sock is server:
                    print 'connection incoming'
                    sock, addr = server.accept()
                    proc = greenlet(client)
                    socks.append( (sock, proc, addr) )
                    proc.switch(sock)
                else:
                    val = proc.switch()
                    if val:
                        code, msg = val
                        print addr, code, msg

                        #if code == 'CHAT':
                        #    broadcast(code, msg)

            except socket.error, e:
                code = e[0]
                if code in [104, 107]:
                    print 'socket disconnect:', e
                else:
                    print 'socket error:', e
                sock.close()

                # Remove
                for i in range(len(socks)):
                    if socks[i][0] == sock:
                        socks.remove(socks[i])
                        break

server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
server.bind((HOST, PORT))
server.listen(5)
print 'Serving'

greenlets = []

try:
    main()

except KeyboardInterrupt:
    print 'Bye'
    print 'Closing socket'
    server.close()

#except Exception, e:
#    print 'Closing socket'
#    server.close()
#    raise e

