from adam import Service
from adam import ConfigManager
from adam import Batch
from adam import PropagationParams
from adam import OpmParams
from adam import BatchRunManager

import unittest

import os
import datetime


class HypercubeTest(unittest.TestCase):
    """Tests hypercube propagation.

    """

    def setUp(self):
        config = ConfigManager(os.getcwd() + '/test_adam_config.json').get_config()
        self.service = Service(config)
        self.assertTrue(self.service.setup())
        self.working_project = self.service.new_working_project()
        self.assertIsNotNone(self.working_project)

    def tearDown(self):
        self.service.teardown()

    def new_hypercube_batch(self, hypercube):
        now = datetime.datetime.utcnow()
        later = now + datetime.timedelta(365 * 10)  # 10 years

        propagation_params = PropagationParams({
            'start_time': now.isoformat() + 'Z',
            'end_time': later.isoformat() + 'Z',
            'step_size': 0,
            'project_uuid': self.working_project.get_uuid(),
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

            # Lower triangular covariance matrix (21 elements in a list)
            'covariance': [
                3.331349476038534e-04,
                4.618927349220216e-04, 6.782421679971363e-04,
                -3.070007847730449e-04, -4.221234189514228e-04, 3.231931992380369e-04,
                -3.349365033922630e-07, -4.686084221046758e-07, 2.484949578400095e-07, 4.296022805587290e-10,  # NOQA (we want to keep the visual triangle)
                -2.211832501084875e-07, -2.864186892102733e-07, 1.798098699846038e-07, 2.608899201686016e-10, 1.767514756338532e-10,  # NOQA
                -3.041346050686871e-07, -4.989496988610662e-07, 3.540310904497689e-07, 1.869263192954590e-10, 1.008862586240695e-10, 6.224444338635500e-10],  # NOQA
            'perturbation': 3,
            'hypercube': hypercube,
        })

        return Batch(propagation_params, opm_params)

    def test_faces(self):
        batch = self.new_hypercube_batch('FACES')

        runner = BatchRunManager(self.service.get_batches_module(), [batch])
        runner.run()
        self.assertEqual('COMPLETED', batch.get_calc_state())

        parts = batch.get_results().get_parts()
        self.assertEqual(13, len(parts))

    def test_corners(self):
        batch = self.new_hypercube_batch('CORNERS')

        runner = BatchRunManager(self.service.get_batches_module(), [batch])
        runner.run()
        self.assertEqual('COMPLETED', batch.get_calc_state())

        parts = batch.get_results().get_parts()
        self.assertEqual(65, len(parts))


if __name__ == '__main__':
    unittest.main()
