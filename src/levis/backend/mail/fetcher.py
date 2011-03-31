#!/usr/bin/env python
#
#
#    MailFetcher,
#
#    Reads mail from one or more POP and/or IMAP servers queues them in memory
#    as illustrated below:
#
#
#    +--------------+                +--------+          +---------+
#    | PopRetriever |-----+---put--->| Queue  |---get--->| Pusher  |
#    +--------------+     |          +--------+          +--+------+
#                         |                                 |
#    +----------------+   |                                 |    +-----------+
#    | ImapRetriever  |---+                                 +--->| BEANSTALK |
#    +----------------+                                          +-----------+
#
#
#    A mail is encapsulated as the tuple (account_id, mail) such that the
#    origin of mail-blob can be identified.
#
#    When persisted to disk the mail-blob is identified by the filename:
#    "<account_id>_<tmpfilename>"
#
#    @author Simon A. F. Lund <safl@safl.dk>
#
#    References:
#
#    - POP3 http://www.faqs.org/rfcs/rfc1939.html
#    - IMAP http://www.faqs.org/rfcs/rfc3501.html
#  
# TODO:
#
#   - Retrieve mails properly, assign id and check the return of retrieval
#   - Persist mails from memory when terminating
#   - Load persisted mails into memory when starting MailFetcher
#   - Throttling to avoid flooding, based on pause-threshold and resume-threshold:
#
#       * Control the retrieval of mail by:
#
#           pausing:    mails in queue > pause-threshold
#           resuming:   mails in queue < resume-threshold
#                   
#   - Command-line options:
#
#       * log-file
#       * log-level
#       * localspool-dir for persisted mails
#       * pause-threshold
#       * resume-threshold
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

from levis.backend.utils import Worker

logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s,%(msecs)d %(levelname)s %(threadName)s %(message)s',
    datefmt='%H:%M:%S'
)

class Retriever(Worker):
    
    timeout = 10
    retry   = 10
    counter = 0
    
    def __init__(self, q, hostname, port, use_ssl, username, password, poll):
        
        self.q          = q
        self.hostname   = hostname
        self.port       = port
        self.use_ssl    = use_ssl
        self.username   = username
        self.password   = password
        self.poll       = poll
        
        thread_name = 'Retriever-%d' % Retriever.counter
        Retriever.counter += 1
        
        Worker.__init__(self, name=thread_name)
            
class PopRetriever(Retriever):
    
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
            logging.error("POP ERR: [%s]." % details)
        
        logging.debug("Connected POP? Answer: %s." % connected)
        if connected:
            
            try:
                (numMessages, size) = M.stat()
                for i in xrange(1, numMessages):
                    (response, lines, octets) = M.retr(i)
                    
                    if response.startswith('+OK'):
                        msg = ''.join(lines)
                        self.q.put(("ID", msg, len(msg)))
                    else:
                        logging.error('RETR response did not start with "+OK"!')
                    
                    if paused:
                        logging.warn('Pausing retrieval. %d mails are ready for retrieval.' % (numMessages-i))
                        break
                    
            except Exception as details:
                logging.error("Error retrieving mails... %s" % details)
                connected = False
            
            logging.debug("Attempting to close...")
            try:                        # Close connection
                M.quit()                
            except:
                logging.error("Could not close and logout...")                
            logging.debug("Did i close?")
        
        if connected:
            time.sleep(self.poll)       # Wait before accepting to reconnect
        else:
            time.sleep(Retriever.retry)   # Wait before accepting to reconnect
    
class ImapRetriever(Retriever):
    
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
            time.sleep(Retriever.retry)        
        
        while connected and self.working:
            
            logging.debug("Checking for new mail...")
            try:
                typ, data = M.search(None, '(Unseen)')
                
                for num in data[0].split():
                    typ, data = M.fetch(num, '(RFC822)')
                    logging.debug('Message %s\n' % (num))
                    msg = data[0][1]
                    self.q.put(("ID", msg, len(msg)))
                
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

class MailFetcher(threading.Thread):
    
    counter = 0
    types = {
        'POP3': PopRetriever,
        'IMAP': ImapRetriever
    }
    
    def __init__(self, accounts):
        
        self.accounts   = accounts
        
        self.q          = Queue.Queue()
        self.retrievers = []

        for (type, hostname, port, use_ssl, username, password, poll) in accounts:
            
            self.retrievers.append(MailFetcher.types[type](
                self.q, hostname, port, use_ssl, username, password, poll
            ))
        
        thread_name = 'MailFetcher-%d' % MailFetcher.counter
        MailFetcher.counter += 1
        threading.Thread.__init__(self, name=thread_name)
    
    def run(self):
        
        # Load persisted mails from disk
        
        logging.debug("Starting retrievers...")
        for t in self.retrievers:
            t.start()
        
        # Todo: monitor queue
        
        for t in self.retrievers:
            t.join()
        
        logging.debug("Stopped.")
    
    def pause(self):
    
        for t in self.retrievers:
            t.pause()
    
    def resume(self):
        
        for t in self.retrievers:
            t.resume()
    
    def stop(self):
        
        for t in self.retrievers:
            t.stop()
            
        for t in self.retrievers:
            t.join()
            
        # Remove any other readers of queue
        # Persist any mails in queue
        
    def get(self):
        pass
    
    def put(self):
        pass

class BeanPusher(Worker):
    """Send messages from local-queue to network-queue."""
    
    retry_to = 10   # Retry-timeout
    
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
            logging.debug("Beanstalk ERR: [%s]" % details)
        
        logging.debug("Connected to Beanstalk? Answer: %s." % connected)
        while connected and self.working:
            
            msg = None
            try:
                (id, msg, msg_len) = self.q.get(timeout=10)
            except Queue.Empty:
                logging.debug("Nothing to push...")
            
            if msg:
                logging.debug("Got message!")
                try:
                    beanstalk.put(msg) # serialize...
                    self.q.task_done()
                except Exception as details:
                    logging.debug("Error sending it... %s" % details)
                    self.q.put(("ID", msg, msg_len))  # Put it back in for later processing when reconnected...
                    connected = False
        
        if not connected:
            logging.debug("Try connecting again in %d seconds.." % BeanPusher.retry_to)
            time.sleep(BeanPusher.retry_to)

def main():
    """Read mail from pop3/imap and push it into the beanstalk queue "mail.in"."""
        
    accounts = []
    accounts.append((
        "IMAP",
        settings.IMAP_HOST,
        settings.IMAP_PORT,
        settings.IMAP_SSL,
        settings.IMAP_USER,
        settings.IMAP_PASS,
        settings.IMAP_POLL
    ))
    
    #accounts.append((
    #    "POP3",
    #    settings.POP_HOST,
    #    settings.POP_PORT,
    #    settings.POP_SSL,
    #    settings.POP_USER,
    #    settings.POP_PASS,
    #    settings.POP_POLL
    #))
    
    fetcher = MailFetcher(accounts)
    fetcher.start()
    
    pusher = BeanPusher(
        fetcher.q,
        settings.BEANSTALK_HOST,
        settings.BEANSTALK_PORT,
        'mail.in'
    )
    pusher.start()
    
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        pass
    
    logging.debug("Telling fetcher to stop.")
    fetcher.stop()
    pusher.stop()
    
    logging.debug("Waiting for fetcher to exit...")
    fetcher.join()
    logging.debug("Waiting for pusher to exit...")
    pusher.join()
    logging.debug("Stopped.")

if __name__ == "__main__":
	main()
