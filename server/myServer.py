#!/usr/bin/env python

# Copyright (c) Twisted Matrix Laboratories.
# See LICENSE for details.

from twisted.internet.protocol import DatagramProtocol
from twisted.internet import reactor
import sys
import os.path

lib_path = os.path.abspath('../utils')
sys.path.append(lib_path)
from myParser import *
from myUser import *
from myCrypto import *

#Server address and port number should be assigned here
#SERVER_URL="ws://connect.mysensors.mobi:8080"
SERVER_URL="ws://localhost:8080" 
PORT=8080

# manage connection in a dictionary, we save connection along with user/device name
connections={}
deletedConnections={}
#These variables will be used to keep the server name and its public key
serverName="mysensors"
pubkey=""
#Database connection will be kept here
usrDatabase=""

# Here we implement the mySensor Protocol

# Here's a UDP version of the simplest possible protocol
class mySensorUDPServer(DatagramProtocol):
    clients={}
    
    def createUser(self,sender,signature,sensors,data,address):
       global usrDatabase
       global serverName
    
       usr=myUser(usrDatabase,serverName)
       cry=myCrypto(serverName)
      
       pub='';p='';
       if 'pubkey' in data: pub=data['pubkey']
       if 'phone' in data: p= data['phone']
       
       st='SHARE #pubkey %s' %(pub)
       if cry.verifySign(pub,signature,sender):
          status=usr.putUser(sender,p,signature,pub,'pubkey')
       else:
          status=False                
       
       st="DATA #msg "   
       if status:
             st+='UserCreated'
       else:
             st+='UserCreationFailed'
       self.transport.write(st,address)


    def datagramReceived(self, datagram, address):

       parser=myParser(datagram)
       recipients=parser.getUsers()
       sender=parser.getSender()
       signature=parser.getSignature()
       data=parser.getData()
       sensors=parser.getSensors()
       cmd=parser.getCmd()
       
       if cmd=="SHARE":
          if "pubkey" in sensors:
             if serverName in recipients:
                #Create a new account 
                self.createUser(sender,signature,sensors,data,address)
            
       elif cmd=="GET":
            print datagram
       else:
            datagram="BAD COMMAND"

       if address[0] not in self.clients:
           self.clients[address[0]]=address[1]
       print self.clients
       print address[1]
       self.transport.write(datagram, address)

def main():
    global usrDatabase
    #Create connection to the Mongo DB
    try:
       client = MongoClient('localhost', 27017)
       #Creating the database for the server
       db = client[serverName]
       collection = db['users']
       # Access the user collection from the database
       usrDatabase = db.users
    except:
       print "ERRER: Cannot aaccess the Mongo database."
       raise SystemExit

    reactor.listenUDP(9090, mySensorUDPServer())
    reactor.run()

if __name__ == '__main__':
    main()


