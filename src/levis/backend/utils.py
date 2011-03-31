#!/usr/bin/env python
import threading

class Worker(threading.Thread):
    
    def __init__(self):
                
        self.working    = False
        self.paused     = False
        self.cv = threading.Condition()
        
        threading.Thread.__init__(self)
    
    def run(self):
        
        self.working = True
        while self.working:
            
            if self.paused:
                self.cv.acquire()
                self.cv.wait()
                self.cv.release()
            else:            
                self.work()
            
        logging.debug("I quit...")
    
    def stop(self):
        
        self.working = False
        if self.paused:
            self.resume()
    
    def pause(self):
        
        self.paused = True
    
    def resume(self):
        
        self.paused = False
        self.cv.acquire()
        self.cv.notify()
        self.cv.release()
    
    def work(self):
        """Override this, this to do the actual work."""
        pass