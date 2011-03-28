#!/usr/bin/env python
from organization.models import Organization
from django.conf import settings
import imaplib
import pprint
import beanstalkc
import time

import threading
import Queue

# TODO: read the oldest first,
# dump stuff into work-queue

def pusher(q, hostname, port):
    
    while True:
        
        print "Connecting to beanstalk"
        connected = False
        try:
            beanstalk = beanstalkc.Connection(
                host=hostname,
                port=port
            )
            beanstalk.use('mail.in')
            connected = True
            
        except Exception as details:
            print "Error connecting / using", details
        
        print "Connected = ", connected
        while connected:
            
            msg = None
            try:
                msg = q.get(timeout=10)
            except Queue.Empty:
                print "Timeout..."
            
            if msg:
                print "Got message!"
                try:
                    beanstalk.put(str(msg))
                except Exception as details:
                    print "Error sending it...", details
                    q.put(msg)  # Put it back in for later processing when reconnected...
                    connected = False
        
        if not connected:
            print "Try connecting again in 10 seconds.."
            time.sleep(10)

def main():
    """Read mail from imap account and push them into the ingoing mail-queue."""
    
    q = Queue.Queue()
    
    t = threading.Thread(target=pusher, args=(q, settings.BEANSTALK_HOST, settings.BEANSTALK_PORT))
    t.start()
    
    connected = False
    (hostname, port, use_ssl, username, password, poll) = (
        settings.IMAP_HOST,
        settings.IMAP_PORT,
        settings.IMAP_SSL,
        settings.IMAP_USER,
        settings.IMAP_PASS,
        settings.IMAP_POLL
    )
    
    while True:
        
        print "Connecting..."
        try:                            # Connect to imap server
            
            if use_ssl:
                M = imaplib.IMAP4_SSL(hostname, port)
            else:
                M = imaplib.IMAP4(hostname, port)
            
            M.login(username, password)
            M.select()
            
            connected = True
            
        except:                         # Publish error            
            print "Could not connect, we will wait and try again..."
        
        if not connected:               # Wait before accepting to reconnect
            time.sleep(10)
        
        while connected:
            
            print "Checking for new mail..."
            try:
                typ, data = M.search(None, '(Unseen)')
                
                for num in data[0].split():
                    typ, data = M.fetch(num, '(RFC822)')
                    print 'Message %s\n' % (num)
                    #pprint.pprint(data) # Put mail into mail-queue
                    q.put(data[0][1])
                
                print 
                time.sleep(poll)
            except Exception as details:
                print "Error when retrieving mails...", details
                break
        
        if connected:                   # Close connection
            print "Attempting to close."
            try:
                M.close()
                M.logout()
            except:
                print "Could not close and logout..."

if __name__ == "__main__":
	main()
