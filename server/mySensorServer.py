###############################################################################
##
##  My Sensor Server v1.0
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

import sys
import os.path

lib_path = os.path.abspath('../utils')
sys.path.append(lib_path)
from myParser import *
from myUser import *
from myCrypto import *

from twisted.internet import reactor
from twisted.python import log
from base64 import b64encode, b64decode 
import hashlib


from autobahn.twisted.websocket import WebSocketServerProtocol, \
                                       WebSocketServerFactory
from twisted.python import log
from twisted.internet import reactor

#Server address and port number should be assigned here
#SERVER_URL="ws://connect.mysensors.mobi:8080"
SERVER_URL="ws://localhost:8080" 
PORT=8080

# manage connection in a dictionary, we save connection along with user/device name
connections={}
deletedConnections={}
#These variables will be used to keep the server name and its public key
serverName=""
pubkey=""
#Database connection will be kept here
usrDatabase=""

# Here we implement the mySensor Protocol
# Social Language for IoT
class MySensorProtocol(WebSocketServerProtocol):
   """
    Sensors server to manage websocket connections, basically create wesocket
    connection and listen to it.  Incoming senzes are processed by a  myParser and 
    delegate task to approprite manager according to senze type.
   """
   # Keep the connection state 
   myState="INITIAL"
   # Keep the connected user name 
   user=""
   
   #ping messages will help to keep the live connection.
   #If server won't get a response within a pingingIntervel (pingCount>0), 
   #it will close the connection.
   pingCount=0
   pingingIntervel=60
   
   #Response to sec-websocket-key will save here
   key=''
  
   #Keep the server detail
   server=""
   publicKey=""
   usrDB=""
        
   def onConnect(self, request):
      print("Client connecting: {}".format(request.peer))
      #Key calculate here will be used in the login process as the session key. 
      cc = '258EAFA5-E914-47DA-95CA-C5AB0DC85B11'
      key=request.headers['sec-websocket-key']
      s = hashlib.sha1()
      s.update(key+cc)
      h = s.digest()
      self.key=b64encode(h)
      #print self.key
      
   def onOpen(self):
       '''
       Call when opening a websocket.
       Initializing the all globle parameters here
       '''
       global serverName
       self.server=serverName
       global pubkey
       self.publicKey=pubkey
       global usrDatabase
       self.usrDB=usrDatabase
       
       print "Total no of connections:"+str(factory.getConnectionCount())
       self.myState="INITIAL"
       #The server sends its public key and
       #signature of websocket key. So the clients can verify the server authenticity.
       cry=myCrypto(serverName) 
       sig=cry.signData(self.key)
       msg="@"+self.server+" DATA #pubkey "+self.publicKey
       msg+=" #websocketkey "+self.key+" #signature "+sig
       self.sendMessage(msg,False)

   def onClose(self,wasClean,code,reason):
       global connections
       global deletedConnections
       """
       Call when closing the websocket, so need to
            1. Reset all globle parametes and connections
            2. Remove connections from connection pool
       """
       self.mysate="INITIAL"
       if self.user in deletedConnections:
             del deletedConnections[self.user]
       elif self.user in connections: 
             del connections[self.user]
       print self.user + " closed the connection"

        
   def onPong(self,payload):
     print "Pong message received "+payload
     #If pong message was received, set the counter back to 0 
     self.pingCount-=1
     #print self.pingCount
     #Send a ping message again after 10m
     if(self.pingCount==0):
       self.factory.reactor.callLater(self.pingingIntervel*2,self.sendPingMessage)
  
  
   def sendPingMessage(self):
       global connections
       #If we did not receive pong message, count should be >0
       #So we close the connection 
       if(self.pingCount>0):
          if self.user in connections: 
             connections[self.user].sendClose()
             del connections[self.user]
             self.mysate="INITIAL"
       else:
          #We send a ping message again
          print "SEND a ping message"
          self.pingCount+=1
          self.sendPing(payload=None)


   def onMessage(self, msg, binary):
       replyMsg="@"+self.server+" DATA #msg "
       print msg
       """
        Call when receiving a message to the listning websocket
        Message will be parsed by the  myParser and delegate the task to appropriate
        manages according to Parser resuslt(result will be myParse object).
        Following tasks can be performed according to Parser result
            1. LOGIN - Login user to system :LOGIN - Logout user from the system
            2. SHARE/:SHARE - Share data between users, manage Share request
            3. GET - Request data from the shared sensors
            4. PUT/:PUT - Create users at mysensors and Control the shared sensors
            5. DATA - Inform the message delivery status and requested data
       """
       parser=myParser(msg)
       recipients=parser.getUsers()
       reply=parser.getReply()
       data=parser.getData()
       sensors=parser.getSensors()
       cmds=parser.getCmds()
       
       if self.myState=="INITIAL":
          if "LOGIN" in cmds:
             #Handle the login process
             self.handle_LOGIN(data)
          elif "PUT" in cmds:
             if self.server in recipients:
                #Create a new account 
                self.handle_PUT_MySensors("PUT",recipients,sensors,data,reply)
             else:
                self.sendMessage(replyMsg+"YouShouldLogFirst",False)
    
          elif "GET" in cmds:
             #Response with a public key of a server or a device
             if 'pubkey' in sensors:
                self.handle_GET_PublicKey(recipients,reply)
             elif self.server in recipients:
                self.handle_GET_MySensors("PUT",recipients,sensors,data,reply)
             else:
                self.sendMessage(replyMsg+"YouShouldLogFirst",False)
          else:
             self.sendMessage(replyMsg+"YouShouldLogFirst",False)
    
    
       elif self.myState=="READY":
         if ":LOGIN" in cmds:
             self.handle_LOGOUT(data)
         elif "SHARE" in cmds:
             self.handle_SHARE(recipients,sensors,reply)
         elif ":SHARE" in cmds:
             self.handle_UNSHARE(recipients,sensors,reply)
         elif "PUT" in cmds:
             if self.server in recipients:
                 self.handle_PUT_MySensors("PUT",recipients,sensors,data,reply)
             else:
                 self.handle_PUT("PUT",recipients,sensors,data,reply)
         elif ":PUT" in cmds:
             if self.server in recipients:
                self.handle_PUT_MySensors(":PUT",recipients,sensors,data,reply)
             else:
                self.handle_PUT(":PUT",recipients,sensors,data,reply)
                
         elif "GET" in cmds:
            if 'pubkey' in sensors:
                self.handle_GET_PublicKey(recipients,reply)
            elif self.server in recipients:
                self.handle_GET_MySensors(recipients,sensors,data,reply)
            else:
                self.handle_GET(recipients,sensors,reply)
            
         elif "DATA" in cmds:
             self.handle_DATA(recipients,sensors,reply)
         else:
             self.sendMessage(replyMsg+"UnsupportedQueryType",False)
       else:
         self.mysate="INITIAL"
         self.sendMessage(replyMsg+"YouShouldLogFirst",False) 


   def isConnected(self,recip):
       global connections
       if recip in connections:
          return True
       else:
          return False


   def handle_LOGOUT(self,data):
       global connections
       """
        This method handles logout process of each user.
       """
       if self.user in connections:
          connections[self.user].sendClose()
          self.mysate="INITIAL"

   def handle_LOGIN(self,data):
       print data
       global connections
       global deletedConnections
       """
        This method handles login process of each user.
        At present user connection socket id is stored in 'connections'.
        Finally we create a DATA Senze and send it to corresponding user, DATA
        Senze contains Login success/fail status.
        We authenticate users by using a PIN number or a digital signature.
       """
       name=''; pin='';sig=''
       if 'name' in data: name= data['name']
       if 'skey' in data: pin= data['skey']
       if 'hkey' in data: pin= data['hkey']
      
       # If PIN is encrypted, it should be decrypted.
       if 'enckey' in data:
           cry=myCrypto(self.server)
           pin= cry.decryptRSA(data['enckey'])
           #print pin
       # If hkey is given, #sec-websocket-key is taken as the session key.
       elif 'hkey' in data:
           #sec-websocket-key is used as the session key
           sig=self.key
           pin=data['hkey']
           #print pin
       # Signature is available, the user authentication is based on digital signature.
       elif 'signature' in data: 
           sig=data['signature']
           #sec-websocket-key is used as the pin
           pin=self.key

       usr=myUser(self.usrDB,name)
       replyMsg="@"+self.server+" DATA #name "+name
       
       #Verify the user by using a PIN or signature
       if usr.login(pin,sig,self.server): 
           # We need to check user alredy have a connection 
           if self.isConnected(name):
             #Let's close it
             deletedConnections[name]=connections[name]
             connections[name].sendClose()
        
           # Set the connected name
           self.user=name
           # Adding websocket connection to connection pool
           connections[self.user]=self
           
           self.myState="READY"
           replyMsg+=" #msg LoginSUCCESS"
           self.sendMessage(replyMsg,False)
           
           #In order to keep the live  connection, the server will send a ping after 5m
           #After that the server will send a ping every 10m (See onPong message)  
           self.factory.reactor.callLater(self.pingingIntervel,self.sendPingMessage)
           self.factory.reactor.callLater(self.pingingIntervel*2,self.sendPingMessage)
       
       
       #If login failed, let's inform it
       if self.myState=="INITIAL":
          replyMsg+=" #msg LoginFAILED"
          self.sendMessage(replyMsg,False)


   def handle_SHARE(self,recipients,sensors,reply):
       global connections
       replyMsg="@"+self.server+" DATA #msg "
 
       """
        In order to start the sharing process both users need to logged in to the system.
        For a instance, if query comes 'SHARE #tp @user2' from the user1.
        First we need to verify that user2 is logged in.
        Then mysensors adds "user2" to the sensor dictionary at user1's document and
        sensor name to the "user1" dictionary at user2's document.
        Finally it delivers the message @user1 SHARE #tp to user2.
        If all process works, mysensors also sends @mysensors DATA #msg ShareDone to user1.
        Otherwise it sends @mysensors DATA #msg ShareFailed to user1.
       """
       failed_recipients=[]
       usr=myUser(self.usrDB,self.user)
       for recipient in recipients:
           if self.isConnected(recipient):
               connections[recipient].sendMessage("@"+self.user+reply,False)
               usr.share(recipient,sensors)
           else:
               failed_recipients.append(recipient)
         
       if len(failed_recipients)==0:
          self.sendMessage(replyMsg+"ShareDone",False)
       else:
          self.sendMessage(replyMsg+"ShareFailed:"+str(failed_recipients),False)

 
   def handle_UNSHARE(self,recipients,sensors,reply):
       """
        If message comes ':SHARE #tp @user2' from the user1,
        First we need to verify that user2 is logged in.
        Then mysensors removes  "user2" from the sensor dictionary at user1's document and
        the sensor name from the "user1" dictionary at user2's document.
        
        If user2 also shared the same sensor to user1, 
        mysensors removes the sensor name from user2 dictionary at user1's document
        and "user2" from the sensor dictionary at user2's document.
        
        Finally it delivers the query @user1 :SHARE #tp to user2.
        If all process works, mysensors sends @mysensors DATA #msg :ShareDone to user1.
        Otherwise it sends @mysensors DATA #msg :ShareFailed to user1.   
       """
       global connections
       replyMsg="@"+self.server+" DATA #msg "
 
       failed_recipients=[]
       usr=myUser(self.usrDB,self.user) 
       for recipient in recipients:
           if self.isConnected(recipient):
               connections[recipient].sendMessage("@"+self.user+reply,False)
               usr.unShare(recipient,sensors)
           else:
               failed_recipients.append(recipient)

       if len(failed_recipients)==0:
          self.sendMessage(replyMsg+":ShareDone",False)
       else:
          self.sendMessage(replyMsg+":ShareFailed:"+str(failed_recipients),False)


   def handle_PUT_MySensors(self,cmd,recipients,sensors,data,reply):
       status=False
       usr=myUser(self.usrDB,self.user)
       cry=myCrypto(self.server)
       type='skey'
    
       n=''; k=''; p='';pub='';sig='';e=''
       if 'name' in data: n= data['name']
       if 'skey' in data: k= data['skey']
       if 'hkey' in data:
           k= data['hkey']
           type='hkey'
       # If PIN is encrypted, it should be decrypted.
       if 'enckey' in data:
           k= cry.decryptRSA(data['enckey'])
           #print k
       if 'pubkey' in data and 'signature' in data:
           pub=data['pubkey']
           sig=data['signature']
           type='pubkey'
       if 'phone' in data: p= data['phone']
       if 'email' in data: e= data['email']
     
       st='@%s DATA #name %s #msg ' %(self.server,n)
       if cmd=='PUT':
          if type=='pubkey':
              if cry.verifySign(pub,sig,n):
                 status=usr.putUser(n,p,e,pub,type)
              else:
                  status=False                
          else:
              status=usr.putUser(n,p,e,k,type)
          
          if status:
             st+='UserCreated'
          else:
             st+='UserCreationFailed'
       else:
          status=usr.delUser(n,p,k,pub)
          if status:
             st+='UserDeleted'
          else:
             st+='UserDeletionFailed'

       self.sendMessage(st,False)


   def handle_PUT(self,cmd,recipients,sensors,data,reply):
       global connections
      
       failed_recipients=[]
       status=False
       usr=myUser(self.usrDB,self.user)
          
       #PUT message will forward to the recipients     
       for recipient in recipients:
          if self.isConnected(recipient):
              rep=myUser(self.usrDB,recipient)
              if rep.isShare(self.user,sensors):
                 connections[recipient].sendMessage("@"+self.user+reply,False)
                 status=True
              else:
                  failed_recipients.append(recipient)
          else:failed_recipients.append(recipient)

       st='@%s DATA #msg %s' %(self.server,cmd)
       if status:
          st+='Done'
          self.sendMessage(st,False)
       else:
          st+='Failed'
          self.sendMessage(st+str(failed_recipients),False)


   def handle_GET(self,recipients,sensors,reply):
       global connections
       failed_recipients=[]
       """
       print "R->",recipients
       print "Reply->",reply
       print "S->",sensors
       """
         
       #If GET addresses to the mysensors   
       if self.server in recipients:
          if 'pubkey' in sensors:
              cry=myCrypto(self.server)
              publicKey=cry.loadRSAPubKey()
              st='@%s DATA #pubkey %s' %(self.server,publicKey)
              self.sendMessage(st,False)
      
       #Otherwise GET message will forward to the recipients     
       else:
           for recipient in recipients:
              if self.isConnected(recipient):
                 rep=myUser(self.usrDB,recipient) 
                 if rep.isShare(self.user,sensors):
                    connections[recipient].sendMessage("@"+self.user+reply,False)
                 else:
                    failed_recipients.append(recipient)
              else:failed_recipients.append(recipient)
    
           st='@%s DATA #msg ' %(self.server)
           if len(failed_recipients)==0:
              self.sendMessage(st+"GETSendDone",False)
           else:
              self.sendMessage(st+"GETSendFailed:"+str(failed_recipients),False)


   def handle_GET_PublicKey(self,recipients,reply):
       
       for recipient in recipients:
           #If public key of the server     
           if self.server in recipient:
              if publicKey!='':
                 response='@%s DATA #pubkey %s' %(self.server,self.publicKey)
                 self.sendMessage(response,False)
              else:
                 response='@%s DATA #msg PublickeyNotFound' %(self.server)
                 self.sendMessage(response,False)
           else:
              #Since mysensors already has public key of it clients,
              #it responses on behalf of the client.
              rep=myUser(self.usrDB,recipient) 
              pub=rep.loadPublicKey()
              if pub!='' :
                 response='@%s DATA #pubkey %s' %(recipient,pub)
                 self.sendMessage(response,False)
              else:
                 response='@%s DATA #msg PublickeyNotFound' %(recipient)
                 self.sendMessage(response,False)


   def handle_GET_MySensors(self,recipients,sensors,data,reply):
      
       usr=myUser(self.usrDB,self.user)
       #Check the given user is online or offline
       #GET #name kasun @mysensors -> @mysenosrs DATA #name kasun ONLINE/OFFLINE
       if 'name' in sensors:
          if 'name' in data.keys():
             if self.isConnected(data['name']):
                response='@%s DATA #name %s #msg ONLINE' %(self.server,data['name'])
             else:
                response='@%s DATA #name %s #msg OFFLINE' %(self.server,data['name'])
          else:
               response='@%s DATA #name #msg UnKnown' %(self.server)
       #Return the list of friends who shared the given sensor with me
       #GET #friends #shared tp @mysensors -> @mysenosrs DATA #friends kasun,nimal #shared tp
       elif 'friends' in sensors:
           if 'shared' in data.keys():
              rep=usr.loadFriends(data['shared'])
              response='@%s DATA #friends %s #shared %s' %(self.server,rep,data['shared'])
           else:
               #Return the list of friends who registered with the server
               #GET #friends kasun,d1,nimal -> @mysenosrs DATA #friends kasun,nimal
               if 'friends' in data.keys():
                  rep=usr.findUsers(data['friends'])
                  response='@%s DATA #friends %s' %(self.server,rep)
               else:
                 response='@%s DATA #sensor #msg UnKnown' %(self.server)
       #Return the list of friends where I shared the given sensor
       #GET #shared tp @mysensors -> @mysenosrs DATA #shared tp #friends kasun,nimal
       elif 'shared' in sensors:
           if 'shared' in data.keys():
              rep=usr.loadData(data['shared'])
              response='@%s DATA #shared %s #friends %s' %(self.server,data['shared'],rep)
           else:
              response='@%s DATA #sensor #msg UnKnown' %(self.server)
    
       #Return the list of sensors shared by the given friend
       #GET #friend nimal @mysensors -> @mysenosrs DATA #friend nimal #shared gps,tp
       elif 'friend' in sensors:
           if 'friend' in data.keys():
              rep=usr.loadData(data['friend'])
              response='@%s DATA #friend %s #shared %s' %(self.server,data['friend'],rep)
           else:
              #Need to return name of friends who shared sensor here
              response='@%s DATA #friend #msg UnKnown' %(self.server)
       #Return the number of connections at the given time
       #GET #connections @mysensors -> @mysenosrs DATA #connections 5
       elif 'connections' in sensors:
             num=str(factory.getConnectionCount())
             response='@%s DATA #connections %s' %(self.server,num)
       #Return the number of users at the given time
       #GET #users @mysensors -> @mysenosrs DATA #users 1000
       elif 'users' in sensors:
             num=str(usr.countDocs())
             response='@%s DATA #users %s' %(self.server,num)
       else:
             response='@%s DATA #msg UnsupportedSenzeType' %(self.server)
       self.sendMessage(response,False)
  
  
   def handle_DATA(self,recipients,sensors,reply):
       global connections
       failed_recipients=[]
       ''' 
       print "R->",recipients
       print "Reply->",reply
       '''
       for recipient in recipients:
         if self.isConnected(recipient):
            rep=myUser(self.usrDB,recipient) 
            if rep.isAllow(self.user,sensors):
                connections[recipient].sendMessage("@"+self.user+reply,False)
            else:failed_recipients.append(recipient)
         else:failed_recipients.append(recipient)

       response='@%s DATA #msg ' %(self.server)
       if len(failed_recipients)==0:
          self.sendMessage(response+"DATASendDone",False)
       else:
          self.sendMessage(response+"DATASendFailed:"+str(failed_recipients),False)


if __name__ == '__main__':

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
   print pubkey

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

#Starting the Web socket server..
   log.startLogging(sys.stdout)
   factory = WebSocketServerFactory(SERVER_URL,debug = False)
   #factory.setProtocolOptions(openHandshakeTimeout = 5)
   factory.protocol = MySensorProtocol
   reactor.listenTCP(PORT,factory)
   reactor.run()

