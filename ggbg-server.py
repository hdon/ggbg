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

def client(sock):
    sock.send('CONNECT\n')
    buf = ''
    msg = ''
    while 1:
        # switch up to parent greenlet
        if buf:
            # pass up newline-broken messages to parent greenlet
            while buf:
                n = buf.find('\n')+1
                if n <= 0: break
                msg = buf[:n]
                buf = buf[n:]
                greenlet.getcurrent().parent.switch(msg)
        else:
            greenlet.getcurrent().parent.switch('')

        # select() says our socket is readable any time we get to this point
        growth = sock.recv(256)
        if not growth:
            raise socket.error(107, 'apparent disconnection')
        print 'growth <<%s>>' % growth
        buf += growth

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

