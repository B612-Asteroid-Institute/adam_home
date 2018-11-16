from adam import Service
from adam import PropagationParams
from adam import OpmParams
from adam import ConfigManager
from adam import BatchPropagation
from adam import BatchPropagations
from adam import RunnableManager

import unittest
import datetime
import os


class RunnableManagerTest(unittest.TestCase):

    def setUp(self):
        config = ConfigManager(os.getcwd() + '/test_adam_config.json').get_config('dev')
        self.service = Service(config)
        self.assertTrue(self.service.setup())
        self.working_project = self.service.new_working_project()
        self.assertIsNotNone(self.working_project)

    def tearDown(self):
        self.service.teardown()

    def new_batch_propagation(self):
        now = datetime.datetime.utcnow()
        later = now + datetime.timedelta(10 * 365)

        propagation_params = PropagationParams({
            'start_time': now.isoformat() + 'Z',
            'end_time': later.isoformat() + 'Z',
            'step_size': 60 * 60,  # 1 hour.
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

        return BatchPropagation(propagation_params, opm_params)

    def test_runnable_manager(self):
        batch_propagations = [self.new_batch_propagation() for i in range(3)]
        batch_propagations_module = BatchPropagations(self.service.rest)

        manager = RunnableManager(
            batch_propagations_module, batch_propagations, self.working_project.get_uuid())
        manager.run()

        for prop in batch_propagations:
            self.assertEqual(
                'COMPLETED', prop.get_runnable_state().get_calc_state())

            self.assertEqual(len(prop.get_final_state_vectors()),
                             len(prop.get_children()))
            for i in range(len(prop.get_final_state_vectors())):
                self.assertEqual(
                    prop.get_final_state_vectors()[i],
                    prop.get_children()[i].get_final_state_vector())


if __name__ == '__main__':
    unittest.main()
