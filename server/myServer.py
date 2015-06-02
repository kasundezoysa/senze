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

#Server port number should be assigned here
port=9090

#manage connection in a dictionary, we save connection along with user/device name
connections={}
deletedConnections={}

#These variables will be used to keep the server name and its public key
serverName="mysensors"
pubkey=""
#Database connection will be kept here
usrDatabase=""

# Here's a UDP version of the simplest possible SENZE protocol
class mySensorUDPServer(DatagramProtocol):
   
   def createUser(self,sender,signature,sensors,data,address):
       global usrDatabase
       global serverName
    
       usr=myUser(usrDatabase,serverName)
       cry=myCrypto(serverName)
      
       pub='';p='';
       if 'pubkey' in data: pub=data['pubkey']
       if 'phone' in data: p= data['phone']
       status=usr.putUser("",p,signature,pub,'pubkey')
       st="DATA #msg "   
       if status:
             st+='UserCreated'
       else:
             st+='UserCreationFailed'
       self.transport.write(st,address)


   def datagramReceived(self, datagram, address):
       global serverName
       global usrDatabase

       parser=myParser(datagram)
       recipients=parser.getUsers()
       sender=parser.getSender()
       signature=parser.getSignature()
       data=parser.getData()
       sensors=parser.getSensors()
       cmd=parser.getCmd()
       
       cry=myCrypto(serverName) 
       sen=myUser(usrDatabase,sender)
         
       if cmd=="SHARE":
          if "pubkey" in sensors and serverName in recipients:
             pubkey=data['pubkey']
             if cry.verifySENZE(pubkey,parser.getSENZE(),parser.getSignature()):
                #Create a new account 
                self.createUser(sender,signature,sensors,data,address) 
       elif cmd=="GET":
            pubkey=sen.loadPublicKey()
            if pubkey !="":
               if cry.verifySENZE(pubkey,parser.getSENZE(),parser.getSignature()):
                  print datagram
               else:
                  print "Verification Failed"
       else:
            datagram="BAD COMMAND"

       #if address[0] not in self.clients:
       #    self.clients[address[0]]=address[1]
       #print self.clients
       print address[1]
       self.transport.write(datagram, address)

def init():
#If .servername is not there we will read the server name from keyboard
#else we will get it from .servername file
   try:
      if not os.path.isfile(".servername"):
         serverName=raw_input("Enter the server name:")
         f=open(".servername",'w')
         f.write(serverName+'\n')
         f.close()
      else:
         #The server name will be read form the .servername file
         f=open(".servername","r")
         serverName = f.readline().rstrip("\n")
   except:
      print "ERRER: Cannot access the server name file."
      raise SystemExit

   #Here we will generate public and private keys for the server
   #These keys will be used to authentication
   #If keys are not available yet
   global pubkey
   try:
      cry=myCrypto(serverName) 
      if not os.path.isfile(cry.pubKeyLoc):
         # Generate or loads an RSA keypair with an exponent of 65537 in PEM format
         # Private key and public key was saved in the .servernamePriveKey and .servernamePubKey files
         cry.generateRSA(1024)
      pubkey=cry.loadRSAPubKey()
   except:
      print "ERRER: Cannot genereate private/public keys for the server."
      raise SystemExit


def main():
    global usrDatabase
    global port

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

    reactor.listenUDP(port, mySensorUDPServer())
    reactor.run()

if __name__ == '__main__':
    init()
    #print pubkey
    main()


