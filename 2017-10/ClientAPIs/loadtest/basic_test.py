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
        self.assertTrue(self.service.setup(
            "https://adam-dev-193118.appspot.com/_ah/api/adam/v1", self.token))
        #self.assertTrue(self.service.setup("http://localhost:8080/_ah/api/adam/v1", self.token))

    def tearDown(self):
        self.service.teardown()
        
    def test_basic(self):
        for i in range(1000):
            self.service.get_batch_runner().add_dummy_batch(365 * 100)  # 100 years
        
        self.service.get_batch_runner().run_batches(10)
        

if __name__ == '__main__':
    unittest.main()