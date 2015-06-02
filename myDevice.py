#!/usr/bin/env python

# Copyright (c) Twisted Matrix Laboratories.
# See LICENSE for details.


from twisted.internet.protocol import DatagramProtocol
from twisted.internet import reactor
import socket


class mySensorDatagramProtocol(DatagramProtocol):
    strings = [
        "Hello, world!",
        "What a fine day it is.",
        "Bye-bye!"]

    def __init__(self, host,port,reactor):
        self.ip= socket.gethostbyname(host)
        self.port = port
        #self._reactor=reactor
        #self.ip=reactor.resolve(host)

    def startProtocol(self):
        self.transport.connect(self.ip,self.port)
        self.sendDatagram()
    
    def stopProtocol(self):
        #on disconnect
        #self._reactor.listenUDP(0, self)
        print "STOP **************"

    def sendDatagram(self):
        self.string=raw_input("Enter:")
        #if len(self.strings):
        #    datagram = self.strings.pop(0)
        self.transport.write(self.string)
        #else:
        #    reactor.stop()

    def datagramReceived(self, datagram, host):
        print 'Datagram received: ', repr(datagram)
        self.sendDatagram()

def main():
    #HOST='connect.mysensors.info'
    HOST='localhost'
    PORT=9090
    protocol = mySensorDatagramProtocol(HOST,PORT,reactor)
    reactor.listenUDP(0, protocol)
    reactor.run()

if __name__ == '__main__':
    main()

