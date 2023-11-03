#!/usr/bin/env python3

import os
import re
import json
import requests
import logging
import datetime as dt
#import humanize

from types import SimpleNamespace
#from collections import namedtuple


#from typing import TypedDict # see https://peps.python.org/pep-0589/
from dataclasses import dataclass

log = logging.getLogger(__name__)

class Client(): ## redmine.Client()
    def __init__(self):
        self.url = os.getenv('REDMINE_URL')
        self.token = os.getenv('REDMINE_KEY')

    def create_ticket(self, user_id, subject, body):
        # https://www.redmine.org/projects/redmine/wiki/Rest_Issues#Creating-an-issue

        headers = { # TODO DRY headers
            'User-Agent': 'netbot/0.0.1', # TODO update to project version, and add version management
            'Content-Type': 'application/json',
            'X-Redmine-API-Key': self.token,
            'X-Redmine-Switch-User': user_id, # Make sure the comment is noted by the correct user
        }

        data = {
            'issue': {
                'project_id': 1,
                'subject': subject,
                'description': body,
            }
        }

        r = requests.post(f"{self.url}/issues.json", data=data, headers=headers)
        # check 201 status
        #root = json.loads(r.text, object_hook= lambda x: SimpleNamespace(**x))
        #ticket = root.ticket[0]
        #return ticket

    def append_message(self, ticket_id, user_id, body):
        headers = { # TODO DRY headers
            'User-Agent': 'netbot/0.0.1', # TODO update to project version, and add version management
            'Content-Type': 'application/json',
            'X-Redmine-API-Key': self.token,
            'X-Redmine-Switch-User': user_id, # Make sure the comment is noted by the correct user
        }

        # PUT a simple JSON structure
        data = {
            'issue': {
                'notes': body
            }
        }

        r = requests.put(f"{self.url}/issues/{ticket_id}.json", data=data, headers=headers)
        # check 201 status

        print(vars(r))

        #root = json.loads(r.text, object_hook= lambda x: SimpleNamespace(**x))
        #root = json.loads(r.text, object_hook=lambda d: namedtuple('Issue', d.keys())(*d.values()))

        # check for error
        #if root.errors:
        #    log.error(f"Error running |{query_str}|: {root.errors}")
        #    return None

        #return root


        # email is full email message, with from, subject and body
        # PUT /issues/[id].json
        # {
        #    "issue": {
        #      "notes": "{email.body}" 
        #    }
        # }


        # for attachments
        # First, upload your file:
        # POST /uploads.json?filename=image.png
        # Content-Type: application/octet-stream
        # (request body is the file content)
        # 201 response:
        #     {"upload":{"token":"7167.ed1ccdb093229ca1bd0b043618d88743"}}
        # Then create the issue using the upload token:

        #You can also upload multiple files (by doing multiple POST requests to /uploads.json), then create an issue with multiple attachments:
        #POST /issues.json
        #{
        #  "issue": {
        #    "project_id": "1",
        #    "subject": "Creating an issue with a uploaded file",
        #    "uploads": [
        #    {"token": "7167.ed1ccdb093229ca1bd0b043618d88743", "filename": "image1.png", "content_type": "image/png"},
        #    {"token": "7168.d595398bbb104ed3bba0eed666785cc6", "filename": "image2.png", "content_type": "image/png"}
        #    ]
        #  }
        #}
        pass

    def find_user(self, email):
        response = self.query(f"/users.json?name={email}")
        # TODO better error checking 
        return response.users[0]
    
    def find_ticket(self, ticket_num:int):
        response = self.query(f"/issues.json?issue_id={ticket_num}")
        if response.total_count > 0:
            return response.issues[0]
        else:
            log.warning(f"Unknown ticket number: {ticket_num}")
            return None

    def find_ticket_from_str(self, str):
        # for now, this is a trivial REGEX to match '#nnn' in a string, and return ticket #nnn
        match = re.search(r'#(\d+)', str)
        if match:
            ticket_num = int(match.group(1))
            return self.find_ticket(ticket_num)
        else:
            log.warning(f"Unable to match ticket number in: {str}")
            return None
    
    def create_user(self, email, first, last):
        user = {
            'login': email,
            'firstname': 'test-first',
            'lastname': 'test-last',
            'mail': email,
        }
        # on create, assign watcher: sender.

    def most_recent_ticket_for(self, email):
        # get the user record for the email
        user = self.find_user(email)

        if user:
            # query open tickets for user, sorted by most recent, limit 1
            response = self.query(f"/issues.json?author_id={user.id}")
            if response.total_count > 0:
                return response.issues[0]
            else:
                log.info(f"No recent open ticket found for: {user}")
                return None
        else:
            log.warning(f"Unknown email: {email}")
            return None

    

    def query(self, query_str: str):
        """run a query against a redmine instance"""
        headers = {
            'User-Agent': 'netbot/0.0.1', # TODO update to project version, and add version management
            'Content-Type': 'application/json',
            'X-Redmine-API-Key': self.token,
        }
        # run the query with the 
        r = requests.get(f"{self.url}{query_str}", headers=headers)
        root = json.loads(r.text, object_hook= lambda x: SimpleNamespace(**x))
        #root = json.loads(r.text, object_hook=lambda d: namedtuple('Issue', d.keys())(*d.values()))

        # check for error
        #if root.errors:
        #    log.error(f"Error running |{query_str}|: {root.errors}")
        #    return None

        return root


## Local testing - REMOVE
#from dotenv import load_dotenv
#load_dotenv()
#client = Client()
#ticket = client.find_ticket_from_str("this is a test of #93 to see what happens")
#print(client.most_recent_ticket_for("johnelliott703@gmail.com"))
#print(client.find_user("johnelliott703@gmail.com"))
