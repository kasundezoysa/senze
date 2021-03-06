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
#import pygame
import pygame.camera
from PIL import Image
from pygame.locals import *
from base64 import b64encode, b64decode 
import thread
import os.path


class myCamDriver:
   cam=""
   img=""

   def __init__(self):
      pygame.camera.init()
      camlist = pygame.camera.list_cameras()
      print camlist
      if camlist:
         self.cam = pygame.camera.Camera(camlist[0],(160,120))

   #Read the device time and return it           
   def readTime(self):
       now = datetime.datetime.now()
       #print now.hour,now.minute,now.second
       return '%s,%s,%s' %(now.hour,now.minute,now.second)

   #Take the photo           
   def takePhoto(self):
      if self.cam:
         self.cam.start()
         self.img = self.cam.get_image()
         self.cam.stop()
   
   #Save it
   def savePhoto(self,b64photo,filename):
      #pygame.time.wait()
      f = open(filename,"w")
      if b64photo:
         data = b64decode(b64photo)
         f.write(data) 
      f.close()

   #Read b64encode photo
   def readPhotob64(self):
       if self.img:
          pygame.image.save(self.img,"tmp.jpg")
          photo = open("tmp.jpg","r").read()
          return b64encode(photo)
       return 0 

   #Show image
   def showPhoto(self,filename):
       print" ******************"
       w = 20
       h = 10
       size=(w,h)
       screen = pygame.display.set_mode(size) 
       img=pygame.image.load(filename) 
       screen.blit(img,(0,0))
       pygame.display.flip() # update the display
       pygame.time.wait(2000)
       #image = Image.open(filename)
       #image.show()

'''
sen=myCamDriver()
sen.takePhoto()
photo=sen.readPhotob64()
sen.savePhoto(photo,"p11.jpg")
print photo
pygame.time.wait(15)
#thread.start_new_thread(sen.showPhoto,("p11.jpg",))              
sen.showPhoto("p11.jpg")
'''
