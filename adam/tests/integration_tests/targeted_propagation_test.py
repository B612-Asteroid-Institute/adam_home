from adam import Service
from adam import PropagationParams
from adam import OpmParams
from adam import ConfigManager
from adam import TargetedPropagation
from adam import TargetedPropagations
from adam import TargetingParams

import unittest
import datetime
import os


class TargetedPropagationTest(unittest.TestCase):

    def setUp(self):
        config = ConfigManager(os.getcwd() + '/test_config.json').get_config('local-dev')
        self.service = Service(config)
        self.assertTrue(self.service.setup())
        self.working_project = self.service.new_working_project()
        self.assertIsNotNone(self.working_project)

    def tearDown(self):
        self.service.teardown()

    def new_targeted_propagation(self):
        start = '2013-05-25T00:00:02.000000Z'
        end = '2018-04-25T03:06:14.200000Z'
        propagation_params = PropagationParams({
            'start_time': start,
            'end_time': end,
            'project_uuid': self.working_project.get_uuid(),
            'description': 'Created by test at ' + start
        })

        state_vec = [-1.4914794358536252e+8,
                     1.0582106861692128e+8,
                     6.0492834101479955e+7,
                     -11.2528789273597756,
                     -22.3258231726462242,
                     -9.7271222877710155]
        opm_params = OpmParams({
            'epoch': start,
            'state_vector': state_vec,
        })

        return TargetedPropagation(propagation_params, opm_params, TargetingParams(
            {'target_distance_from_earth': 1.0e4, 'tolerance': 1.0}))

    def test_targeted_propagation(self):
        targeted_propagation = self.new_targeted_propagation()

        props = TargetedPropagations(self.service.rest)

        props.insert(targeted_propagation, self.working_project.get_uuid())
        uuid = targeted_propagation.get_uuid()
        self.assertIsNotNone(uuid)

        runnable_state = props.get_runnable_state(uuid)
        self.assertIsNotNone(runnable_state)
        while (runnable_state.get_calc_state() != 'COMPLETED' and runnable_state.get_calc_state() != 'FAILED'):
            print(runnable_state.get_calc_state())
            runnable_state = props.get_runnable_state(uuid)
            self.assertIsNotNone(runnable_state)
        self.assertEqual('COMPLETED', runnable_state.get_calc_state())
        self.assertIsNone(runnable_state.get_error())

        runnable_state_list = props.get_runnable_states(
            self.working_project.get_uuid())
        self.assertEqual(1, len(runnable_state_list))

        props.update_with_results(targeted_propagation)
        print(targeted_propagation.get_maneuver())
        self.assertIsNotNone(targeted_propagation.get_ephemeris())

        fresh_targeted_prop = props.get(uuid)
        self.assertIsNotNone(fresh_targeted_prop)
        self.assertEqual(uuid, fresh_targeted_prop.get_uuid())

        props.delete(uuid)

        self.assertIsNone(props.get(uuid))


if __name__ == '__main__':
    unittest.main()
