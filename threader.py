#!/usr/bin/env python3

import os
import logging
import email

from dotenv import load_dotenv
from imapclient import IMAPClient

logging.basicConfig(level=logging.INFO)
log = logging.getLogger(__name__)

log.info('initializing threader')

ticket_url = "http://localhost/redmine/mail_handler"

# load credentials 
load_dotenv()

host = os.getenv('IMAP_HOST')
user = os.getenv('IMAP_USER')
passwd = os.getenv('IMAP_PASSWORD')

with IMAPClient(host) as server:
    server.login(user, passwd)
    server.select_folder("INBOX", readonly=True)
    log.info(f'logged into {host}')

    messages = server.search("UNSEEN")
    for uid, message_data in server.fetch(messages, "RFC822").items():
        email_message = email.message_from_bytes(message_data[b"RFC822"])
        print(uid, email_message.get("From"), email_message.get("Subject"))
        # POST to /mail_handler API
        # mark message seen

