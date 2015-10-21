###############################################################################
##
##  A sample device driver v0.01
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

from random import randint
import datetime

#following variables will ve used to handle the GPIO ports
GPIOLock=False
GPIOStatus=[False,False,False,False,False,False,False,False,
False,False,False,False,False,False,False,False]

class myDriver:
  
   def __init__(self):
      GPIOLock=False
      #Set the public and private key locations
  

   #In order to read the sensor values, separate functions should be implemented. 
   #For example, if temperature sensor is available, read the value return it 
   def readTp(self):
      return randint(0,50)
      
   #If GPS is available, read the value return it         
   def readGPS(self):
      return randint(0,1000)
      
   #Read the device time and return it           
   def readTime(self):
       now = datetime.datetime.now()
       #print now.hour,now.minute,now.second
       return '%s,%s,%s' %(now.hour,now.minute,now.second)
       
   #Read the GPIO port status and return it           
   def readGPIO(self,port):
       global GPIOStatus
       if GPIOStatus[port]:return 'ON'
       else: return 'OFF'
  
   #In order to handle GPIO ports, following functions should be implemented. 
   #For example, if Senze-> PUT #gpio2 @device, then switch 2 will be turned ON.
   def handleON(self,port):
       global GPIOLock
       global GPIOStatus
       #This function should implement the necessary action before it returns the value
       #Wait if someone is accessing the gpio ports
       c=1
       while(GPIOLock):
         time.sleep(c)
         c+=1
         if c>10: return 'ERROR'
       GPIOLock=True
       #Here we should include the function to turn on the switch
       # TURN_ON() 
       GPIOStatus[port]=True
       GPIOLock=False
       return 'ON'
   
   #For example, if Senze -> :PUT #gpio2 @device, then switch will be turned OFF
   def handleOFF(self,port):
       global GPIOLock
       global GPIOStatus
       #This function should implement necessary action before it returns the value
       #Wait if someone is accessing the device
       c=1
       while(GPIOLock):
         time.sleep(c)
         c+=1
         if c>10: return 'ERROR'
       GPIOLock=True
       #Here we should include the function to turn off the switch
       # TURN_OFF() 
       GPIOStatus[port]=False
       GPIOLock=False
       return 'OFF'



sen=myDriver()
print sen.handleON(1)
print sen.handleOFF(1)
print sen.readTp()
print sen.readGPS()
print sen.readTime()

