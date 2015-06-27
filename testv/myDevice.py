#!/usr/bin/env python

###############################################################################
##
##  My Sensor UDP Client v1.0
##  @Copyright 2014 MySensors Research Project
##  SCoRe Lab (www.scorelab.org)
##  University of Colombo School of Computing
##
##  Licensed under the Apache License, Version 2.0 (the "License");
##  you may not use this file except in compliance with the License.
##  You may obtain a copy of the License at
##
##      http://www.apache.org/licenses/LICENSE-2.0
##
##  Unless required by applicable law or agreed to in writing, software
##  distributed under the License is distributed on an "AS IS" BASIS,
##  WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
##  See the License for the specific language governing permissions and
##  limitations under the License.
##
###############################################################################


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
serverPubKey=""

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
    
    def handleServerResponse(self,senze):
        sender=senze.getSender()
        data=senze.getData()
        sensors=senze.getSensors()
        cmd=senze.getCmd()
 
        if cmd=="DATA":
           if 'msg' in sensors and 'UserRemoved' in data['msg']:
              cry=myCrypto(device)
              try:
                 os.remove(".devicename")
                 os.remove(cry.pubKeyLoc)
                 os.remove(cry.privKeyLoc)
                 print "Device was successfully removed"
              except OSError:
                 print "Cannot remove user configuration files"
              reactor.stop()

           elif 'pubkey' in sensors and data['pubkey']!="" and 'name' in sensors and data['name']!="":
                 recipient=myCrypto(data['name'])
                 if recipient.saveRSAPubKey(data['pubkey']):
                    print "Public key=> "+data['pubkey']+" Saved."
                 else:
                    print "Error: Saving the public key."

    def datagramReceived(self, datagram, host):
        global device
        print 'Datagram received: ', repr(datagram)
        
        parser=myParser(datagram)
        recipients=parser.getUsers()
        sender=parser.getSender()
        signature=parser.getSignature()
        data=parser.getData()
        sensors=parser.getSensors()
        cmd=parser.getCmd()
       
        validQuery=False  
        cry=myCrypto(device)
        if state=="READY":
           if serverPubkey !="" and sender=="mysensors":
              if cry.verifySENZE(parser,serverPubkey):
                 self.handleServerResponse(parser)
              else:
                 print "SENZE Verification failed"
           else:
              if sender!="":
                 recipient=myCrypto(sender)
                 if os.path.isfile(recipient.pubKeyLoc):
                    pub=recipient.loadRSAPubKey()
                 else:
                    pub=""
                 if pub!="" and cry.verifySENZE(parser,pub):
                    print "SENZE Verified"
                 else:
                    print "SENZE Verification failed"
               
        else:
           if cmd=="DATA":
              if 'msg' in sensors and 'UserCreated' in data['msg']:
                 # Creating the .devicename file and store the device name 
                 # public key of mysensor server  
                 f=open(".devicename",'w')
                 f.write(device+'\n')
                 if 'pubkey' in sensors: 
                     pubkey=data['pubkey']
                     f.write(pubkey+'\n')
                 f.close()
                 print device+ " was created at the server."
                 print "You should execute the program again."
                 print "The system halted!"
                 reactor.stop()

              elif 'msg' in sensors and 'UserCreationFailed' in data['msg']:
                 print "This user name may be already taken"
                 print "You can try it again with different username"
                 print "The system halted!"
                 reactor.stop()
            
         #self.sendDatagram()

def init():
    #cam=myCamDriver()
    global device
    global pubkey
    global serverPubkey
    global state
    #If .device name is not there, we will read the device name from keyboard
    #else we will get it from .devicename file
    try:
      if not os.path.isfile(".devicename"):
         device=raw_input("Enter the device name: ")
         # Account need to be created at the server
         state='INITIAL'
      else:
         #The device name and server public key will be read form the .devicename file
         f=open(".devicename","r")
         device = f.readline().rstrip("\n")
         serverPubkey=f.readline().rstrip("\n")
         print serverPubkey
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
