import thread
import time

def my_code(message,delay):
   time.sleep(delay)
   print "My code is running"
   print message


try:
   thread.start_new_thread(my_code, ("Thread-1",2, ) )
   thread.start_new_thread(my_code, ("Thread-2",4, ) )
except:
   print "Error: unable to start thread"
print "Hello"
time.sleep(10)
#my_code_thread = threading.Thread(target= my_code)
#my_code_thread.start()
#root.mainloop()
