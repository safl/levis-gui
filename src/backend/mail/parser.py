#!/usr/bin/env python
from django.conf import settings
from helpdesk.models import Ticket, Priority, Queue, State
from  django.contrib.auth.models import User
import beanstalkc

import threading
import logging
import pprint
import email
import time

logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s,%(msecs)d %(levelname)s %(threadName)s %(message)s',
    datefmt='%H:%M:%S'
)

from levis.backend.utils import Worker

def main():
    
    priority    = Priority.objects.get(name="normal")
    state       = State.objects.get(name="new")
    queue       = Queue.objects.get(name="default")
    user        = User.objects.get(pk=1)
    
    (hostname, port) = (settings.BEANSTALK_HOST, settings.BEANSTALK_PORT)
    
    while True:
        
        logging.debug("Connecting to beanstalk...")
        connected = False
        try:
            
            beanstalk = beanstalkc.Connection(
                host=hostname,
                port=port
            )
            beanstalk.watch('mail.in')
            beanstalk.ignore('default')
            
            connected = True
            
        except Exception as details:
            logging.debug("Beanstalk ERR: [%s]" % details)
        
        logging.debug("Connected? Answer = %s" % connected)
        while connected:
            
            logging.debug("Grabbing job..")
            try:
                job = beanstalk.reserve()
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
                
                job.delete()
            except Exception as details:
                logging.debug("Something went wrong! ERR: [%s]" % details)
                connected = False
            
        if not connected:
            logging.debug("Wait %d seconds then we try connecting to beanstalk again..")
            time.sleep(10)
    
if __name__ == "__main__":
    main()

