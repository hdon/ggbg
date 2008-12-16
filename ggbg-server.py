#!/usr/bin/python
import os, sys, select, socket

HOST = ''
PORT = 13111

server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
server.bind((HOST, PORT))

try:
    server.listen(5)

    socks = [server]

    while 1:
        r, w, e = select.select(socks, [], socks)
        for sock in socks:
            if sock is server:
                sock, addr = server.accept()
                print addr, 'connected'
                socks.append(sock)
                sock.send('HELLO!')
            else:
                print 'received data:', sock.recv(1)

except KeyboardInterrupt:
    print 'Bye'
    print 'Closing socket'
    server.close()

except Exception, e:
    print 'Closing socket'
    server.close()
    raise e

