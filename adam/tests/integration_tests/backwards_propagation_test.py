from adam import Service
from adam import Batch
from adam import PropagationParams
from adam import OpmParams
from adam import BatchRunManager
from adam import ConfigManager

import json
import unittest
import datetime
import os

import numpy as np
import numpy.testing as npt

class BackwardsPropagationTest(unittest.TestCase):
    """Integration test of backwards propagation.
    
    """
    def setUp(self):
        config = ConfigManager(os.getcwd() + '/test_config.json').get_config()
        self.service = Service(config)
        self.assertTrue(self.service.setup())
        self.working_project = self.service.new_working_project()
        self.assertIsNotNone(self.working_project)

    def tearDown(self):
        self.service.teardown()
        
    def make_batch(self, state_vec, start_time, end_time):
        start_time_str = start_time.isoformat() + 'Z'
        end_time_str = end_time.isoformat() + 'Z'
        
        propagation_params = PropagationParams({
            'start_time': start_time_str,
            'end_time': end_time_str,
            'step_size': 0,
            'project_uuid': self.working_project.get_uuid(),
            'description': 'Created by test at ' + start_time_str
        })
        opm_params = OpmParams({
            'epoch': start_time_str,
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
        
    def test_backwards_and_forwards(self):
        now = datetime.datetime.now()
        later = now + datetime.timedelta(10 * 365)  # 10 years
    
        state_vec = [130347560.13690618,
                     -74407287.6018632,
                     -35247598.541470632,
                     23.935241263310683,
                     27.146279819258538,
                     10.346605942591514]
        
        print("Starting at %s" % (state_vec))
        
        print("Propagating forward from %s to %s" % (now, later))
        batch = self.make_batch(state_vec, now, later)
        runner = BatchRunManager(self.service.get_batches_module(), [batch])
        runner.run()
        forward_end_state = batch.get_results().get_end_state_vector()
        print("Final state at %s" % forward_end_state)
        
        print("Propagating backward from %s to %s" % (later, now))
        batch = self.make_batch(forward_end_state, later, now)
        runner = BatchRunManager(self.service.get_batches_module(), [batch])
        runner.run()
        backwards_end_state = batch.get_results().get_end_state_vector()
        print("Final state at %s" % backwards_end_state)
        
        difference = np.subtract(state_vec, backwards_end_state)
        print("Difference is %s" % difference)

        npt.assert_allclose(difference[0:3], [0, 0, 0], rtol=0, atol=1e-3)
        npt.assert_allclose(difference[3:6], [0, 0, 0], rtol=0, atol=1e-10)
        

if __name__ == '__main__':
    unittest.main()