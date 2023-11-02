#!/usr/bin/env python3

import os
import logging
import email
import json
import requests

from dotenv import load_dotenv
from imapclient import IMAPClient

import redmine

logging.basicConfig(level=logging.INFO)
log = logging.getLogger(__name__)

log.info('initializing threader')

# load credentials 
load_dotenv()
host = os.getenv('IMAP_HOST')
user = os.getenv('IMAP_USER')
passwd = os.getenv('IMAP_PASSWORD')


client = redmine.Client()

log.info(f'logging into {host}')
with IMAPClient(host=host, port=993, ssl=True) as server:
    server.login(user, passwd)
    server.select_folder("INBOX", readonly=True)
    log.info(f'logged into {host}')

    messages = server.search("UNSEEN")
    for uid, message_data in server.fetch(messages, "RFC822").items():
        email_message = email.message_from_bytes(message_data[b"RFC822"])
        
        # map userid from From
        from_address = email_message.get("From")
        subject = email_message.get("Subject")
        body = email_message.get("Body")
        log.info(f'uid:{uid} - from:{from_address}, subject:{subject}')

        user = client.find_user(from_address)
        if user == None:
            log.error(f"Unknown email address, no user found: {from_address}")
            # create new user if needed -> always new ticket
            # TODO try parsing first and last from from_address
            #first = ""
            #last = ""
            #user = client.create_user(from_address, first, last)

        # map ticket from Subject, if possible
        ticket = client.client.find_ticket_from_str(subject)
        
        # map ticket from "most recently updated open ticket by userid", if any
        if user and (ticket is None):
            ticket = client.most_recent_ticket_for(user)

        if ticket:
            client.append_message(ticket.id, user.login, body)
            log.info(f"Updated ticket #{ticket.id} with message from {user.login}")
            # TODO handle attachments
        else:
            # open new ticket for the email
            ticket = client.create_ticket(user.login, subject, body)
            log.info(f"Created new ticket from: {user.login}")
