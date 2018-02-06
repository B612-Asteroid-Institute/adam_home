"""
    service.py
"""
# This is janky. Why do we have to do this?
import sys
sys.path.append('..')

import adam
from adam import RestRequests
from adam import AuthorizingRestProxy
from adam import Auth
from adam import Batch
from adam import BatchRunner
from adam import Groups
from adam import Projects
from adam import Timer
from adam.batch import Batches

import datetime

class Service():
    """Module wrapping the REST API and associated client libraries. The goal of this
    module is to make it very easy and readable to do basic operations against a 
    dev setup. As such, it is not usable for production client code, but can serve as
    an example for clients to follow.

    """
    def __init__(self):
        self.batch_runs = []
    
    def setup(self, url, token):
        timer = Timer()
        timer.start("Setup")
        
        rest = RestRequests(url)
        self.auth = Auth(rest)
        if not self.auth.authorize(token):
            timer.stop()
            return False
        
        self.rest = AuthorizingRestProxy(rest, self.auth.get_token())
        self.projects = Projects(self.rest)
        self.batches = Batches(self.rest)
        self.groups = Groups(self.rest)
        
        self.batch_runner = BatchRunner(self.batches)
        
        # Also sets up a project to work in.
        self.project = self.projects.new_project(None, None,
            "Test project created at " + str(datetime.datetime.now()))
        print("Set up project with uuid " + self.project.get_uuid())
        
        timer.stop()
        return True
        
    def teardown(self):
        timer = Timer()
        timer.start("Teardown")
        self.projects.delete_project(self.project.get_uuid())
        timer.stop()
            
    def get_projects_module(self):
        return self.projects
    
    def get_batches_module(self):
        return self.batches
    
    def get_groups_module(self):
        return self.groups
    
    def get_batch_runner(self):
        return self.batch_runner
        
    def add_dummy_batch(self, days_to_propagate):
        if (days_to_propagage > 36500):
            print("Server has trouble handling propagation durations longer than 100 years. Try something smaller.")
            return

        now = datetime.datetime.utcnow()
        later = now + datetime.timedelta(days_to_propagate)
        
        batch_run = Batch(self.rest)
        batch_run.set_start_time(now.isoformat() + 'Z')
        batch_run.set_end_time(later.isoformat() + 'Z')

        state_vec = [130347560.13690618,
                     -74407287.6018632,
                     -35247598.541470632,
                     23.935241263310683,
                     27.146279819258538,
                     10.346605942591514]
        batch_run.set_state_vector(now.isoformat() + 'Z', state_vec)

        batch_run.set_step_size(3600, 'min')
        batch_run.set_mass(500.5)
        batch_run.set_solar_rad_area(25.2)
        batch_run.set_solar_rad_coeff(1.2)
        batch_run.set_drag_area(33.3)
        batch_run.set_drag_coeff(2.5)
        
        batch_run.set_originator('Test')
        batch_run.set_object_name('TestObj')
        batch_run.set_object_id('TestObjId')
        batch_run.set_description('Created by test at ' + str(now) + 'Z')
        batch_run.set_project(self.project.get_uuid())
        
        self.batch_runner.add_batch(batch_run)
        