#!/usr/bin/env python
import threading
import logging
import pprint
import email
import time

from django.conf import settings
from django.contrib.auth.models import User

from levis.helpdesk.models import Ticket, Priority, Queue, State

import beanstalkc

logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s,%(msecs)d %(levelname)s %(threadName)s %(message)s',
    datefmt='%H:%M:%S'
)

from levis.backend.utils import BeanWorker

class MailParser(BeanWorker):
    
    def handle_job(self, job):
        
        priority    = Priority.objects.get(name="normal")
        state       = State.objects.get(name="new")
        queue       = Queue.objects.get(name="default")
        user        = User.objects.get(pk=1)
        
        mail_raw = job.body
        msg = email.message_from_string(mail_raw)
        
        t = Ticket()
        t.number    = int(time.time()/10000)
        t.created   = int(time.time())
        t.owner     = user
        t.priority  = priority
        t.queue = queue
        t.state = state
        t.title = msg.get('Subject')
        t.save()
        
        return True

#class MailParser(Worker):
#    
#    def __init__(self, hostname, port, tubes):
#        
#        self.hostname   = hostname
#        self.port       = port
#        self.tubes      = tubes
#        
#        Worker.__init__(self)
#    
#    def work(self):
#        
#        priority    = Priority.objects.get(name="normal")
#        state       = State.objects.get(name="new")
#        queue       = Queue.objects.get(name="default")
#        user        = User.objects.get(pk=1)
#        
#        logging.debug("Connecting to beanstalk %s:%d watching tubes = %s..." % (
#            self.hostname, self.port, self.tubes
#        ))
#        connected = False
#        try:
#            
#            beanstalk = beanstalkc.Connection(
#                host=self.hostname,
#                port=self.port
#            )
#            for t in self.tubes:
#                beanstalk.watch(t)
#            if 'default' not in self.tubes:
#                beanstalk.ignore('default')
#
#            connected = True
#            
#        except Exception as details:
#            logging.debug("Beanstalk ERR: [%s]" % details)
#    
#        while connected and self.working:            
#            
#            logging.debug("Grabbing job..")
#            try:
#                job = beanstalk.reserve()
#                mail_raw = job.body
#                msg = email.message_from_string(mail_raw)
#                
#                t = Ticket()
#                t.number    = int(time.time()/10000)
#                t.created   = int(time.time())
#                t.owner     = user
#                t.priority  = priority
#                t.queue = queue
#                t.state = state
#                t.title = msg.get('Subject')
#                t.save()
#                
#                job.delete()
#            except Exception as details:
#                logging.debug("Something went wrong! ERR: [%s]" % details)
#                connected = False
#                
#            if not connected:
#                logging.debug("Wait %d seconds then we try connecting to beanstalk again..")
#                time.sleep(10)

def main():
    
    parser = MailParser(
        settings.BEANSTALK_HOST,
        settings.BEANSTALK_PORT,
        ['mail.in']        
    )
    parser.start()
    
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        pass
    
    parser.stop()
    parser.join()
    
if __name__ == "__main__":
    main()

