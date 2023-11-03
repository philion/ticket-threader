#!/usr/bin/env python3

import os
import logging
import email
import email.policy
import re

import redmine

from imapclient import IMAPClient, SEEN, DELETED

# imapclient docs: https://imapclient.readthedocs.io/en/3.0.0/index.html
# source code: https://github.com/mjs/imapclient

logging.basicConfig(level=logging.INFO)
log = logging.getLogger(__name__)

class Client(): ## imap.Client()
    def __init__(self):
        self.host = os.getenv('IMAP_HOST')
        self.user = os.getenv('IMAP_USER')
        self.passwd = os.getenv('IMAP_PASSWORD')
        self.port = 993

        self.redmine = redmine.Client()

    # note: not happy with this method of dealing with complex email address
    # but I don't see a better way.
    def parse_email_address(self, email_addr):
        # Paul Philion <philion@seattlecommunitynetwork.org>
        # regex: r'(\w+) (\w+) <(\w+@\w+\.\w+)>'
        # r"(^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$)"

        # try to capture first, last and email from from_address
        email_regex = re.compile(r'(.*) <(\w+@\w+\.\w+)>')
        m = email_regex.match(email_addr)
        if m:
            first, last = m.group(1).rsplit(' ', 1)
            addr = m.group(2)

        return first, last, addr

    def handle_message(self, uid, message):
        from_address = message.get("From")
        subject = message.get("Subject")

        # this is to strip the leading content-type line
        body = message.get_body('plain').as_string().split('\n', maxsplit=1)[1]

        first, last, addr = self.parse_email_address(from_address)
        log.info(f'uid:{uid} - from:{last}, {first}, email:{addr}, subject:{subject}')

        # get user id from from_address
        user = self.redmine.find_user(addr)
        if user == None:
            log.error(f"Unknown email address, no user found: {addr}, {from_address}")
            # create new user if needed -> always new ticket
            # TODO try parsing first and last from from_address
            # user = redmine.create_user(addr, first, last)
            # self.redmine.create_ticket(user.login, subject, body)
 
        # find ticket using the subject, if possible
        # this uses a simple REGEX '#\d+' to match ticket numbers
        ticket = self.redmine.find_ticket_from_str(subject)
        
        # if there is not ticket number found,
        # query "most recently updated open ticket by userid", if any
        if user and (ticket is None):
            ticket = self.redmine.most_recent_ticket_for(user.login)

        if ticket:
            # found a ticket, append the message
            self.redmine.append_message(ticket.id, user.login, body)
            log.info(f"Updated ticket #{ticket.id} with message from {user.login}")
            # TODO handle attachments
        else:
            # no open tickets, create new ticket for the email message
            self.redmine.create_ticket(user.login, subject, body)
            log.info(f"Created new ticket from: {user.login}")

    def parse_message(self, data):
        return email.message_from_bytes(data[b"RFC822"])

    def check_unseen(self):
        with IMAPClient(host=self.host, port=self.port, ssl=True) as server:
            server.login(self.user, self.passwd)
            server.select_folder("INBOX", readonly=False)
            log.info(f'logged into imap {self.host}')

            messages = server.search("UNSEEN")
            for uid, message_data in server.fetch(messages, "RFC822").items():
                # process each message returned by the query
                try:
                    # decode the message
                    message = self.parse_message(message_data)
                    
                    # handle the message
                    self.handle_message(uid, message)

                    #  mark msg uid seen and deleted, as per redmine imap.rb
                    server.add_flags(uid, [SEEN, DELETED])
                    
                except Exception as e:
                    log.error(f"Message {uid} can not be processed: {e}")
                    server.add_flags(uid, [SEEN])
