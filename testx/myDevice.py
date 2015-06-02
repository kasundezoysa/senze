###############################################################################
##
##  A sample device client v0.01
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

from twisted.internet import reactor
#from autobahn.websocket import WebSocketClientFactory, WebSocketClientProtocol, connectWS
from autobahn.twisted.websocket import WebSocketClientProtocol, \
                                      WebSocketClientFactory
from twisted.internet.protocol import ReconnectingClientFactory
from twisted.python import log
from twisted.internet import reactor

import thread
import time
import sys
import os.path
import urllib2
lib_path = os.path.abspath('../utils')
sys.path.append(lib_path)
from myParser import *
from myCrypto import *
from myDriver import *
#from myCamDriver import *
import re
import hashlib
from PIL import Image

state="INITIAL"
Reconnect=False
pubkey=""

#ServerName="connect.mysensors.mobi"
ServerName="localhost"
Port=8080
pin=""

def check_connectivity(reference):
  try:
     response=urllib2.urlopen('http://74.125.228.100',timeout=1)
     print "Network is ready."
     return True
  except urllib2.URLError:
     print "Network connectioned was failed. Trying..."
     time.sleep(randint(0,30))
     check_connectivity(reference)
    

class MyClientProtocol(WebSocketClientProtocol):
  #Response to sec-websocket-key will save here
   key=''
   pingCount=0
   pingingIntervel=30
   
   #Save base64 encoded jpg photo in the given file
   def savePhoto(self,b64photo,filename):
      f = open(filename,"w")
      if b64photo:
         data = b64decode(b64photo)
         f.write(data) 
      f.close()

   #Show image
   def showPhoto(self,filename):
      image = Image.open(filename)
      image.show()

   #read SENZE
   def readSENZE(self):
       print "Hello kasun"
       senze=raw_input("Enter the SENZE: ")

   #Ping and pong messages will be used to keep the active connection.
   def onPing(self,payload):
     print "Received a ping message "
     self.pingCount+=1
     self.sendPong(payload=None)
     print "Send the pong message"

   #Ping message will not count, something went wrong.
   #So we close the connection. 
   def checkPingMessage(self):
      if(self.pingCount<=0):
         self.sendClose()
         self.pingCount=0   
      else:
         self.pingCount-=1
         print self.pingCount
         self.factory.reactor.callLater(self.pingingIntervel+5,self.checkPingMessage)
             
   def onClose(self,wasClean,code,reason):
      print('The connection was closed. Reason: {}'.format(reason))
    
   def onConnect(self, response):
      print("Server connected: {}".format(response.peer))
      self.key=response.headers['sec-websocket-accept']
      #print response.headers
      print self.key
  
   def onOpen(self):
      global state
      global device
      global pin
      global pubkey
      global server
      
      print("Connecting to the websocket server...")
      cry=myCrypto(name=device) 
      #If system is at the initial state, it will send the device creation Senze
      #The otherwise, it will send the login Senze
      if state=='INITIAL':
          if pin!="":
             #Hash of the pin will be calculated
             s = hashlib.sha1()
             s.update(pin)
             h = s.digest()
             pin=b64encode(h)
             response ='PUT #name %s #email kasun@ucsc.lk #hkey %s @%s' %(device,pin,server)
          else:
             signature=cry.signData(data=device);
             response ='PUT #name %s #pubkey %s #signature %s @%s' %(device,pubkey,signature,server)
      elif state=='LOGIN':
          if pin!="":
             #pin= H(pin+self.key) will be calculated
             s = hashlib.sha1()
             s.update(pin+self.key)
             h = s.digest()
             hkey=b64encode(h)
             response ='LOGIN #name %s #hkey %s @%s' %(device,hkey,server)
          else:
             #sec-websocket-accept will be digitally signed
             signature=cry.signData(data=self.key);
             response ='LOGIN #name %s #signature %s @%s' %(device,signature,server)
      self.sendMessage(response)
  
   #Senze response should be built as follows by calling the functions in the driver class
   def sendDataSenze(self,sensors,data,recipient):
       response='DATA'
       device=myDriver()
       for sensor in sensors:
           #If temperature is requested
           if "tp" == sensor:
              response ='%s #tp %s' %(response,device.readTp())
           #If time is requested
           elif "time" == sensor:
              response ='%s #time %s' %(response,device.readTime())
           #If gps is requested 
           elif "gps" == sensor:
              response ='%s #gps %s' %(response,device.readGPS())
           #If gpio is requested 
           elif "gpio" in sensor:
              m=re.search(r'\d+$',sensor)
              pinnumber=int(m.group())
              print pinnumber
              response ='%s #gpio%s %s' %(response,pinnumber,device.readGPIO(port=pinnumber))
           else:
              response ='%s #%s NULL' %(response,sensor)
        
       response="%s @%s" %(response,recipient)
       
       #Data can be encrypted as follows
       #aes256=myCrypto("device1")
       #aes256.generateAES("123456")
       #enc=aes256.encrypt(response)
       cry=myCrypto(recipient)
       enc=cry.encryptRSA(response)
       response="DATA #cipher %s @%s" %(enc,recipient)
       print response
       self.sendMessage(payload=response)

   #Handle the GPIO ports by calling the functions in the driver class
   #If value is one, switch will be turned on, otherwise it will be turned off
   def handlePUTSenze(self,sensors,data,recipient,value):
       response='DATA'
       device=myDriver()
       for sensor in sensors:
          #If GPIO operation is requested
          if "gpio" in sensor:
              pinnumber=0
              #search for gpio pin number
              m=re.search(r'\d+$',sensor)
              if m :
                 pinnumber=int(m.group())
            
              if pinnumber>0 and pinnumber<=16:
                 if value==1: ans=device.handleON(port=pinnumber)
                 else: ans=device.handleOFF(port=pinnumber)
                 response='%s #gpio%s %s' %(response,pinnumber,ans)
              else: 
                 response='%s #gpio%d UnKnown' %(response,pinnumber)
          else:
              response='%s #%s UnKnown' %(response,sensor)
          
          response="%s @%s" %(response,recipient)
          self.sendMessage(payload=response)
    

   #This section handles Senzes
   def onMessage(self, msg, binary):
      global device
      global cam
      global server
      global state
      global Reconnect
      
      print "Got a senze: " + msg
      #Parse the Senze
      parser=myParser(msg)
      recipients=parser.getUsers()
      reply=parser.getReply()
      data=parser.getData()
      sensors=parser.getSensors()
      cmds=parser.getCmds()
      conds=parser.getConds()
   
      cry=myCrypto(device)
      #Received the cipher SENZE, it can be decrypted as follows
      if 'DATA' in cmds and 'cipher' in sensors:
         try:
            #cry.generateAES("123456")
            #dec=cry.decrypt(data['cipher'])
            dec=cry.decryptRSA(data['cipher'])
            print dec
            #We have to parse the Senze again
            parser=myParser(dec)
            recipients=parser.getUsers()
            reply=parser.getReply()
            data=parser.getData()
            sensors=parser.getSensors()
            cmds=parser.getCmds()
            conds=parser.getConds()
            
         except:
            print "Decyption Failed"
    
    
      if 'DATA' in cmds:
         #If the device receives a public key, it will be saved in a file
         if 'pubkey' in sensors:
             if 'websocketkey' in data:
               #Should use this as the session key
               self.key=data['websocketkey']
               
               print self.key
              
             recipient=recipients.pop(0)
             if  state=='INITIAL' or  state=='LOGIN':
                 #Since the first public key is the server public key
                 #the recipient name will be taken as the server name.
                 server=recipient
             loc="."+recipient+"PubKey.pem"
             #If the device already has the pubic key, ignore it
             if not os.path.isfile(loc):
                if 'pubkey' in data:
                   serverPubKey=data['pubkey']
                   cry.saveRSAPubKey(publicKeyLoc=loc,pubkey=serverPubKey)
             else:
                   serverPubKey=b64encode(open(loc,"r").read())
                   
             #Here we handle the server authentication 
             if 'signature' in data:
                if not (cry.verifySign(serverPubKey,data['signature'],self.key)):
                   print "Server authentication was failed."
                   reactor.stop() 
                else:
                   print "Server authentication was successfull."
             else:
                print "Unknown server."
               
         elif 'photo' in sensors:
               try:
                  self.savePhoto(data['photo'],"p1.jpg")
                  thread.start_new_thread(self.showPhoto,("p1.jpg",))
               except:
                  print "Error: unable to show the photo"
               #cam.savePhoto(data['photo'],"p1.jpg")
   
         elif 'msg' in sensors:
        
            if data['msg']=='LoginSUCCESS':
                status='READY'
                print "Welcome "+device
                #Read Senzes from SENZES file and distribute it in 5 seconds intervals
                #We should not send them back
                if not Reconnect:
                   if os.path.isfile('SENZES'):
                      #The Senzes will be read form the SENZE file
                      f=open("SENZES","r")
                      lines = f.readlines()
                      t=0
                      for line in lines:
                          if not line.startswith("#"):
                             senze=line.rstrip("\n")
                             t+=2
                             self.factory.reactor.callLater(t,self.sendMessage,payload=senze,isBinary=False)
                     
                print 'Sending a ping message in very minute to keep the live connection.'
                self.factory.reactor.callLater(self.pingingIntervel+5,self.checkPingMessage)
                print 'Waiting for Senzes.....'
                #thread.start_new_thread(self.readSENZE,())
            
            elif 'UserCreated' in data['msg']:
                #Creating the .devicename file and store the device name and PIN  
                f=open(".devicename",'w')
                f.write(device+'\n')
                if(pin!=""):
                     f.write(pin+'\n')
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
         
            elif data['msg']=='PUTDone':
                print 'OK: PUT senze was delivered.'

            elif data['msg']=='ShareDone':
                print 'OK: The sensor was shared.'
        
            elif 'GETSendFailed' in data['msg']:
                print 'ERROR: Sending the GET senze was failed.'
           
            elif 'UnsupportedSenzeType' in data['msg']:
                print 'ERROR: Unsupported Senze'
              
            elif 'ShareFailed' in data['msg']:
                print "ERROR: Sharing the sensor was failed."
     
            elif data['msg']=='LoginFAILED':
                print "ERROR: The login failed. The system halted!"
                reactor.stop()       
            else:
                print data['msg']
            
      #If GET Senze was received. The device must handle it.
      elif "GET" in cmds:
         rep=recipients.pop(0)
         if "FOR" in conds.keys():
            n=int(conds["FOR"])
            for i in xrange(1,n+1):
                self.factory.reactor.callLater(1,self.sendDataSenze,sensors=sensors,data=data,recipient=rep)
         elif "IF" in conds.keys():
            if checkCon(conds["IF"]):
                self.factory.reactor.callLater(1,self.sendDataSenze,sensors=sensors,data=data,recipient=rep)
         else:
            self.factory.reactor.callLater(1,self.sendDataSenze,sensors=sensors,data=data,recipient=rep)
    
      #If PUT Senze was received. The device must handle it.
      elif "PUT" in cmds:
         rep=recipients.pop(0)
         if "IF" in conds.keys():
            if checkCon(conds["IF"]):
               self.factory.reactor.callLater(1,self.handlePUTSenze,sensors=sensors,data=data,recipient=rep,value=1)
         else:
               self.factory.reactor.callLater(1,self.handlePUTSenze,sensors=sensors,data=data,recipient=rep,value=1)
    
      #If :PUT Senze was received. The device must handle it.
      elif ":PUT" in cmds:
         rep=recipients.pop(0)
         if "IF" in conds.keys():
            if checkCon(conds["IF"]):
               self.factory.reactor.callLater(1,self.handlePUTSenze,sensors=sensors,data=data,recipient=rep,value=0)
         else:
            self.factory.reactor.callLater(1,self.handlePUTSenze,sensors=sensors,data=data,recipient=rep,value=0)



# ReconnectingClientFactory class will handle the lost connections
class MyClientFactory(ReconnectingClientFactory,WebSocketClientFactory):
   protocol = MyClientProtocol
   maxDelay = 30
   maxRetries = 1000

   def startedConnecting(self, connector):
     print('Started to connect.')

   def clientConnectionLost(self, connector, reason):
      print('Lost connection. Reason: {}'.format(reason))
      ReconnectingClientFactory.clientConnectionLost(self, connector, reason)

   def clientConnectionFailed(self, connector, reason):
      print('Connection failed. Reason: {}'.format(reason))
      ReconnectingClientFactory.clientConnectionFailed(self, connector, reason)


if __name__ == '__main__':
   #Following two variables will be used to store server and device name.
   server='mysensors'
   device='mydevice'
   #cam=myCamDriver()

   #If .device name is not there, we will read the device name from keyboard
   #else we will get it from .devicename file
   try:
      if not os.path.isfile(".devicename"):
         device=raw_input("Enter the device name:")
         pin=raw_input("Enter the PIN (For pubkey authntication, just press the RETURN key):")
         # Account need to be created at the server
         state='INITIAL'
      else:
         #The device name will be read form the .devicename file
         f=open(".devicename","r")
         device = f.readline().rstrip("\n")
         pin = f.readline().rstrip("\n")
         state='LOGIN'
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
   check_connectivity(ServerName)

   try:
     #Web socket client is connecting to the public server
     log.startLogging(sys.stdout)
     #factory = WebSocketClientFactory("ws://"+ServerName+":"+str(Port),debug = False)
     #factory.protocol = MyClientProtocol
     factory = MyClientFactory("ws://"+ServerName+":"+str(Port),debug = False,debugCodePaths = False)
     reactor.connectTCP(ServerName,Port,factory)
     reactor.run()
   except:
      print "ERRER: Cannot connect the server."
      raise SystemExit

   
