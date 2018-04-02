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

class KeplerianTest(unittest.TestCase):
    """Integration test of using keplerian elements instead of cartesian.
    
    """
    def setUp(self):
        config = ConfigManager(os.getcwd() + '/test_config.json').get_config()
        self.service = Service(config)
        self.assertTrue(self.service.setup())
        self.working_project = self.service.new_working_project()
        self.assertIsNotNone(self.working_project)

    def tearDown(self):
        self.service.teardown()
        
    def make_cartesian_and_keplerian_batches(self, start_time_str, end_time_str):
        # These are equivalent cartesian and keplerian elements.
        keplerian_elements = [
            3.1307289138037175E8,  # Semimajor axis (km)
            0.5355029800000188,  # Eccentricity
            0.4090995347727893,  # Inclination (deg)
            5.7344265189168055,  # Right ascension of ascending node (deg)
            6.2830852879040275,  # Argument of pericenter (aka periapsis) (deg)
            -2.216878629258714,  # True anomaly (deg)
            1.327124400419394E11  # Gravitational constant, this one for the sun (km^3/s^2)
        ]

        cartesian_state_vector = [
            -3.065363415010223E11, -1.1097955684640254E11, -4.812970642252724E10,  # x, y, z
            15759.855276409047, -10587.56732919585, -4589.673432886973  # dx, dy, dZ
        ]
        
        propagation_params = PropagationParams({
            'start_time': start_time_str,
            'end_time': end_time_str,
            'step_size': 0,
            'project_uuid': self.working_project.get_uuid(),
            'description': 'Created by test at ' + start_time_str
        })
        opm_params_templ = {
            'epoch': start_time_str,
            'keplerian_elements': keplerian_elements,
            
            'mass': 500.5,
            'solar_rad_area': 25.2,
            'solar_rad_coeff': 1.2,
            'drag_area': 33.3,
            'drag_coeff': 2.5,
            
            'originator': 'Test',
            'object_name': 'TestObj',
            'object_id': 'TestObjId',
        }

        cartesian_opm_params = opm_params_templ.copy()
        cartesian_opm_params['state_vector'] = cartesian_state_vector

        keplerian_opm_params = opm_params_templ.copy()
        keplerian_opm_params['keplerian_elements'] = keplerian_elements
        
        cartesian = Batch(propagation_params, OpmParams(cartesian_opm_params))
        keplerian = Batch(propagation_params, OpmParams(keplerian_opm_params))
        return cartesian, keplerian
        
    def test_keplerian_and_cartesian(self):
        start = datetime.datetime.now()
        end = start + datetime.timedelta(10 * 365)  # 10 years
        start_time_str = start.isoformat() + 'Z'
        end_time_str = end.isoformat() + 'Z'

        cartesian, keplerian = self.make_cartesian_and_keplerian_batches(start_time_str, end_time_str)
    
        BatchRunManager(self.service.get_batches_module(), [cartesian, keplerian]).run()

        cartesian_end_state = cartesian.get_results().get_end_state_vector()
        keplerian_end_state = keplerian.get_results().get_end_state_vector()

        difference = np.subtract(cartesian_end_state, keplerian_end_state)
        npt.assert_allclose(difference[0:3], [0, 0, 0], rtol=0, atol=1e-3)
        npt.assert_allclose(difference[3:6], [0, 0, 0], rtol=0, atol=1e-10)
        

if __name__ == '__main__':
    unittest.main()