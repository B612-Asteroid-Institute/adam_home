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
from adam import Projects
from adam.batch import Batches

import datetime
import tabulate
import threading

class Timer(object):
    def __init__(self):
        self.stack = []
    
    def start(self, description):
        self.stack.append([description, datetime.datetime.now()])
    
    def stop(self):
        latest = self.stack.pop()
        time_diff = (datetime.datetime.now() - latest[1]).total_seconds()
        print("[" + str(time_diff) + "] " + latest[0])

class Service(object):
    """Module wrapping the REST API and associated client libraries. The goal of this
    module is to make it very easy and readable to do basic operations against a 
    dev setup. As such, it is not usable for production client code, but can serve as
    an example for clients to follow.

    """
    def __init__(self):
        self.batch_runs = []
        self.timer = Timer()
        

    def __repr__(self):
        """
        Args:
            None

        Returns:
            A string describing the contents of this object.
        """
        return "TODO"
    
    def setup(self, url, token):
        self.timer.start("Setup")
        
        rest = RestRequests(url)
        self.auth = Auth(rest)
        if not self.auth.authorize(token):
            self.timer.stop()
            return False
        
        self.rest = AuthorizingRestProxy(rest, self.auth.get_token())
        self.projects = Projects(self.rest)
        self.batches = Batches(self.rest)
        
        # Also sets up a project to work in.
        self.project = self.projects.new_project(None, None,
            "Test project created at " + str(datetime.datetime.now()))
        print("Set up project with uuid " + self.project.get_uuid())
        
        self.timer.stop()
        return True
        
    def teardown(self):
        self.timer.start("Teardown")
        print('\n')
        
#         self.timer.start('Deleting ' + str(len(self.batch_runs)) + ' batches...')
#         def delete_batch(i):
#             batch = self.batch_runs[i]
#             if not batch.get_uuid() is None:
#                 self.batches.delete_batch(batch.get_uuid())
#         
#         threads = []
#         for i in range(len(self.batch_runs)):
#             t = threading.Thread(target=delete_batch, args=(i,))
#             threads.append(t)
#             t.start()
#         for t in threads:
#             t.join()
#         self.timer.stop()
        
        self.timer.start('Deleting project')
        self.projects.delete_project(self.project.get_uuid())
        self.timer.stop()
        self.timer.stop()
            
    
    def add_dummy_batch(self, days_to_propagate):
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

        # Optional parameters (uncomment to use)
#         batch_run.set_propagator_uuid("00000000-0000-0000-0000-000000000002")    # Only Sun as point mass, nothing else
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
        
        self.batch_runs.append(batch_run)
    
    def get_batches_status(self):
#         self.timer.start("Refreshing batches")
        batch_runs_by_state = {'PENDING': [], 'RUNNING': [], 'COMPLETED': [], 'FAILED': []}
        states = self.batches.get_batch_states()
        for batch in self.batch_runs:
            batch_runs_by_state[states[batch.get_uuid()]].append(batch.get_uuid())
        
#         self.timer.stop()
        return batch_runs_by_state
    
    def _runs_in_states(self, batch_runs_by_state, states):
        total = 0
        for state in states:
            total = total + len(batch_runs_by_state[state])
        return total       
    
    def _submit_batches(self, do_concurrently):
        if do_concurrently:
            def submit_batch(i):
                self.batch_runs[i].submit()

            threads = []
            for i in range(len(self.batch_runs)):
                t = threading.Thread(target=submit_batch, args=(i,))
                threads.append(t)
                t.start()
            for t in threads:
                t.join()
        else:
            for batch in self.batch_runs:
                batch.submit()
    
    def run_batches(self, do_concurrently):
        self.timer.start("Submitting batches")
        self._submit_batches(do_concurrently)
        self.timer.stop()
        
        self.timer.start("Waiting for running")
        any_are_running = False
        batch_runs_by_state = self.get_batches_status()
#         print(tabulate.tabulate([[state, len(batch_runs_by_state[state])] for state in batch_runs_by_state]))
        while not self._runs_in_states(batch_runs_by_state, ['COMPLETED', 'FAILED']) == len(self.batch_runs):
        
            if self._runs_in_states(batch_runs_by_state, ['COMPLETED', 'FAILED', 'RUNNING']) > 0 and not any_are_running:
                any_are_running = True
                self.timer.stop()
                self.timer.start("Running")
                
            batch_runs_by_state = self.get_batches_status()
#             print(tabulate.tabulate([[state, len(batch_runs_by_state[state])] for state in batch_runs_by_state]))
            
        self.timer.stop()
        