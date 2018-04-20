from adam import Service
from adam import Batch
from adam import PropagationParams
from adam import OpmParams
from adam import BatchRunManager
from adam import ConfigManager

import unittest
import datetime
import os


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

    def test_ref_frame(self):
        now = datetime.datetime.now()
        later = now + datetime.timedelta(365)  # 1 year
        start_time_str = now.isoformat() + 'Z'
        end_time_str = later.isoformat() + 'Z'

        state_vec = [130347560.13690618,
                     -74407287.6018632,
                     -35247598.541470632,
                     23.935241263310683,
                     27.146279819258538,
                     10.346605942591514]

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

            'center_name': 'EARTH',
            'ref_frame': 'EMEME2000',
        })

        batch = Batch(propagation_params, opm_params)
        runner = BatchRunManager(self.service.get_batches_module(), [batch])
        runner.run()
        end_state_1 = batch.get_results().get_end_state_vector()
        print("Final state at %s" % end_state_1)

        opm_params = OpmParams({
            'epoch': start_time_str,
            'state_vector': state_vec,

            'center_name': 'SUN',
            'ref_frame': 'ICRF',
        })
        batch = Batch(propagation_params, opm_params)
        runner = BatchRunManager(self.service.get_batches_module(), [batch])
        runner.run()
        end_state_2 = batch.get_results().get_end_state_vector()
        print("Final state at %s" % end_state_2)

        self.assertNotEqual(end_state_1, end_state_2)


if __name__ == '__main__':
    unittest.main()
