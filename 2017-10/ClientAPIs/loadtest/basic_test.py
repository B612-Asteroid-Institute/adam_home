from service import Service

import json
import unittest

import os

class BasicTest(unittest.TestCase):
    """Basic integration test to demonstrate use of service tester.
    
    """
    def setUp(self):
        with open(os.getcwd() + '/token.txt', "r") as f:
            self.token = f.read()
        self.service = Service()
        self.assertTrue(self.service.setup("https://adam-dev-193118.appspot.com/_ah/api/adam/v1", self.token))

    def tearDown(self):
        self.service.teardown()
        
    def test_basic(self):
        for i in range(30):
            self.service.add_dummy_batch(365 * 50)  # 50 years
        
        self.service.run_batches(False)
        

if __name__ == '__main__':
    unittest.main()