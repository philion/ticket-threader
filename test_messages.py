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


if __name__ == '__main__':
    unittest.main()