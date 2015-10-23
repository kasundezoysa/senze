import RPi.GPIO as GPIO
import time


GPIO.setmode(GPIO.BOARD)
GPIO.setup(13,GPIO.OUT)
GPIO.setup(15,GPIO.OUT)

while True:
    print "ON"
    time.sleep(2)
    GPIO.output(13,1)
    GPIO.output(15,0)
    time.sleep(2)
    GPIO.output(13,0)
    GPIO.output(15,1)
    print "OFF"

GPIO.cleanup()
