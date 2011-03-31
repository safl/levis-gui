#!/usr/bin/env python
import threading
import logging
import time

import beanstalkc

class Worker(threading.Thread):
    
    counter = 0
    
    def __init__(self, name=None):
                
        self.working    = False
        self.paused     = False
        self.cv = threading.Condition()
        
        if name:
            thread_name = name
        else:
            thread_name     = "Worker-%d" % Worker.counter
            Worker.counter  += 1
        
        threading.Thread.__init__(self, name=thread_name)
    
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
        
        self.working = False    # Stop working
        if self.paused:         # If the worker is paused, unblock it
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
    
class BeanWorker(Worker):
    
    counter = 0
    
    def __init__(self, hostname, port, tubes):
        
        self.hostname   = hostname
        self.port       = port
        self.tubes      = tubes
        
        thread_name = 'BeanWorker-%d' % BeanWorker.counter
        BeanWorker.counter += 1
        
        Worker.__init__(self, name=thread_name)
    
    def work(self):        
        
        logging.debug("Connecting to beanstalk %s:%d watching tubes = %s..." % (
            self.hostname, self.port, self.tubes
        ))
        connected = False
        try:
            
            beanstalk = beanstalkc.Connection(
                host=self.hostname,
                port=self.port
            )
            for t in self.tubes:
                beanstalk.watch(t)
            if 'default' not in self.tubes:
                beanstalk.ignore('default')

            connected = True
            
        except Exception as details:
            logging.debug("Beanstalk ERR: [%s]" % details)
    
        while connected and self.working:            
            
            logging.debug("Grabbing job...")
            try:
                
                job = beanstalk.reserve(timeout=10)
                if job:
                    logging.debug("Got job...")
                    res = self.handle_job(job)
                    if res:
                        job.delete()
                else:
                    logging.debug("Probably timed out...")
                    
            except Exception as details:
                logging.error("Something went wrong! ERR: [%s]" % details)
                connected = False
                
            if not connected:
                logging.debug("Wait %d seconds then we try connecting to beanstalk again..")
                time.sleep(10)
                
    def handle_job(self, job):
        return False
        