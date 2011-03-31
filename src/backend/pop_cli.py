#!/usr/bin/env python
from django.conf import settings
import poplib

import pprint
import time

def main():
    """Read mail from pop account and push them into the ingoing mail-queue."""
    
    # TODO: read the oldest first,
    # dump stuff into work-queue
    
    connected = False
    (hostname, port, use_ssl, username, password, poll) = (
        settings.POP_HOST,
        settings.POP_PORT,
        settings.POP_SSL,
        settings.POP_USER,
        settings.POP_PASS,
        settings.POP_POLL
    )
    
    while True:
                
        try:                            # Connect to imap server
            
            if use_ssl:
                M = poplib.POP3_SSL(hostname, port)
            else:
                M = poplib.POP3(hostname, port)
            
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
                
                time.sleep(poll)        # Wait before accepting to reconnect
            except:
                print "Error when retrieving mails..."
                break
            
            print "Attempting to close."
            try:                        # Close connection
                M.quit()                
            except:
                print "Could not close and logout..."
            print "Did i close?"
            
        else:
                        
            time.sleep(10)              # Wait before accepting to reconnect

if __name__ == "__main__":
	main()

