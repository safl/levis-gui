#!/usr/bin/env python
#
#
#    MailFetcher,
#
#    Reads mail from one or more POP and/or IMAP servers queues them in memory.
#
#    Nifty features:
#
#    - Throttling to avoid exhausting resources
#    - Persistence of in-memory mails upon shutdown
#
#    Functionality is illustrated below:
#
#
#    +--------------+                +--------------+          +---------+
#    | PopRetriever |-----+---put--->| MailFetcher  |---get--->| Pusher  |
#    +--------------+     |          +-----+--------+          +--+------+
#                         |                |                      |
#    +----------------+   |                |                      |    +-----------+
#    | ImapRetriever  |---+                +---persist--->        +--->| BEANSTALK |
#    +----------------+                                                +-----------+
#
#    A mail is encapsulated as the tuple (account_id, mail) such that the
#    origin of a mail-blob can be identified.
#
#    When persisted to disk the mail-blob is identified by the filename:
#    "<account_id>_<tmpfilename>.eml"
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
#   - Remove persisted mail after load.
#   - Lock mail-queue when shutting down.
#   - Command-line options:
#
#       * log-file
#       * log-level
#       * localspool-dir for persisted mails
#       * pause-threshold
#       * resume-threshold
#
from collections import deque
import threading
import tempfile
import logging
import imaplib
import poplib
import pprint
import glob
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

class Empty(Exception):
    "Exception raised by MailFetcher.get()."
    pass

class Retriever(Worker):
    
    timeout = 10
    retry   = 10
    counter = 0
    
    def __init__(self, acct_id, put, hostname, port, use_ssl, username, password, poll):
        
        self.id = acct_id
        
        self.put        = put
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
                        self.put((self.id, msg, len(msg)))
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
                    self.put((self.id, msg, len(msg)))
                
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
    
    def __init__(self, accounts, persist_dir=None, pause_threshold=104857600, resume_threshold=0):
        
        self.accounts   = accounts
        
        self.mutex      = threading.Lock()
        self.not_empty  = threading.Condition(self.mutex)
        
        self._mailq         = deque()
        self._mailq_bytes   = 0        
        
        self.resume_threshold   = resume_threshold
        self.pause_threshold    = pause_threshold
        
        self.paused =  False
        self.retrievers = []
        self.persist_dir = persist_dir
        
        for (type, acct_id, hostname, port, use_ssl, username, password, poll) in accounts:
            
            self.retrievers.append(MailFetcher.types[type](
                acct_id, self.put, hostname, port, use_ssl, username, password, poll
            ))
        
        thread_name = 'MailFetcher-%d' % MailFetcher.counter
        MailFetcher.counter += 1
        threading.Thread.__init__(self, name=thread_name)
    
    def run(self):
                
        if self.persist_dir:            # Load persisted mails from disk
            self.from_file()
            
            if self._mailq_bytes >= self.pause_threshold:    # Check threshold
                self.pause()
        
        logging.debug("Starting retrievers...")
        for t in self.retrievers:
            t.start()
        
        for t in self.retrievers:
            t.join()
        
        logging.debug("Stopped.")
    
    def pause(self):
        
        self.paused = True
        for t in self.retrievers:
            t.pause()
    
    def resume(self):
        
        self.paused = False
        for t in self.retrievers:
            t.resume()
    
    def stop(self):
        
        for t in self.retrievers:
            t.stop()
            
        for t in self.retrievers:
            t.join()
        
        # Remove any readers of the mail-queue
        
        if self.persist_dir:    # Persist mail-queue to filesystem
            self.to_file()
    
    def put(self, item):
        
        self.not_empty.acquire()
        try:
            self._mailq.appendleft(item)
            self._mailq_bytes += item[2]
            logging.debug('Queue size: %d, items=%d.' % (self._mailq_bytes, len(self._mailq)))
            
            if self._mailq_bytes >= self.pause_threshold:    # Check threshold
                self.pause()
            
            self.not_empty.notify()
            
        finally:
            self.not_empty.release()
    
    def get(self, timeout=10.0):
        
        self.not_empty.acquire()
        try:
            if timeout < 0:
                raise ValueError("'Timeout must be a positive number")
            else:
                endtime = time.time() + timeout
                while not len(self._mailq):
                    remaining = endtime - time.time()
                    if remaining <= 0.0:
                        raise Empty
                    self.not_empty.wait(remaining)
            
            item = self._mailq.pop()
            self._mailq_bytes -= item[2]
            
            if self._mailq_bytes <= self.resume_threshold:
                self.resume()
            
            logging.debug('Queue size: %d' % self._mailq_bytes)
            return item
        finally:
            self.not_empty.release()
            
    def to_file(self):
        """
        Persist the mail-queue to file-system.
        
        This could be implemented with simply pickling the deque, but by
        using files it is much easier to manually fetch the persisted mails.
        """
        logging.info("About to persist %d mails of total %d bytes." % (len(self._mailq), self._mailq_bytes))
        
        for (acct_id, mail, bytes) in self._mailq:
            try:
                
                with tempfile.NamedTemporaryFile(
                    prefix  = "%s_" %(acct_id),
                    suffix  = '.eml',
                    dir     = self.persist_dir,
                    delete  = False) as f:
                    
                    f.write(mail)
                    
            except Exception as details:
                logging.error('Failed persisting mail from account "%s". ERR [%s]' % (acct_id, details))
                
    def from_file(self):
        """
        Load persisted mails from file-system into mail-queue.
        """
        
        for fn in glob.glob(self.persist_dir+'*.eml'):
            try:
                
                with open(fn, 'r') as fd:
                    (acct_id, _) = fn.split('_', 1)
                    mail    = fd.read()
                    bytes   = len(mail)
                    self._mailq.append((acct_id, mail, bytes))
                    self._mailq_bytes += bytes
                    
            except Exception as details:
                logging.error("Failed reading persisted mail identified by filename [%]. ERR: [%s]" % (fn, details))
                
        logging.info("Loaded %d mails from file-system of a total of %d bytes." % (len(self._mailq), self._mailq_bytes))

class BeanPusher(Worker):
    """Send messages from local-queue to network-queue."""
    
    retry_to = 10   # Retry-timeout
    
    def __init__(self, get, put, hostname, port, tube):
        
        self.get        = get
        self.put        = put
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
                msg = self.get(timeout=10.0)
            except Empty:
                logging.debug("Mail-queue is empty, nothing to push.")
            except Exception as details:
                logging.error("Error when requesting mail from fetcher. ERR: [%s]" % details)
            
            if msg:
                logging.debug("Got message!")
                try:
                    beanstalk.put( msg[1] )       # Serialize...
                except Exception as details:
                    logging.error("Beanstalk ERR: [%s]" % details)
                    self.put( msg )
                    connected = False
        
        if not connected:
            logging.debug("Re-connect attempt in %d seconds.." % BeanPusher.retry_to)
            time.sleep(BeanPusher.retry_to)

def main():
    """Read mail from pop3/imap and push it into the beanstalk queue "mail.in"."""
        
    accounts = []
    accounts.append((
        "IMAP",
        "id",
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
    
    f = MailFetcher(accounts, '/tmp/')
    f.start()
    
    pusher = BeanPusher(
        f.get,
        f.put,
        settings.BEANSTALK_HOST,
        settings.BEANSTALK_PORT,
        'helpdesk.mail.in'
    )
    pusher.start()
    
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        pass
    
    logging.debug("Telling fetcher to stop.")
    f.stop()
    pusher.stop()
    
    logging.debug("Waiting for fetcher to exit...")
    f.join()
    logging.debug("Waiting for pusher to exit...")
    pusher.join()
    logging.debug("Stopped.")

if __name__ == "__main__":
	main()
