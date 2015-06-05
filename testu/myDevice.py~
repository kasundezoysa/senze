#!/usr/bin/env python

# Copyright (c) Twisted Matrix Laboratories.
# See LICENSE for details.


from twisted.internet.protocol import DatagramProtocol
from twisted.internet import reactor
import datetime

import socket
import time
import sys
import os.path
lib_path = os.path.abspath('../utils')
sys.path.append(lib_path)
from myParser import *
from myCrypto import *
#from myDriver import *
#from myCamDriver import *
import re
import hashlib
#from PIL import Image

#host='connect.mysensors.info'
host='localhost'
port=9090
state="INITIAL"
device=""
server="mysensors"

class mySensorDatagramProtocol(DatagramProtocol):
  
    def __init__(self, host,port,reactor):
        self.ip= socket.gethostbyname(host)
        self.port = port
        #self._reactor=reactor
        #self.ip=reactor.resolve(host)

    def startProtocol(self):
        self.transport.connect(self.ip,self.port)
        if state=='INITIAL':
           #If system is at the initial state, it will send the device creation Senze
           self.register()
        else:
           response=raw_input("Enter your Senze:")
           self.sendDatagram(response)

    def stopProtocol(self):
        #on disconnect
        #self._reactor.listenUDP(0, self)
        print "STOP **************"

    def register(self):
        global server
        cry=myCrypto(name=device) 
        senze ='SHARE #pubkey %s @%s' %(pubkey,server)
        senze=cry.signSENZE(senze)
        self.transport.write(senze)
        
    def sendDatagram(self,senze):
        global server
        cry=myCrypto(name=device)
        senze=cry.signSENZE(senze)
        print senze
        self.transport.write(senze)
    
    def datagramReceived(self, datagram, host):
        print 'Datagram received: ', repr(datagram)
        
        parser=myParser(datagram)
        recipients=parser.getUsers()
        sender=parser.getSender()
        signature=parser.getSignature()
        data=parser.getData()
        sensors=parser.getSensors()
        cmd=parser.getCmd()
       
        
        if cmd=="DATA":
           if 'UserCreated' in data['msg']:
               #Creating the .devicename file and store the device name and PIN  
               f=open(".devicename",'w')
               f.write(device+'\n')
               f.close()
               print device+ " was created at the server."
               print "You should execute the program again."
               print "The system halted!"
               reactor.stop()

           elif 'UserCreationFailed' in data['msg']:
              print "This user name may be already taken"
              print "You can try it again with different username"
              print "The system halted!"
              reactor.stop()

         #self.sendDatagram()

def init():
    #cam=myCamDriver()
    global device
    global pubkey
    global state
    #If .device name is not there, we will read the device name from keyboard
    #else we will get it from .devicename file
    try:
      if not os.path.isfile(".devicename"):
         device=raw_input("Enter the device name: ")
         # Account need to be created at the server
         state='INITIAL'
      else:
         #The device name will be read form the .devicename file
         f=open(".devicename","r")
         device = f.readline().rstrip("\n")
         state='READY'
    except:
      print "ERRER: Cannot access the device name file."
      raise SystemExit

    #Here we will generate public and private keys for the device
    #These keys will be used to perform authentication and key exchange
    try:
      cry=myCrypto(name=device)
      #If keys are not available yet
      if not os.path.isfile(cry.pubKeyLoc):
         # Generate or loads an RSA keypair with an exponent of 65537 in PEM format
         # Private key and public key was saved in the .devicenamePriveKey and .devicenamePubKey files
         cry.generateRSA(bits=1024)
      pubkey=cry.loadRSAPubKey()
    except:
        print "ERRER: Cannot genereate private/public keys for the device."
        raise SystemExit
    print pubkey
   
    #Check the network connectivity.
    #check_connectivity(ServerName)

def main():
    global host
    global port
    protocol = mySensorDatagramProtocol(host,port,reactor)
    reactor.listenUDP(0, protocol)
    reactor.run()

if __name__ == '__main__':
    init()
    main()
