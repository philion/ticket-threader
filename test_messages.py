#!/usr/bin/env python3

import unittest
import os, glob

import imap

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


if __name__ == '__main__':
    unittest.main()