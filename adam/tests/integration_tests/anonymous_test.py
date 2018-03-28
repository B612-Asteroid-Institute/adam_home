# This is janky. Why do we have to do this?
import sys
sys.path.append('..')

from adam import Service
from adam import ConfigManager

import json
import unittest

import os

class AnonymousTest(unittest.TestCase):
    """Tests anonymous access to API.
    
    """
    def setUp(self):
        config = ConfigManager(os.getcwd() + '/test_config.json').get_config()
        config.set_token("")
        self.service = Service(config)
        self.assertTrue(self.service.setup())

    def tearDown(self):
        self.service.teardown()
        
    def test_access(self):
        projects = self.service.get_projects_module()
        projects.print_projects()
        

if __name__ == '__main__':
    unittest.main()