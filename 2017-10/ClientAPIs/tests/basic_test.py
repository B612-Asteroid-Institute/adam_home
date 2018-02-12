# This is janky. Why do we have to do this?
import sys
sys.path.append('..')

from adam import Service

import json
import unittest

import os

class BasicTest(unittest.TestCase):
    """Basic integration test to demonstrate use of service tester.
    
    """
    def setUp(self):
        self.service = Service()
        self.assertTrue(self.service.setup_with_test_account(prod=False))

    def tearDown(self):
        self.service.teardown()
        
    def test_basic(self):
        print("Hello world")
        

if __name__ == '__main__':
    unittest.main()