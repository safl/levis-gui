#!/usr/bin/env python
#
#   MailFetcher,
#
#   Reads mail from one or more POP and/or IMAP servers, queues them in memory
#   for delivery to beantalk.
#
#   +------------+  +--------------+
#   | PopFetcher |  | ImapFetcher  |
#   +---+--------+  +-----+--------+
#       |                 |
#       +-----------------+
#                         |
#   +--------+            |
#   | Queue  |<--- put ---+
#   +--+-----+
#      |            +---------+
#      +--- get --->| Pusher  |-----> BEANSTALK
#                   +---------+
#
import threading
import logging
import imaplib
import poplib
import pprint
import Queue
import time

import beanstalkc

from organization.models import Organization
from django.conf import settings

logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s,%(msecs)d %(levelname)s %(threadName)s %(message)s',
    datefmt='%H:%M:%S'
)

class Worker(threading.Thread):
    
    def __init__(self):
                
        self.working   = False
        
        threading.Thread.__init__(self)
    
    def run(self):
        
        self.working = True
        while self.working:
            self.work()
            
        logging.debug("I quit...")
    
    def stop(self):
        self.working = False
    
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
        
        Worker.__init__(self)
    
class PopFetcher(Fetcher):
    
    def work(self):
        
        connected = False
        try:                            # Connect to pop3 server
            logging.debug("Connecting to POP server %s:%d with SSL? Answer: %s." % (
                self.hostname, self.port, self.use_ssl
            ))
            if self.use_ssl:
                M = poplib.POP3_SSL(
                    self.hostname,
                    self.port
                )
            else:
                M = poplib.POP3(
                    self.hostname,
                    self.port
                )
            
            M.user(self.username)
            M.pass_(self.password)
            
            connected = True
            
        except Exception as details:    # Publish error
            logging.debug("POP ERR: [%s]." % details, exc_info=3)
        
        logging.debug("Connected POP? Answer: %s." % connected)
        if connected:
            
            try:
                numMessages = len(M.list()[1])
                for i in range(numMessages):
                    for j in M.retr(i+1)[1]:
                        # Put into queue
                        logging.debug("MSG: %s" % j)
            except:
                logging.debug("Error retrieving mails... %s" % details)
                connected = False
            
            logging.debug("Attempting to close...")
            try:                        # Close connection
                M.quit()                
            except:
                logging.debug("Could not close and logout...")                
            logging.debug("Did i close?")
        
        if connected:
            time.sleep(self.poll)    # Wait before accepting to reconnect
        else:
            time.sleep(10)      # Wait before accepting to reconnect
    
class ImapFetcher(Fetcher):
    
    def work(self):
        
        logging.debug("Connecting to IMAP server %s:%d with SSL? Answer: %s." % (
            self.hostname, self.port, self.use_ssl
        ))
        connected = False
        try:                            # Connect to imap server
            
            if self.use_ssl:
                M = imaplib.IMAP4_SSL(
                    self.hostname,
                    self.port
                )
            else:
                M = imaplib.IMAP4(
                    self.hostname,
                    self.port
                )
            
            M.login(
                self.username,
                self.password
            )
            M.select()            
            connected = True
        
        except Exception as details:                         # Publish error            
            logging.debug("IMAP ERR: [%s]." % details)
        
        logging.debug("Connected IMAP? Answer: %s." % connected)
        if not connected:               # Wait before accepting to reconnect
            time.sleep(10)        
        
        while connected and self.working:
            
            logging.debug("Checking for new mail...")
            try:
                typ, data = M.search(None, '(Unseen)')
                
                for num in data[0].split():
                    typ, data = M.fetch(num, '(RFC822)')
                    logging.debug('Message %s\n' % (num))
                    #pprint.pprint(data) # Put mail into mail-queue
                    self.q.put(data[0][1])
                
                time.sleep(self.poll)
            except Exception as details:
                logging.debug("Error when retrieving mails... %s" % details)
                break
        
        if connected:                   # Close connection
            logging.debug("Attempting to close.")
            try:
                M.close()
                M.logout()
            except:
                logging.debug("Could not close and logout...")

class Pusher(Worker):
    """Send messages from local-queue to network-queue."""
    
    def __init__(self, q, hostname, port, tube):
        
        self.q          = q
        self.hostname   = hostname
        self.port       = port
        self.tube       = tube
        
        Worker.__init__(self)
        
    def work(self):
        
        logging.debug("Connecting to beanstalk %s:%d tube = %s..." % (
            self.hostname, self.port, self.tube
        ))
        connected = False
        try:
            
            beanstalk = beanstalkc.Connection(
                host=self.hostname,
                port=self.port
            )
            beanstalk.use(self.tube)
            connected = True
            
        except Exception as details:
            logging.debug("Beanstalk ERR: [%s]" % details, exc_info=3)
        
        logging.debug("Connected Beanstalk? Answer: %s." % connected)
        while connected and self.working:
            
            msg = None
            try:
                msg = self.q.get(timeout=10)
            except Queue.Empty:
                logging.debug("Timeout...")
            
            if msg:
                logging.debug("Got message!")
                try:
                    beanstalk.put(str(msg))
                except Exception as details:
                    logging.debug("Error sending it... %s" % details)
                    self.q.put(msg)  # Put it back in for later processing when reconnected...
                    connected = False
        
        if not connected:
            logging.debug("Try connecting again in 10 seconds..")
            time.sleep(10)

def main():
    """Read mail from pop3/imap and push it into the beanstalk queue "mail.in"."""
    
    q = Queue.Queue()
    
    #t = threading.Thread(target=pusher, args=(q, settings.BEANSTALK_HOST, settings.BEANSTALK_PORT))
    pusher = Pusher(q, settings.BEANSTALK_HOST, settings.BEANSTALK_PORT, 'mail.in')
    
    (hostname, port, use_ssl, username, password, poll) = (
        settings.IMAP_HOST,
        settings.IMAP_PORT,
        settings.IMAP_SSL,
        settings.IMAP_USER,
        settings.IMAP_PASS,
        settings.IMAP_POLL
    )
    imap_thread = ImapFetcher(q, hostname, port, use_ssl, username, password, poll)
    
    (hostname, port, use_ssl, username, password, poll) = (
        settings.POP_HOST,
        settings.POP_PORT,
        settings.POP_SSL,
        settings.POP_USER,
        settings.POP_PASS,
        settings.POP_POLL
    )
    pop_thread = PopFetcher(q, hostname, port, use_ssl, username, password, poll)
    
    threads = [pusher, pop_thread, imap_thread]
    
    logging.debug("Starting threads...")
    for t in threads:
        t.start()
    
    try:
        while True:
            
            time.sleep(1)
    except KeyboardInterrupt:
        pass
    
    logging.debug("Stopping threads...")
    for t in threads:
        t.stop()
    
    logging.debug("Waiting for threads...")
    for t in threads:
        t.join()
    logging.debug("Stopped.")

if __name__ == "__main__":
	main()
