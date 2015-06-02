# My Senosr Server v0.01
# @Copyright by Kasun De Zoysa  MySensors Research Project
# University of Colombo School of Computing

import sys
import re
import os.path
import mmap

# All user configuration files will be created under the following directory.
userHome= "../users/"

class User:
   """ All user related operations are here
        checkUser  - Check the availability of a user
        checkPass  - check the PIN number
        addShare   - create a file in the user directory with the sensor name
                   - add recipient name to the file
        deleteShare- remove the recipient name from the sensor file in the user directory
   """
   def __init__(self,name):
       self.name=name
       self.path=userHome+self.name+"/"

   def checkUser(self):
       if os.path.exists(self.path+"pass"):
         return True
       else: return False

   def checkPass(self,key):
       try:
         #print self.path
         f=open(self.path+"pass")
         line=f.readline()
         f.close()
         #print line
         t=line.strip().split(':')
         if t[1]==key: return True
         else: return False
       except:
         return False
   """
   Following function will add recipient names to
   the sensor files in the user directory.
   """ 
   def addShare(self,recipient,sensors):
       try:
         for sensor in sensors:
             if not os.path.exists(self.path+sensor):
                  f=open(self.path+sensor,'w')
                  f.write(recipient+"\n")
                  f.close()
             else:
                  if recipient not in open(self.path+sensor).read():
                     f=open(self.path+sensor,'a')
                     f.write(recipient+"\n")
                     f.close()
         return True
       except:
         return False
   
   """
   Following function will remove recipient names from
   the sensor files in the user directory.
   """
   def deleteShare(self,recipient,sensors):
       try:
         for sensor in sensors:
             f = open(self.path+sensor,"r")
             lines = f.readlines()
             f.close()
             if recipient+"\n" in lines:
                f=open(self.path+sensor,'w')
                for line in lines:
                    if line!=recipient+"\n": f.write(line)
                f.close()
         return True
       except:
         return False

   """
   Check the given user name is available in the
   sensor file in the user directory.
   """
   def isAllow(self,sender,sensors):
       try:
         for sensor in sensors:
             if sender in open(self.path+sensor).read():       
                return True
         return False
       except:
         return False
   
   def checkStr(self,str):
     # f = open(self.path+"allow")
      if str in open(self.path+"allow").read():
         return True
      else: return False
      #s = mmap.mmap(f.fileno(), 0, access=mmap.ACCESS_READ)
      #if str in s: return True
      #else: return False
    
   def readSensor(self,name):
      if os.path.exists(self.path+name):
         values = [line.strip() for line in open(self.path+name)]
      else:
         values=[]
      return values

"""
u=User("kasun")
u1=User("u1")
if u.checkPass("1234"):
   print "OK"
else: print "FAIL"
if u.addShare("u2",["tp","gps"]):
#if u.deleteShare("u3",["tp","gps"]):
   print "Share deleted"
else: print "FAIL delete"
"""