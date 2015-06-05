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
database=""

# Here's a UDP version of the simplest possible SENZE protocol
class mySensorUDPServer(DatagramProtocol):
   
   def createUser(self,query,address):
       global database
       global serverName

       usr=myUser(database,serverName)
       cry=myCrypto(serverName)
       data=query.getData()
       pubkey='';phone='';
       if 'pubkey' in data: pubkey=data['pubkey']
       if 'phone' in data: phone= data['phone']
       if cry.verifySENZE(query,pubkey):
          status=usr.addUser(query.getSender(),phone,query.getSENZE(),pubkey,query.getSignature())
       st="DATA #msg "
       if status:
             st+='UserCreated'
       else:
             st+='UserCreationFailed'
       self.transport.write(st,address)

   def shareSensors(self,query):
       global connections
       global database
       """
        In order to start the sharing process both users need to online.
        For a instance, if query comes 'SHARE #tp @user2' from the user1.
        First we need to verify that user2 is online.
        Then mysensors adds "user2" to the sensor dictionary at user1's document and
        sensor name to the "user1" dictionary at user2's document.
        Finally it delivers the message SHARE #tp @user2 ^user1 to user2.
        Otherwise it sends DATA #msg Shared to user1.
       """
       usr=myUser(database,query.getSender())
       recipients=query.getUsers()
       for recipient in recipients:
           if recipient in connections.keys():
              usr.share(recipient,query.getSensors())
              forward=connections[recipient]
              self.transport.write(query.getFULLSENZE(),forward)


   def unshareSensors(self,query):
       global connections
       global database
       usr=myUser(database,query.getSender())
       recipients=query.getUsers()
       for recipient in recipients:
           if recipient in connections.keys():
              usr.unShare(recipient,query.getSensors())
              forward=connections[recipient]
              self.transport.write(query.getFULLSENZE(),forward)


   def GETSenze(self,query):
       global connections
       global database
       global serverName

       sender=query.getSender()
       sensors=query.getSensors()
       usr=myUser(database,serverName)
       recipients=query.getUsers() 
       for recipient in recipients:
           recipientDB=myUser(database,recipient)  
           if 'pubkey' in sensors:
               #Since mysensors already has public key of it clients,
               #it responses on behalf of the client.
               pubkey=recipientDB.loadPublicKey()
               if pubkey!='' :
                  if sender in connections.keys():
                     backward=connections[sender]    
                     senze='DATA #pubkey %s' %(pubkey)
                     print "*******************"
                     self.transport.write(senze,backward)
           #Otherwise GET message will forward to the recipients     
           else:
               if recipient in connections.keys():
                  forward=connections[recipient]
                  if recipientDB.isShare(sender,query.getSensors()):
                     self.transport.write(query.getFULLSENZE(),forward)
  

   def PUTSenze(self,query):
       global connections
       global database
       
       sender=query.getSender()
       usr=myUser(database,sender)
       recipients=query.getUsers()
       #PUT message will forward to the recipients     
       for recipient in recipients:
           if recipient in connections.keys():
              recipientDB=myUser(database,recipient)
              if recipientDB.isShare(sender,query.getSensors()):
                 forward=connections[recipient]
                 self.transport.write(query.getFULLSENZE(),forward)


   def DATASenze(self,query):
       global connections
       global database
       
       sender=query.getSender()
       usr=myUser(database,sender)
       recipients=query.getUsers()
       for recipient in recipients:
           if recipient in connections.keys():
              recipientDB=myUser(database,recipient)
              if recipientDB.isAllow(sender,query.getSensors()):
                 forward=connections[recipient]
                 self.transport.write(query.getFULLSENZE(),forward)


   def datagramReceived(self, datagram, address):
       global serverName
       global usrDatabase

       query=myParser(datagram)
       recipients=query.getUsers()
       sender=query.getSender()
       signature=query.getSignature()
       data=query.getData()
       sensors=query.getSensors()
       cmd=query.getCmd()
       validQuery=False  
       cry=myCrypto(serverName) 
       if cmd=="SHARE" and "pubkey" in sensors and serverName in recipients:
          #Create a new account 
          self.createUser(query,address)
       else:
          senderDB=myUser(database,sender)
          pubkey=senderDB.loadPublicKey()
          if pubkey !="":
             if cry.verifySENZE(query,pubkey):
                validQuery=True

       if validQuery:
            connections[sender]=address
            if cmd=="SHARE":
                self.shareSensors(query)
            elif cmd=="UNSHARE":
                self.unshareSensors(query)
            elif cmd=="GET":
                self.GETSenze(query)
            elif cmd=="PUT":
                self.PUTSenze(query)
            elif cmd=="DATA":
                self.DATASenze(query)

       else:
            datagram="Bad query"
            self.transport.write(datagram, address)

       #if address[0] not in self.clients:
       #    self.clients[address[0]]=address[1]
       #print self.clients
       #print address[1]
       #self.transport.write(datagram, address)

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
    global database
    global port

    #Create connection to the Mongo DB
    try:
       client = MongoClient('localhost', 27017)
       #Creating the database for the server
       db = client[serverName]
       collection = db['users']
       # Access the user collection from the database
       database = db.users
    except:
       print "ERRER: Cannot aaccess the Mongo database."
       raise SystemExit

    reactor.listenUDP(port, mySensorUDPServer())
    reactor.run()

if __name__ == '__main__':
    init()
    #print pubkey
    main()


