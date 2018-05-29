from adam import Service
from adam import Batch
from adam import PropagationParams
from adam import OpmParams
from adam import BatchRunManager
from adam import ConfigManager

import unittest
import datetime
import os

import numpy as np
import numpy.testing as npt


class ReferenceFrameTest(unittest.TestCase):
    """Integration test of using different reference frames.

    """

    def setUp(self):
        config = ConfigManager(os.getcwd() + '/test_config.json').get_config('dev')
        self.service = Service(config)
        self.assertTrue(self.service.setup())
        self.working_project = self.service.new_working_project()
        self.assertIsNotNone(self.working_project)

    def tearDown(self):
        self.service.teardown()

    # This test and the following test are exactly the same propagation, but are done
    # in two different reference frames.
    def test_icrf(self):
        start_time_str = "2000-01-01T11:58:55.816Z"
        end_time_str = "2009-07-21T21:55:08.813Z"

        sun_icrf_state_vec =   [-306536341.5010222, -110979556.84640282, -48129706.42252728,
                                15.75985527640906, -10.587567329195842, -4.589673432886975]

        propagation_params = PropagationParams({
            'start_time': start_time_str,
            'end_time': end_time_str,
            'step_size': 86400,
            'project_uuid': self.working_project.get_uuid(),
            'description': 'Created by test at ' + start_time_str
        })
        opm_params = OpmParams({
            'epoch': start_time_str,
            'state_vector': sun_icrf_state_vec,

            'center_name': 'SUN',
            'ref_frame': 'ICRF',
        })
        batch = Batch(propagation_params, opm_params)
        runner = BatchRunManager(self.service.get_batches_module(), [batch])
        runner.run()
        end_state = batch.get_results().get_end_state_vector()
        expected_end_state = [73978163.61069362, -121822760.05571477, -52811158.83249758, 
                            31.71000343989318, 29.9657246374751, .6754531613947713]

        difference = np.subtract(expected_end_state, end_state)
        print("Difference is %s" % difference)

        npt.assert_allclose(difference[0:3], [0, 0, 0], rtol=0, atol=.02)
        npt.assert_allclose(difference[3:6], [0, 0, 0], rtol=0, atol=.00002)

        self.assertTrue("ICRF" in batch.get_results().get_parts()[-1].get_ephemeris())

    def test_sun_ememe(self):
        start_time_str = "2000-01-01T11:58:55.816Z"
        end_time_str = "2009-07-21T21:55:08.813Z"

        sun_ememe_state_vec = [-306536346.18024945, -120966638.54521248, -12981.069369263947,
                                15.759854830195243, -11.539570959741736, 0.0005481049628786039]

        propagation_params = PropagationParams({
            'start_time': start_time_str,
            'end_time': end_time_str,
            'step_size': 86400,
            'project_uuid': self.working_project.get_uuid(),
            'description': 'Created by test at ' + start_time_str
        })
        opm_params = OpmParams({
            'epoch': start_time_str,
            'state_vector': sun_ememe_state_vec,

            'center_name': 'SUN',
            'ref_frame': 'EMEME2000',
        })

        batch = Batch(propagation_params, opm_params)
        runner = BatchRunManager(self.service.get_batches_module(), [batch])
        runner.run()
        end_state = batch.get_results().get_end_state_vector()
        expected_end_state = [73978158.47632701, -132777272.5255892, 5015.073123970032,
                            31.710003506237434, 27.761693311026138, -11.299967713192564]

        difference = np.subtract(expected_end_state, end_state)
        print("Difference is %s" % difference)

        npt.assert_allclose(difference[0:3], [0, 0, 0], rtol=0, atol=.02)
        npt.assert_allclose(difference[3:6], [0, 0, 0], rtol=0, atol=.00002)

        # THIS IS VERY STRANGE, BUT A FACT.
        # The values returned are actually in Sun-centered EMEME, but the ephemeris
        # reports that it is in Sun-centered ICRF.
        self.assertTrue("ICRF" in batch.get_results().get_parts()[-1].get_ephemeris())
        self.assertFalse("EMEME" in batch.get_results().get_parts()[-1].get_ephemeris())


if __name__ == '__main__':
    unittest.main()
