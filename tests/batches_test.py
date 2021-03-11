from adam import PropagationParams
from adam import OpmParams
from adam.batch import StateSummary
from adam import Batches

from adam.rest_proxy import _RestProxyForTest

import unittest


class BatchesTest(unittest.TestCase):
    """Unit tests for batches module

    """

    dummy_propagation_params = PropagationParams({
        'start_time': 'AAA',
        'end_time': 'BBB',
        'project_uuid': 'CCC'
    })
    dummy_opm_params = OpmParams({
        'epoch': 'DDD',
        'state_vector': [1, 2, 3, 4, 5, 6]
    })

    def _check_input(self, data_dict):
        """Check input data

        Checks input data by asserting the following:
            - start time = 'AAA'
            - end time = 'BBB'
            - step size = 86400 (default)
            - opm string in data dictionary is not None
            - originator = 'ADAM_User'
            - object name = 'dummy'
            - object ID = '001'
            - epoch and state vector are 'CCC' and [1, 2, 3, 4, 5, 6], respectively
            - object mass = 1000 (default)
            - object solar radiation area = 20 (default)
            - object solar radiation coefficient = 1 (default)
            - object drag area = 20 (default)
            - object drag coefficient = 2.2 (default)
            - propagator ID is default (none specified)

        Args:
            data_dict (dict) - input data for POST

        Returns:
            True
        """
        self.assertEqual(data_dict['start_time'], self.dummy_propagation_params.get_start_time())
        self.assertEqual(data_dict['end_time'], self.dummy_propagation_params.get_end_time())
        self.assertEqual(data_dict['project'], self.dummy_propagation_params.get_project_uuid())
        self.assertEqual(data_dict['step_duration_sec'], 86400)
        self.assertEqual(data_dict['propagator_uuid'], "00000000-0000-0000-0000-000000000001")
        opm = data_dict['opm_string']
        self.assertIsNotNone(opm)
        self.assertIn('ORIGINATOR = ADAM_User', opm)
        self.assertIn('OBJECT_NAME = dummy', opm)
        self.assertIn('OBJECT_ID = 001', opm)
        self.assertIn('EPOCH = DDD', opm)
        self.assertIn('X = 1', opm)
        self.assertIn('Y = 2', opm)
        self.assertIn('Z = 3', opm)
        self.assertIn('X_DOT = 4', opm)
        self.assertIn('Y_DOT = 5', opm)
        self.assertIn('Z_DOT = 6', opm)
        self.assertIn('MASS = 1000', opm)
        self.assertIn('SOLAR_RAD_AREA = 20', opm)
        self.assertIn('SOLAR_RAD_COEFF = 1', opm)
        self.assertIn('DRAG_AREA = 20', opm)
        self.assertIn('DRAG_COEFF = 2.2', opm)
        return True

    def _check_inputs(self, inputs):
        for data_dict in inputs['requests']:
            self._check_input(data_dict)
        return True

    def test_new_batch(self):
        rest = _RestProxyForTest()
        batches = Batches(rest)

        # A successful run.
        rest.expect_post("/batch", self._check_input, 200, {'calc_state': 'PENDING', 'uuid': '1'})

        state = batches.new_batch(self.dummy_propagation_params, self.dummy_opm_params)
        self.assertEqual('1', state.get_uuid())
        self.assertEqual('PENDING', state.get_calc_state())

        # Unsuccessful run.
        rest.expect_post("/batch", self._check_input, 400, {'calc_state': 'PENDING', 'uuid': '1'})
        with self.assertRaises(RuntimeError):
            batches.new_batch(self.dummy_propagation_params, self.dummy_opm_params)

    def test_new_batches(self):
        rest = _RestProxyForTest()
        batches = Batches(rest)

        # Successful run.
        rest.expect_post("/batches", self._check_inputs, 200, {'requests': [
            {'calc_state': 'PENDING', 'uuid': '1'},
            {'calc_state': 'RUNNING', 'uuid': '2'}
        ]})
        states = batches.new_batches([
            [self.dummy_propagation_params, self.dummy_opm_params],
            [self.dummy_propagation_params, self.dummy_opm_params]
        ])
        self.assertEqual(2, len(states))
        self.assertEqual('1', states[0].get_uuid())
        self.assertEqual('PENDING', states[0].get_calc_state())
        self.assertEqual('2', states[1].get_uuid())
        self.assertEqual('RUNNING', states[1].get_calc_state())

        # Unsuccessful run.
        rest.expect_post("/batches", self._check_inputs, 400, {})
        with self.assertRaises(RuntimeError):
            batches.new_batches([
                [self.dummy_propagation_params, self.dummy_opm_params],
                [self.dummy_propagation_params, self.dummy_opm_params]
            ])

    def test_delete_batch(self):
        rest = _RestProxyForTest()
        batches = Batches(rest)

        # Successful request.
        rest.expect_delete("/batch/aaa", 204)
        batches.delete_batch('aaa')

        # 200 isn't a valid return value for delete calls right now
        rest.expect_delete("/batch/aaa", 200)
        with self.assertRaises(RuntimeError):
            batches.delete_batch('aaa')

    def test_get_summary(self):
        rest = _RestProxyForTest()
        batches = Batches(rest)

        # Successful request.
        rest.expect_get('/batch/aaa', 200, {'uuid': 'aaa', 'calc_state': 'RUNNING'})
        summary = batches.get_summary('aaa')
        self.assertEqual('aaa', summary.get_uuid())
        self.assertEqual('RUNNING', summary.get_calc_state())

        # Successfully found missing.
        rest.expect_get('/batch/aaa', 404, 'Not JSON wat')
        self.assertIsNone(batches.get_summary('aaa'))

        # Unsuccessful request.
        rest.expect_get('/batch/aaa', 503, 'Also not JSON wat')
        with self.assertRaises(RuntimeError):
            batches.get_summary('aaa')

    def test_get_summaries(self):
        rest = _RestProxyForTest()
        batches = Batches(rest)

        # Successful request.
        rest.expect_get(
            '/batch?project_uuid=' + self.dummy_propagation_params.get_project_uuid(),
            200,
            {'items': [
                {'uuid': 'aaa', 'calc_state': 'RUNNING'},
                {'uuid': 'bbb', 'calc_state': 'COMPLETED'},
                {'uuid': 'ccc', 'calc_state': 'FAILED'}
            ]})
        summaries = batches.get_summaries(self.dummy_propagation_params.get_project_uuid())
        self.assertEqual(3, len(summaries))
        self.assertEqual('aaa', summaries['aaa'].get_uuid())
        self.assertEqual('RUNNING', summaries['aaa'].get_calc_state())
        self.assertEqual('bbb', summaries['bbb'].get_uuid())
        self.assertEqual('COMPLETED', summaries['bbb'].get_calc_state())
        self.assertEqual('ccc', summaries['ccc'].get_uuid())
        self.assertEqual('FAILED', summaries['ccc'].get_calc_state())

        # Unsuccessful request.
        rest.expect_get(
            '/batch?project_uuid=' + self.dummy_propagation_params.get_project_uuid(), 403, {})
        with self.assertRaises(RuntimeError):
            batches.get_summaries(self.dummy_propagation_params.get_project_uuid())

    def test_get_propagation_results(self):
        rest = _RestProxyForTest()
        batches = Batches(rest)

        # Parts count not specified. No result retrieval is attempted.
        state = StateSummary({
            'uuid': 'aaa',
            'calc_state': 'COMPLETED',
        })
        self.assertIsNone(batches.get_propagation_results(state))

        # Parts count is 0. No result retrieval is attempted.
        state = StateSummary({
            'uuid': 'aaa',
            'calc_state': 'COMPLETED',
            'parts_count': 0,
        })
        self.assertIsNone(batches.get_propagation_results(state))

        # Normal retrieval.
        state = StateSummary({
            'uuid': 'aaa',
            'calc_state': 'COMPLETED',
            'parts_count': 2,
        })
        rest.expect_get('/batch/aaa/1', 200, {'part_index': 'a', 'calc_state': 'RUNNING'})
        rest.expect_get('/batch/aaa/2', 200, {'part_index': 'z', 'calc_state': 'COMPLETED'})
        results = batches.get_propagation_results(state)
        self.assertEqual(2, len(results.get_parts()))
        self.assertEqual('a', results.get_parts()[0].get_part_index())
        self.assertEqual('z', results.get_parts()[1].get_part_index())

        # Some parts could not be found.
        state = StateSummary({
            'uuid': 'aaa',
            'calc_state': 'FAILED',
            'parts_count': 3,
        })
        rest.expect_get('/batch/aaa/1', 404, 'Not json')
        rest.expect_get('/batch/aaa/2', 200, {'part_index': 'z', 'calc_state': 'COMPLETED'})
        rest.expect_get('/batch/aaa/3', 404, 'Not json')
        results = batches.get_propagation_results(state)
        self.assertEqual(3, len(results.get_parts()))
        self.assertIsNone(results.get_parts()[0])
        self.assertEqual('z', results.get_parts()[1].get_part_index())
        self.assertIsNone(results.get_parts()[2])

        # Complete failure.
        state = StateSummary({
            'uuid': 'aaa',
            'calc_state': 'COMPLETED',
            'parts_count': 2,
        })
        rest.expect_get('/batch/aaa/1', 403, 'irrelevant')
        with self.assertRaises(RuntimeError):
            batches.get_propagation_results(state)


if __name__ == '__main__':
    unittest.main()
