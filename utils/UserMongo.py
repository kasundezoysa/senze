# My Senosr Server v1
# @Copyright by Kasun De Zoysa  MySensors Research Project
# University of Colombo School of Computing

import sys
import re
import os.path
import mmap
from pymongo import MongoClient
from myCrypto import *
import hashlib


class User:
   database=""
   usrDoc=""
   """ All database related operations are here
        putUser    - Check the availability of a user name and create it
        delUser    - Remove the given user
        login      - Read the pin/public key and handle the login 
        Share      - Sharing the sensors
        UnShare    - remove the share
        
   """
   def __init__(self,db,name):    
       self.database=db
       self.name=name
       doc=self.database.find_one({"name":self.name})
       if(doc):
           self.usrDoc=doc
       else:
          doc=""
    
   def putUser(self,name,phone,key,pubkey):
       #admin user is root. He can create main accounts.
       #The other users can create sub accounts.
       #Then the user name become main_account_name.subaccount_name
       uname=name
       if self.name!= "": 
          uname='%s.%s' %(self.name,name)
          owner=self.name
       else:
          owner="root"
       
       doc=self.database.find_one({"name":uname})
       if(doc):
          #if user name is already taken
          return False
       else:
          #The system support pin or public key based authentication.
          if pubkey!='':
             #It saves public key
             user = {"name":uname,"phone":phone,"publickey":pubkey,"owner":owner}
          else:
             #It saves SHA1 hash of the PIN
             s = hashlib.sha1()
             s.update(key)
             key=b64encode(s.digest())  
             user = {"name":uname,"phone":phone,"skey":key,"owner":owner}
          post_id = self.database.insert(user)
          return True

   def delUser(self,name,phone,key,pubkey):
       #Owners can login and delete their accounts.
       #Main accounts (owner=root) cannot delete right now.
       uname=name
       if self.name!= "":
          uname='%s.%s' %(self.name,name)
          owner=self.name
       else:
           owner="root"
       
       doc=self.database.find_one({"name":uname})
       #print uname
       if not (doc):
          #if the given user is not available
          return False
       else:
          if(self.usrDoc):
             post_id=self.database.remove({"name":uname,"owner":owner})
             return True
          else:
             return False
   
   def login(self,key,sig):
       #doc=db.find_one({"name":self.name,"skey":key})
       if(self.usrDoc):
           #PIN is compared with hash of the key 
           if 'skey' in self.usrDoc:
              s = hashlib.sha1()
              s.update(key)
              key=b64encode(s.digest())  
              if self.usrDoc['skey']==key:
                 return True
           #Signature will be verified with the public key
           elif 'publickey' in self.usrDoc:
               cry=MyCrypto("mysensors")
               if cry.verifySign(self.usrDoc['publickey'],sig,key):
                  return True
       return False
  
   def loadPublicKey(self):
       if(self.usrDoc):
          if 'publickey' in self.usrDoc:
             s=self.usrDoc['publickey']
             return str(s)
       return ''
  
   def loadData(self,name):
       if(self.usrDoc):
          if name in self.usrDoc:
             s=self.usrDoc[name]
             return str(','.join(s))
       return ''
  
   def logout(self):
       #This will call when user logout
       if(self.usrDoc):
           self.usrDoc=""
           return True
       else: return False

   """
   Following function will add recipient names to
   the sensor array in the user dictionary.
   It also add the sensor name to the recipient array in
   the recipient dictionary.
   """ 
   def share(self,recipient,sensors):
       # User should loged 
       if not (self.usrDoc): return False
       # Recipient should be available
       doc=self.database.find_one({"name":recipient})
       if not doc: return False
       
       for sensor in sensors:
           #Check the sensor is already in the shared list
           if not self.isShare(recipient,[sensor]):
              #check that the sensor was shared for someone else
              if sensor in self.usrDoc.keys():
                 self.usrDoc[sensor].append(recipient)
              else:
                 self.usrDoc[sensor]=[recipient]
                 
           #Tag recipient document
           # Check that user was shared anything else
           if self.name in doc.keys():
              if not sensor in doc[self.name]:
                 doc[self.name].append(sensor)
           else:
              doc[self.name]=[sensor]
       post_id = self.database.save(doc)
       post_id = self.database.save(self.usrDoc)
       return True
  
  
   """
   Following function will remove recipient names from
   the sensor array in the user dictionary.
   It also remove the sensor name from the recipient array in
   the recipient dictionary
   """ 
   def unShare(self,recipient,sensors):
       # User must be loged 
       if not (self.usrDoc): return False
       # Recipient should available
       doc=self.database.find_one({"name":recipient})
       if not doc: return False
      
       for sensor in sensors:
           #Check that the logged user was shared a sensor
           #If so remove recipient name from the senor dictionary
           if self.isShare(recipient,[sensor]):
              self.usrDoc[sensor].remove(recipient)
        
              #Remove shared tag from recipient document
              # Check that user was shared anything else
              if self.name in doc.keys():
                 if sensor in doc[self.name]:
                    doc[self.name].remove(sensor)
           
           #Check that the recipient was shared a sensor
           #If so remove the sensor name from the recipient dictionary 
           if self.isAllow(recipient,[sensor]):
              #print self.usrDoc[recipient]
              self.usrDoc[recipient].remove(sensor)
              
              #Remove shared tag from recipient document
              # Check that user was shared anything else
              if sensor in doc.keys():
                 if self.name in doc[sensor]:
                    #print doc[sensor]
                    doc[sensor].remove(self.name)
               
       post_id = self.database.save(doc)
       post_id = self.database.save(self.usrDoc)
       return True

   def isShare(self,recipient,sensors):
       if not (self.usrDoc): return False
       for sensor in sensors:
           if not sensor in self.usrDoc.keys(): return False
           if not recipient in self.usrDoc[sensor]: return False
       return True 
       
   def isAllow(self,sender,sensors):
       if not (self.usrDoc): return False
       for sensor in sensors:
           if not sender in self.usrDoc.keys(): return False
           if not sensor in self.usrDoc[sender]: return False
       return True 
   
   def countDocs(self):
       if not (self.usrDoc): return False
       return self.database.find().count() 
   

#Create connection to the Mongo DB
client = MongoClient('localhost', 27017)
#Creating the database

db = client['mysensors']
collection = db['users']
# Access the user collection from the mysensors database
usrDB = db.users
usr=User(usrDB,'meter')
print usr.countDocs()


rep=usr.loadData('lat')
pub=usr.loadPublicKey()
print pub
print rep
