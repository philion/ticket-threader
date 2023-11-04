#!/usr/bin/env python3

import unittest
import logging
import os, glob

from dotenv import load_dotenv

import imap
import redmine

logging.basicConfig(level=logging.DEBUG)
#log = logging.getLogger(__name__)


class TestMessages(unittest.TestCase):

    def test_messages_examples(self):
        # open 
        for filename in glob.glob('test_messages/*.eml'):
            with open(os.path.join(os.getcwd(), filename), 'rb') as file:
                message = imap.parse_message(file.read())
                print(message)

    def test_email_address_parsing(self):
        from_address =  "Esther Jang <infrared@cs.washington.edu>"
        first, last, addr = imap.parse_email_address(from_address)
        self.assertEqual(first, "Esther")
        self.assertEqual(last, "Jang")
        self.assertEqual(addr, "infrared@cs.washington.edu")

    # disabled so I don't flood the system with files
    def skip_test_upload(self):
        load_dotenv()
        client = redmine.Client()

        with open("test_messages/message-126.eml", 'rb') as file:
            message = imap.parse_message(file.read())
            print(message)
            for attachment in message.attachments:
                client.append_attachment("93", "philion", attachment.payload, attachment.name, attachment.content_type)


if __name__ == '__main__':
    unittest.main()