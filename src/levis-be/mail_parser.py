#!/usr/bin/env python
from django.conf import settings
from helpdesk.models import Ticket, Priority, Queue, State
from  django.contrib.auth.models import User
import beanstalkc

import pprint
import email
import time

def main():
    
    priority    = Priority.objects.get(name="normal")
    state       = State.objects.get(name="new")
    queue       = Queue.objects.get(name="default")
    user        = User.objects.get(pk=1)
    
    (hostname, port) = (settings.BEANSTALK_HOST, settings.BEANSTALK_PORT)
    
    while True:
        
        print "Connecting to beanstalk..."
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
            print "Error setting up beanstalk...", details
        
        print "Connected = ", connected
        while connected:
            
            print "Grabbing job.."
            try:
                job = beanstalk.reserve()
                msg = email.message_from_string(job.body)
                for h, v in msg.items():
                    print h,v
                
                t = Ticket()
                t.number = int(time.time()/10000)
                t.created = int(time.time())
                t.owner = user
                t.priority = priority
                t.queue = queue
                t.state = state
                t.title = msg.get('subject', "Hmm")
                t.save()
                
                job.delete()
            except Exception as details:
                print "Something went wrong!", details
                connected = False
            
        if not connected:
            print "Wait ten seconds then we try connecting to beanstalk again.."
            time.sleep(10)
    
if __name__ == "__main__":
    main()

