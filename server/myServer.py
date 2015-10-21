#!/usr/bin/env python
###############################################################################
##
##  My Sensor UDP Server v1.0
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
import sys
import os.path
import time

lib_path = os.path.abspath('../utils')
sys.path.append(lib_path)
from myParser import *
from myUser import *
from myCrypto import *

#UDP Server port number should be assigned here
port=9090

# At present we manage connection in a dictionary. 
# We save connection IP and port along with user/device name
connections={}
connectionsTime={}

#These global variables will be used to keep the server name and its public key
serverName="mysensors"
serverPubkey=""
#Database connection will be kept in this variable
database=""

# Here's a UDP version of the simplest possible SENZE protocol
class mySensorUDPServer(DatagramProtocol):
   
   # This method will create a new user at the server based on the following SENZE
   # SHARE #pubkey PEM_PUBKEY @mysensors #time timeOfRequest ^userName signatureOfTheSenze
   def createUser(self,query,address):
       global database
       global serverName
       global serverPubkey

       usr=myUser(database,serverName)
       cry=myCrypto(serverName)
       data=query.getData()
       pubkey='';phone='';
       if 'pubkey' in data: pubkey=data['pubkey']
       if 'phone' in data: phone= data['phone']
       if cry.verifySENZE(query,pubkey):
          status=usr.addUser(query.getSender(),phone,query.getSENZE(),pubkey,query.getSignature())
       if status:
             st='DATA #msg UserCreated #pubkey %s ' %(serverPubkey)
       else:
             st='DATA #msg UserCreationFailed'
       senze=cry.signSENZE(st)
       self.transport.write(senze,address)


   # This methid will remove the user at the server based on the following SENZE
   # UNSHARE #pubkey @mysensors #time timeOfRequest ^userName signatureOfTheSenze
   def removeUser(self,sender,pubkey,address):
       global database
       global serverName

       usr=myUser(database,serverName)
       cry=myCrypto(serverName)
       status=usr.delUser(sender,pubkey)       
       st="DATA #msg "
       if status:
             st+='UserRemoved'
       else:
             st+='UserCannotRemoved'
       senze=cry.signSENZE(st)
       self.transport.write(senze,address)


   def shareSensors(self,query):
       global connections
       global database
       global serverName
       """
        If query comes 'SHARE #tp @user2 #time t1 ^user1 siganture' from the user1.
        First we need to verify that user2 is available.
        Then mysensors adds "user2" to the sensor dictionary at user1's document and
        sensor name to the "user1" dictionary at user2's document.
        Finally it delivers the message SHARE #tp @user2 #time t1 ^user1 signature to user2.
       """
       usr=myUser(database,query.getSender())
       recipients=query.getUsers()
       for recipient in recipients:
           if recipient in connections.keys():
              usr.share(recipient,query.getSensors())
              forward=connections[recipient]
              if forward!=0:
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
              if forward!=0:
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
                     senze='DATA #name %s #pubkey %s' %(recipient,pubkey)
                     cry=myCrypto(serverName) 
                     senze=cry.signSENZE(senze)
                     self.transport.write(senze,backward)
           #Otherwise GET message will forward to the recipients     
           else:
               if recipient in connections.keys():
                  forward=connections[recipient]
                  if forward!=0 and recipientDB.isShare(sender,query.getSensors()):
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
                 if forward!=0:
                    self.transport.write(query.getFULLSENZE(),forward)


   def DATASenze(self,query):
       global connections
       global database
       
       sender=query.getSender()
       usr=myUser(database,sender)
       recipients=query.getUsers()
       sensors=query.getSensors()
       for recipient in recipients:
           if recipient in connections.keys():
              recipientDB=myUser(database,recipient)
              #DATA msg queries will always deliverd
              if recipientDB.isAllow(sender,sensors) or "msg" in sensors:
                 forward=connections[recipient]
                 if forward!=0:
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
       senderDB=myUser(database,sender)
       pubkey=senderDB.loadPublicKey()
    
       if cmd=="SHARE" and "pubkey" in sensors and serverName in recipients:
          #Create a new account 
          self.createUser(query,address)
          validQuery=True

       elif cmd=="UNSHARE" and "pubkey" in sensors and serverName in recipients:
          #Remove the account
          status=False
          if pubkey !="":
             if cry.verifySENZE(query,pubkey):
                status=self.removeUser(sender,pubkey,address)
          validQuery=True

       else:
          if pubkey !="":
             if cry.verifySENZE(query,pubkey):
                validQuery=True

       if validQuery:
            connections[sender]=address
            connectionsTime[sender]=time.time()
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
            senze="DATA #msg SignatureVerificationFailed"
            senze=cry.signSENZE(senze)
            self.transport.write(senze, address)

   #Let's send a ping to keep open the port
   def sendPing(self,delay):
       global connections
       #print connections
       for recipient in connections:
           forward=connections[recipient]
           timeGap=time.time()-connectionsTime[recipient]
           #print timeGap
           #If there are no activities messages during in an hour, let's close the connection
           if (timeGap<3600):
              self.transport.write("PING",forward)
           else:
              connections[recipient]=0
           #   connectionsTime.pop(recipient,None)
       reactor.callLater(delay,self.sendPing,delay=delay)


   #This function is called when we start the protocol
   def startProtocol(self):
   	print "## SERVER STARTED ##"
        self.sendPing(20)


def init():
# If .servername is not there we will read the server name from keyboard
# else we will get it from .servername file
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

   # Here we will generate public and private keys for the server
   # These keys will be used to authentication
   # If keys are not available yet
   global serverPubkey
   try:
      cry=myCrypto(serverName) 
      if not os.path.isfile(cry.pubKeyLoc):
         # Generate or loads an RSA keypair with an exponent of 65537 in PEM format
         # Private key and public key was saved in the .servernamePriveKey and .servernamePubKey files
         cry.generateRSA(1024)
      serverPubkey=cry.loadRSAPubKey()
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
    print serverPubkey
    main()


