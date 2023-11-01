#!/usr/bin/env python3

import os
import logging
import email
import json
import requests

from dotenv import load_dotenv
from imapclient import IMAPClient

logging.basicConfig(level=logging.INFO)
log = logging.getLogger(__name__)

log.info('initializing threader')

# load credentials 
load_dotenv()
redmine = os.getenv('REDMINE_HOST')
secret = os.getenv('REDMINE_KEY')
host = os.getenv('IMAP_HOST')
user = os.getenv('IMAP_USER')
passwd = os.getenv('IMAP_PASSWORD')

log.info(f'logging into {host}')

# url to POST new email tickets to redmine
ingest_url = f"http://{redmine}/mail_handler"

with IMAPClient(host=host, port=993, ssl=True) as server:
    server.login(user, passwd)
    server.select_folder("INBOX", readonly=True)
    log.info(f'logged into {host}')

    messages = server.search("UNSEEN")
    for uid, message_data in server.fetch(messages, "RFC822").items():
        email_message = email.message_from_bytes(message_data[b"RFC822"])
        log.info(f'{uid} - from:{email_message.get("From")}, subject:{email_message.get("Subject")}')
        
        # POST to /mail_handler API
        headers = {
            'User-Agent': 'threader/0.0.1',
        }

        data = { 
            'key': secret, 
            'email': email_message.as_string(), #email.gsub(/(?<!\r)\n|\r(?!\n)/, "\r\n"),
            'allow_override': True,
            #'unknown_user': "create",
            #'project': "scn",
            #'default_group': default_group,
            #'no_account_notice': no_account_notice,
            #'no_notification': no_notification,
            #'no_permission_check': no_permission_check,
            #'project_from_subaddress': project_from_subaddress,
        }

        r = requests.post(url=ingest_url, data=data, headers=headers)

        from pprint import pprint
        pprint(vars(r))

        log.info(f"request sent {ingest_url}, response: {r}")

