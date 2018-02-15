# This is janky. Why do we have to do this?
import sys
sys.path.append('..')

from adam import PropagationParams
from adam import OpmParams
from adam import Service
from adam import StmPropagationModule

import unittest
import datetime

import numpy as np
import numpy.testing as npt

class StmPropagationModuleTest(unittest.TestCase):
    """Basic integration test to demonstrate use of service tester.
    
    """
    def setUp(self):
        self.service = Service()
        self.assertTrue(self.service.setup_with_test_account(prod=False))
        self.stm_module = StmPropagationModule(self.service.get_batches_module())

    def tearDown(self):
        self.service.teardown()
        
    def test_basic_stm(self):
        state_vec = [130347560.13690618,
                     -74407287.6018632,
                     -35247598.541470632,
                     23.935241263310683,
                     27.146279819258538,
                     10.346605942591514]
    
        start_time = datetime.datetime(2017, 10, 4, 0, 0, 0 , 123456)
        end_time = datetime.datetime(2018, 10, 4, 0, 0, 0 , 123456)
        
        propagation_params = PropagationParams({
            'start_time': start_time.isoformat() + 'Z',
            'end_time': end_time.isoformat() + 'Z',
            'project_uuid': self.service.get_working_project().get_uuid(),
            'description': 'Created by test at ' + start_time.isoformat() + 'Z'
        })
        
        opm_params = OpmParams({
            'epoch': start_time.isoformat() + 'Z',
            'state_vector': state_vec,
        })
        
        end_state, stm = self.stm_module.run_stm_propagation(
            propagation_params, opm_params)

        # Taken from printed output of ../state_stm_propagation.py
        expected_end_state = np.array([-37523497.931654416, 492950622.8491298, 204482176.63445434, -11.336957217854795, 7.18499733419028, 3.3597496059480085])
        expected_stm = np.matrix(
            [[9.70874844e+00, -1.21563565e+00, -9.26967637e-01, 5.34214567e+07, 1.64329953e+07, 5.30094892e+06],
            [7.11171945e+00, -3.24202476e+00, -5.93038128e-01, 3.90278376e+07, 3.82420496e+07, 9.62761631e+06],
            [2.50503331e+00, -3.00334152e-01, -2.62144498e+00, 1.46131045e+07, 1.04218322e+07, 1.53347450e+07],
            [2.14264136e-07, -2.82295666e-08, -2.23357566e-08, 1.33259336e+00, 6.98930318e-01, 2.41824966e-01],
            [4.69172199e-07, -2.03571494e-07, -6.32223023e-08, 2.52995851e+00, 2.04570983e+00, 7.47014439e-01],
            [1.82661672e-07, -4.57388872e-08, -1.15455121e-07, 9.96459361e-01, 8.11376173e-01, 3.16765622e-01]]
        )
        
        npt.assert_allclose(expected_end_state, np.array(end_state), rtol=1e-8, atol=0)
        npt.assert_allclose(expected_stm.getA(), stm.getA(), rtol=1e-8, atol=0)
        

if __name__ == '__main__':
    unittest.main()