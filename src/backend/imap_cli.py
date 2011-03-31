#!/usr/bin/env python
from organization.models import Organization
from django.conf import settings
import beanstalkc

import threading
import imaplib
import poplib
import pprint
import Queue
import time

class Worker(threading.Thread):
    
    def __init__(self):
                
        self.working   = False
    
    def run(self):
        
        self.working = True
        while self.working:
            self.work()
    
    def stop(self):
        self.fetching = False
    
    def work(self):
        """Override this, this to do the actual work."""
        pass

class Fetcher(Worker):
    
    def __init__(self, q, hostname, port, use_ssl, username, password, poll):
        
        self.q          = q
        self.hostname   = hostname
        self.port       = port
        self.use_ssl    = use_ssl
        self.username   = username
        self.password   = password
        self.poll       = poll
    
class PopFetcher(Fetcher):
    
    def work(self):
        
        try:                            # Connect to pop3 server
            
            if use_ssl:
                M = poplib.POP3_SSL(
                    self.hostname,
                    self.port
                )
            else:
                M = poplib.POP3(
                    self.hostname,
                    self.port
                )
            
            M.user(username)
            M.pass_(password)
            
            connected = True
            
        except Exception as details:    # Publish error
            print "Could not connect, we will wait and try again...", details
                
        if connected:
            
            try:
                numMessages = len(M.list()[1])
                for i in range(numMessages):
                    for j in M.retr(i+1)[1]:
                        print j
            except:
                print "Error when retrieving mails..."
                connected = False
            
            print "Attempting to close."
            try:                        # Close connection
                M.quit()                
            except:
                print "Could not close and logout..."
            print "Did i close?"
        
        if connected:
            time.sleep(poll)    # Wait before accepting to reconnect
        else:
            time.sleep(10)      # Wait before accepting to reconnect
    
class ImapFetcher(Fetcher):
    
    def work(self):
        pass

class Pusher(Worker):
    """Send messages from local-queue to network-queue."""
    
    def __init__(self, q, hostname, port):
        
        self.q          = q
        self.hostname   = hostname
        self.port       = port
        
        Worker.__init__(self)
        
    def work(self):
        
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

#def pusher(q, hostname, port):
#    
#    while True:
#        
#        print "Connecting to beanstalk"
#        connected = False
#        try:
#            beanstalk = beanstalkc.Connection(
#                host=hostname,
#                port=port
#            )
#            beanstalk.use('mail.in')
#            connected = True
#            
#        except Exception as details:
#            print "Error connecting / using", details
#        
#        print "Connected = ", connected
#        while connected:
#            
#            msg = None
#            try:
#                msg = q.get(timeout=10)
#            except Queue.Empty:
#                print "Timeout..."
#            
#            if msg:
#                print "Got message!"
#                try:
#                    beanstalk.put(str(msg))
#                except Exception as details:
#                    print "Error sending it...", details
#                    q.put(msg)  # Put it back in for later processing when reconnected...
#                    connected = False
#        
#        if not connected:
#            print "Try connecting again in 10 seconds.."
#            time.sleep(10)

#def pop_fetcher(q, hostname, port, use_ssl, username, password, poll):
#    
#    while True:
#                
#        try:                            # Connect to imap server
#            
#            if use_ssl:
#                M = poplib.POP3_SSL(hostname, port)
#            else:
#                M = poplib.POP3(hostname, port)
#            
#            M.user(username)
#            M.pass_(password)
#            
#            connected = True
#            
#        except Exception as details:    # Publish error            
#            print "Could not connect, we will wait and try again...", details
#                
#        if connected:
#            
#            try:
#                numMessages = len(M.list()[1])
#                for i in range(numMessages):
#                    for j in M.retr(i+1)[1]:
#                        print j
#                
#                time.sleep(poll)        # Wait before accepting to reconnect
#            except:
#                print "Error when retrieving mails..."
#                break
#            
#            print "Attempting to close."
#            try:                        # Close connection
#                M.quit()                
#            except:
#                print "Could not close and logout..."
#            print "Did i close?"
#            
#        else:
#            
#            time.sleep(10)              # Wait before accepting to reconnect

def imap_fetcher(q, hostname, port, use_ssl, username, password, poll):
    
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

def main():
    """Read mail from pop3/imap and push it into the beanstalk queue "mail.in"."""
    
    q = Queue.Queue()
    
    t = threading.Thread(target=pusher, args=(q, settings.BEANSTALK_HOST, settings.BEANSTALK_PORT))
    t.start()
    
    (hostname, port, use_ssl, username, password, poll) = (
        settings.IMAP_HOST,
        settings.IMAP_PORT,
        settings.IMAP_SSL,
        settings.IMAP_USER,
        settings.IMAP_PASS,
        settings.IMAP_POLL
    )
    pop_thread  = threading.Thread(target=pop_fetcher, args=(q, hostname, port, use_ssl, username, password, poll))
    pop_thread.daemon = True
    pop_thread.start()
    
    (hostname, port, use_ssl, username, password, poll) = (
        settings.POP_HOST,
        settings.POP_PORT,
        settings.POP_SSL,
        settings.POP_USER,
        settings.POP_PASS,
        settings.POP_POLL
    )
    imap_thread = threading.Thread(target=imap_fetcher, args=(q, hostname, port, use_ssl, username, password, poll))
    imap_thread.daemon = True
    imap_thread.start()
    
    while True:
        time.sleep(1)

if __name__ == "__main__":
	main()
