# This is janky. Why do we have to do this?
import sys
sys.path.append('..')

from adam import Service
from adam.batch import Batch

import json
import unittest
import datetime

import os

class BatchRunnerTest(unittest.TestCase):
    """Integration test of batch running.
    
    """
    def setUp(self):
        self.service = Service()
        self.assertTrue(self.service.setup_with_test_account())

    def tearDown(self):
        self.service.teardown()
        
    def add_dummy_batch(self, days_to_propagate):
        if (days_to_propagate > 36500):
            print("Server has trouble handling propagation durations longer than 100 years. Try something smaller.")
            return

        now = datetime.datetime.utcnow()
        later = now + datetime.timedelta(days_to_propagate)
        
        batch_run = Batch(self.service.get_rest())
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
        batch_run.set_project(self.service.get_working_project().get_uuid())
        
        self.service.get_batch_runner().add_batch(batch_run)
        
    def test_small_batch(self):
        num_batches = 5
        num_threads = 3
        
        for i in range(num_batches):
            self.add_dummy_batch(365 * 50)  # 50 years
        
        self.service.get_batch_runner().run_batches(num_threads)
        

if __name__ == '__main__':
    unittest.main()