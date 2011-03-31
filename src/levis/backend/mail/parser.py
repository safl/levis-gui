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
    
def main():
    
    parser = MailParser(
        settings.BEANSTALK_HOST,
        settings.BEANSTALK_PORT,
        ['helpdesk.mail.in']        
    )
    logging.debug('Starting parser...')
    parser.start()
    
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        pass
    
    logging.debug('Stopping parser...')
    parser.stop()
    logging.debug('Waiting for parser to stop...')
    parser.join()
    logging.debug('Exiting.')
    
if __name__ == "__main__":
    main()

