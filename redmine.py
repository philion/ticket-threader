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
#from dataclasses import dataclass

#logging.basicConfig(level=logging.DEBUG)
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

        r = requests.post(
            url=f"{self.url}/issues.json", 
            data=json.dumps(data), 
            headers=headers)
        
        print(f"create_ticket response: {r}")
        
        # check status
        #if r.status_code != 201:
        # check 201 status
        #root = json.loads(r.text, object_hook= lambda x: SimpleNamespace(**x))
        #ticket = root.ticket[0]
        #return ticket

    def append_message(self, ticket_id:str, user_id:str, note:str, attachments):
        headers = { # TODO DRY headers
            'User-Agent': 'netbot/0.0.1', # TODO update to project version, and add version management
            'Content-Type': 'application/json',
            'X-Redmine-API-Key': self.token,
            'X-Redmine-Switch-User': user_id, # Make sure the comment is noted by the correct user
        }

        # PUT a simple JSON structure
        data = {
            'issue': {
                'notes': note,
                'uploads': []
            }
        }

        # add the attachments
        if len(attachments) > 0:
            for a in attachments:
                data['issue']['uploads'].append({
                    "token": a.token, 
                    "filename": a.name,
                    "content_type": a.content_type,
                })

        r = requests.put(
            url=f"{self.url}/issues/{ticket_id}.json", 
            data=json.dumps(data),
            headers=headers)
        
        # check status
        if r.status_code != 204:
            root = json.loads(r.text, object_hook= lambda x: SimpleNamespace(**x))
            log.error(f"append_message, status={r.status_code}: {root}")
            # throw exception?


    def upload_file(self, user_id, data, filename, content_type):
        # POST /uploads.json?filename=image.png
        # Content-Type: application/octet-stream
        # (request body is the file content)
        
        headers = { # TODO DRY headers
            'User-Agent': 'netbot/0.0.1', # TODO update to project version, and add version management
            'Content-Type': 'application/octet-stream',
            'X-Redmine-API-Key': self.token,
            'X-Redmine-Switch-User': user_id, # Make sure the comment is noted by the correct user
        }

        r = requests.post(
            url=f"{self.url}/uploads.json?filename={filename}", 
            files={ 'upload_file': (filename, data, content_type) },
            headers=headers
        )
        
        # 201 response: {"upload":{"token":"7167.ed1ccdb093229ca1bd0b043618d88743"}}
        if r.status_code == 201:
            # all good, get token
            root = json.loads(r.text, object_hook= lambda x: SimpleNamespace(**x))
            token = root.upload.token
            log.info(f"Uploaded {filename} {content_type}, got token={token}")
            return token
        else:
            #print(vars(r))
            log.error(f"Error uploading {filename} {content_type} - response:{r}")
            # todo throw exception

    def upload_attachments(self, user_id, attachments):
        # uploads all the attachments, 
        # sets the upload token for each 
        for a in attachments:
            token = self.upload_file(user_id, a.payload, a.name, a.content_type)
            a.set_token(token)

    ### OLD REMOVE
    def xxx_append_attachment(self, ticket_id, user_id, data, filename, content_type):
        # upload the data as a new file
        upload_token = self.upload_file(user_id, data, filename, content_type)

        # then PUT the upload to the issue API
        headers = { # TODO DRY headers
            'User-Agent': 'netbot/0.0.1', # TODO update to project version, and add version management
            'Content-Type': 'application/json',
            'X-Redmine-API-Key': self.token,
            'X-Redmine-Switch-User': user_id, # Make sure the comment is noted by the correct user
        }

        # PUT a simple JSON structure with the uploaded file info
        data = {
            'issue': {
                'notes': f"Uploading attachment {filename} to ticket #{ticket_id}.",
                'uploads': [
                    { 
                        "token": upload_token, 
                        "filename": filename,
                        "content_type": content_type,
                    }
                ]
            }
        }

        r = requests.put(
            url=f"{self.url}/issues/{ticket_id}.json", 
            data=json.dumps(data),
            headers=headers)

        print(f"append_attachment response: {r}")

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

    def find_ticket_from_str(self, str:str):
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
            # query open tickets created by user, sorted by most recently updated, limit 1
            response = self.query(f"/issues.json?author_id={user.id}&status_id=open&sort=updated_on:desc&limit=1")

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

        # check 200 status code

        root = json.loads(r.text, object_hook= lambda x: SimpleNamespace(**x))

        return root