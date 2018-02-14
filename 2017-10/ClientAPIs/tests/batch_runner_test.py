# This is janky. Why do we have to do this?
import sys
sys.path.append('..')

from adam import Service
from adam import Batch
from adam import PropagationParams
from adam import OpmParams
from adam.batch_runner import BatchRunManager

import json
import unittest
import datetime

import os

class BatchRunnerTest(unittest.TestCase):
    """Integration test of batch running.
    
    """
    def setUp(self):
        self.service = Service()
#         self.assertTrue(self.service.setup("http://localhost:8080/_ah/api/adam/v1", "1KT0bImQ83b2vEhDwPF0PZevYu92"))
        self.assertTrue(self.service.setup_with_test_account(prod=False))

    def tearDown(self):
        self.service.teardown()
        
    def new_dummy_batch(self, days_to_propagate):
        if (days_to_propagate > 36500):
            print("Server has trouble handling propagation durations longer than 100 years. Try something smaller.")
            return

        now = datetime.datetime.utcnow()
        later = now + datetime.timedelta(days_to_propagate)
        
        propagation_params = PropagationParams({
            'start_time': now.isoformat() + 'Z',
            'end_time': later.isoformat() + 'Z',
            'step_size': 60 * 60,  # 1 hour.
            'project_uuid': self.service.get_working_project().get_uuid(),
            'description': 'Created by test at ' + str(now) + 'Z'
        })
        
        state_vec = [130347560.13690618,
                     -74407287.6018632,
                     -35247598.541470632,
                     23.935241263310683,
                     27.146279819258538,
                     10.346605942591514]
        opm_params = OpmParams({
            'epoch': now.isoformat() + 'Z',
            'state_vector': state_vec,
            
            'mass': 500.5,
            'solar_rad_area': 25.2,
            'solar_rad_coeff': 1.2,
            'drag_area': 33.3,
            'drag_coeff': 2.5,
            
            'originator': 'Test',
            'object_name': 'TestObj',
            'object_id': 'TestObjId',
        })
        
        return Batch(propagation_params, opm_params)
        
    def test_small_batch(self):
        num_batches = 3
        
        duration = 365  # 1 year
        batches = [self.new_dummy_batch(duration) for i in range(num_batches)]
        
        runner = BatchRunManager(self.service.get_batches_module(), batches)
        print(runner)
        runner.run()
        print(runner.get_latest_statuses())
        

if __name__ == '__main__':
    unittest.main()