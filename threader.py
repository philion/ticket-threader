#!/usr/bin/env python3

import os
import logging
import email
import re

from dotenv import load_dotenv
from imapclient import IMAPClient

import imap

logging.basicConfig(level=logging.INFO)
log = logging.getLogger(__name__)

log.info('initializing threader')

# load credentials 
load_dotenv()

# construct the client
imap_client = imap.Client()

# process unseen emails
imap_client.check_unseen()
