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
    if len(msg) > 256:
        raise IndexError("message length too long (%d > 256)" % len(msg))
    sock.send(chr(len(msg)) + msg)

# Greenlet responsible for client interaction
def client(sock):
    tell(sock, 'CHAT', 'Welcome to the server!')
    buf = '' # packet buffer
    msg = '' # finished packet, or blank string
    bytes_remaining = 0
    while 1:
        # Pass message packet up to parent greenlet
        greenlet.getcurrent().parent.switch(msg)
        msg = ''

        # No message pending, return control to parent greenlet
        if bytes_remaining == 0:
            # When parent greenlet returns to us, we have a new data ready
            buf = sock.recv(1)
            # Check for disconnect
            if len(buf) == 0:
                raise socket.error(107, 'apparent disconnection 1')
            bytes_remaining = ord(buf)
            buf = ''
            # Check that there is no more data available before returning control
            r, w, e = select_call([sock], [], [])
            if not r:
                greenlet.getcurrent().parent.switch('')

        # Receive more data
        more = sock.recv(bytes_remaining)
        # Check for disconnect
        if not more:
            raise socket.error(107, 'apparent disconnection 2')
        # Pump message packet buffering
        buf += more
        bytes_remaining -= len(more)

        # Message packet reception complete
        if bytes_remaining == 0:
            print 'packet:', buf
            # Pass message packet up to parent greenlet
            msg = buf

def main():
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
                    msg = proc.switch()
                    if msg:
                        print addr, msg
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

