"""
    service.py
"""

from adam.auth import Auth
from adam.batch import Batch
from adam.batch import Batches
from adam.group import Groups
from adam.project import Projects
from adam.timer import Timer
from adam.rest_proxy import RestRequests
from adam.rest_proxy import AuthorizingRestProxy
from adam.rest_proxy import LoggingRestProxy

import datetime

class Service():
    """Module wrapping the REST API and associated client libraries. The goal of this
    module is to make it very easy and readable to do basic operations against a prod or
    dev setup.

    """
    def __init__(self):
        self.batch_runs = []
    
    def setup_with_test_account(self, prod=True):
        # These tokens belong to b612.adam.test@gmail.com (b612adam) which has
        # been given the permissions necessary to carry out various operations.
        if prod:
            token = "42MbDS0RbvVZF83aqXvapPvY6h62"
            url = "https://pro-equinox-162418.appspot.com/_ah/api/adam/v1"
            parent_project = "61c25677-c328-45c4-af22-a0a4d5e54826"
        else:
            token = "1YueO0qiWOTBJSZjdIynYTmJZDG3"
            url = "https://adam-dev-193118.appspot.com/_ah/api/adam/v1"
            parent_project = "88e2152d-e37e-437d-af88-65bca9374f34"
        return self.setup(url, token, parent_project)
    
    def setup(self, url, token, parent_project = None):
        timer = Timer()
        timer.start("Setup")
        
        self.parent_project = parent_project
        
        rest = RestRequests(url)
        self.auth = Auth(rest)
        
        if not self.auth.authorize(token):
            # Try one more time, since often the error is a session expired error and
            # seems to work fine on the second try.
            print("Encountered error, retrying authorization")
            if not self.auth.authorize(token):
                timer.stop()
                return False
        
        self.rest = AuthorizingRestProxy(rest, self.auth.get_token())
        self.projects = Projects(self.rest)
        self.batches = Batches(self.rest)
        self.groups = Groups(self.rest)
        
        # Also sets up a project to work in.
        self.project = self.projects.new_project(parent_project, None,
            "Test project created at " + str(datetime.datetime.now()))
        print("Set up project with uuid " + self.project.get_uuid())
        
        timer.stop()
        return True
        
    def teardown(self):
        timer = Timer()
        timer.start("Teardown")
        self.projects.delete_project(self.project.get_uuid())
        timer.stop()
    
    def careful_clean_up_projects(self):
        for p in self.projects.get_projects():
            if (not p.get_uuid() == "00000000-0000-0000-0000-000000000001" and
                not p.get_uuid() == "88e2152d-e37e-437d-af88-65bca9374f34" and
                not p.get_uuid() == "61c25677-c328-45c4-af22-a0a4d5e54826" and
                not p.get_uuid() == "ffffffff-ffff-ffff-ffff-ffffffffffff"):
                print("Deleting project " + p.get_uuid())
                try:
                    self.projects.delete_project(p.get_uuid())
                except:
                    print("Failed to delete project " + p.get_uuid() + ". Moving on...")
    
    def get_working_project(self):
        return self.project
            
    def get_projects_module(self):
        return self.projects
    
    def get_batches_module(self):
        return self.batches
    
    def get_groups_module(self):
        return self.groups
    
    def get_rest(self):
        # Note, this is only necessary because batches are currently more than pure data
        # objects and therefore need a rest accessor (and aren't built here).
        # Please don't use this extensively.
        return self.rest
        