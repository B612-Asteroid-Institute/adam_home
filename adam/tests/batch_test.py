from adam import Batch
from adam import PropagationParams
from adam import OpmParams
from adam.batch import StateSummary
from adam.batch import PropagationResults

import unittest


class BatchTest(unittest.TestCase):
    """Unit tests for Batch object

    """

    def test_get_methods(self):
        propagation_params = {'a': 1}
        opm_params = {'b': 2}
        batch = Batch(propagation_params, opm_params)
        self.assertEqual(propagation_params, batch.get_propagation_params())
        self.assertEqual(opm_params, batch.get_opm_params())
        self.assertIsNone(batch.get_uuid())
        self.assertIsNone(batch.get_calc_state())
        self.assertIsNone(batch.get_state_summary())
        self.assertIsNone(batch.get_results())

        state_summary = StateSummary({'uuid': 'aaa', 'calc_state': 'RUNNING'})
        batch.set_state_summary(state_summary)
        self.assertEqual(state_summary, batch.get_state_summary())
        self.assertEqual('aaa', batch.get_uuid())
        self.assertEqual('RUNNING', batch.get_calc_state())

        results = {'c': 3}
        batch.set_results(results)
        self.assertEqual(results, batch.get_results())


class PropagationParamsTest(unittest.TestCase):
    """Unit tests for PropagationParams object

    """

    def test_get_methods(self):
        p = PropagationParams({
            'start_time': 'foo',
            'end_time': 'bar',
            'step_size': 123,
            'project_uuid': 'aaa',
            'propagator_uuid': 'bbb',
            'description': 'abc'})
        self.assertEqual('foo', p.get_start_time())
        self.assertEqual('bar', p.get_end_time())
        self.assertEqual(123, p.get_step_size())
        self.assertEqual('aaa', p.get_project_uuid())
        self.assertEqual('bbb', p.get_propagator_uuid())
        self.assertEqual('abc', p.get_description())

    def test_defaults(self):
        p = PropagationParams({'start_time': 'foo', 'end_time': 'bar'})
        self.assertEqual(86400, p.get_step_size())
        self.assertEqual(PropagationParams.DEFAULT_CONFIG_ID, p.get_propagator_uuid())

        # No default.
        self.assertIsNone(p.get_project_uuid())
        self.assertIsNone(p.get_description())

    def test_required_keys(self):
        with self.assertRaises(KeyError):
            PropagationParams({'start_time': 'foo'})

        with self.assertRaises(KeyError):
            PropagationParams({'end_time': 'bar'})

    def test_invalid_keys(self):
        with self.assertRaises(KeyError):
            PropagationParams({'unrecognized': 0})


class OpmParamsTest(unittest.TestCase):
    """Unit tests for OpmParams object

    """

    def test_generate_opm(self):
        o = OpmParams({
            'epoch': 'foo',
            'state_vector': [1, 2, 3, 4, 5, 6],

            'originator': 'a',
            'object_name': 'b',
            'object_id': 'c',

            'mass': 1,
            'solar_rad_area': 2,
            'solar_rad_coeff': 3,
            'drag_area': 4,
            'drag_coeff': 5,

            'covariance': [0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11,
                           12, 13, 14, 15, 16, 17, 18, 19, 20],
            'perturbation': 7,
            'hypercube': 'CORNERS',
        })
        expected_opm = """CCSDS_OPM_VERS = 2.0
ORIGINATOR = a
COMMENT Cartesian coordinate system
OBJECT_NAME = b
OBJECT_ID = c
CENTER_NAME = SUN
REF_FRAME = ITRF-97
TIME_SYSTEM = UTC
EPOCH = foo
X = 1
Y = 2
Z = 3
X_DOT = 4
Y_DOT = 5
Z_DOT = 6
MASS = 1
SOLAR_RAD_AREA = 2
SOLAR_RAD_COEFF = 3
DRAG_AREA = 4
DRAG_COEFF = 5
CX_X = 0
CY_X = 1
CY_Y = 2
CZ_X = 3
CZ_Y = 4
CZ_Z = 5
CX_DOT_X = 6
CX_DOT_Y = 7
CX_DOT_Z = 8
CX_DOT_X_DOT = 9
CY_DOT_X = 10
CY_DOT_Y = 11
CY_DOT_Z = 12
CY_DOT_X_DOT = 13
CY_DOT_Y_DOT = 14
CZ_DOT_X = 15
CZ_DOT_Y = 16
CZ_DOT_Z = 17
CZ_DOT_X_DOT = 18
CZ_DOT_Y_DOT = 19
CZ_DOT_Z_DOT = 20
USER_DEFINED_ADAM_INITIAL_PERTURBATION = 7 [sigma]
USER_DEFINED_ADAM_HYPERCUBE = CORNERS"""
        # Remove the CREATION_DATE stamp since that varies.
        opm = "\n".join([line for line in o.generate_opm().splitlines()
                         if not line.startswith('CREATION_DATE')])
        self.maxDiff = None  # Otherwise if the next line fails, we can't see the diff
        self.assertEqual(expected_opm, opm)

    def test_generate_opm_with_defaults(self):
        o = OpmParams({'epoch': 'foo', 'state_vector': [1, 2, 3, 4, 5, 6]})
        expected_opm = """CCSDS_OPM_VERS = 2.0
ORIGINATOR = ADAM_User
COMMENT Cartesian coordinate system
OBJECT_NAME = dummy
OBJECT_ID = 001
CENTER_NAME = SUN
REF_FRAME = ITRF-97
TIME_SYSTEM = UTC
EPOCH = foo
X = 1
Y = 2
Z = 3
X_DOT = 4
Y_DOT = 5
Z_DOT = 6
MASS = 1000
SOLAR_RAD_AREA = 20
SOLAR_RAD_COEFF = 1
DRAG_AREA = 20
DRAG_COEFF = 2.2"""
        # Remove the CREATION_DATE stamp since that varies.
        opm = "\n".join([line for line in o.generate_opm().splitlines()
                         if not line.startswith('CREATION_DATE')])
        self.maxDiff = None  # Otherwise if the next line fails, we can't see the diff
        self.assertEqual(expected_opm, opm)

    def test_access_state_vector(self):
        o = OpmParams({'epoch': 'foo', 'state_vector': [1, 2, 3, 4, 5, 6]})
        self.assertEqual([1, 2, 3, 4, 5, 6], o.get_state_vector())
        o.set_state_vector([6, 5, 4, 3, 2, 1])
        self.assertEqual([6, 5, 4, 3, 2, 1], o.get_state_vector())

    def test_required_keys(self):
        with self.assertRaises(KeyError):
            OpmParams({'epoch': 'foo'})

        with self.assertRaises(KeyError):
            OpmParams({'state_vector': []})

    def test_invalid_keys(self):
        with self.assertRaises(KeyError):
            OpmParams({'unrecognized': 0})


class StateSummaryTest(unittest.TestCase):
    """Unit tests for StateSummary object

    """

    def test_get_methods(self):
        s = StateSummary({
            'uuid': 'a',
            'calc_state': 'b',
            'step_duration_sec': 1,
            'create_time': 'c',
            'execute_time': 'd',
            'complete_time': 'e',
            'project': 'f',
            'parts_count': 2,
        })
        self.assertEqual('a', s.get_uuid())
        self.assertEqual('b', s.get_calc_state())
        self.assertEqual(1, s.get_step_size())
        self.assertEqual('c', s.get_create_time())
        self.assertEqual('d', s.get_execute_time())
        self.assertEqual('e', s.get_complete_time())
        self.assertEqual('f', s.get_project_uuid())
        self.assertEqual(2, s.get_parts_count())

    def test_required_keys(self):
        with self.assertRaises(KeyError):
            StateSummary({'uuid': 'a'})

        with self.assertRaises(KeyError):
            StateSummary({'calc_state': 'b'})


class PropagationResultsTest(unittest.TestCase):
    """Unit tests for PropagationResults object

    """

    def test_get_methods(self):
        # All keys.
        pr = PropagationResults([{
            'part_index': 'a',
            'calc_state': 'b',
            'stk_ephemeris': 'c',
            'error': 'd'
        }])
        self.assertEqual(1, len(pr.get_parts()))
        p = pr.get_parts()[0]
        self.assertEqual('a', p.get_part_index())
        self.assertEqual('b', p.get_calc_state())
        self.assertEqual('c', p.get_ephemeris())
        self.assertEqual('d', p.get_error())

        # Only required keys.
        pr = PropagationResults([{
            'part_index': 'a',
            'calc_state': 'b',
        }])
        self.assertEqual(1, len(pr.get_parts()))
        p = pr.get_parts()[0]
        self.assertEqual('a', p.get_part_index())
        self.assertEqual('b', p.get_calc_state())
        self.assertIsNone(p.get_ephemeris())
        self.assertIsNone(p.get_error())

    def test_required_keys(self):
        with self.assertRaises(KeyError):
            PropagationResults([{
                'part_index': 'a'
            }])

        with self.assertRaises(KeyError):
            PropagationResults([{
                'calc_state': 'b'
            }])

    def test_no_parts(self):
        with self.assertRaises(RuntimeError):
            PropagationResults([])

    def test_empty_parts(self):
        parts = [None, {'part_index': 'a', 'calc_state': 'b'}, None]
        results = PropagationResults(parts)
        self.assertEqual(3, len(results.get_parts()))
        self.assertIsNone(results.get_parts()[0])
        self.assertIsNotNone(results.get_parts()[1])
        self.assertIsNone(results.get_parts()[2])

    def test_get_final_state_vector(self):
        pr = PropagationResults([None])
        self.assertIsNone(pr.get_end_state_vector())

        pr = PropagationResults([{
            'part_index': 'a',
            'calc_state': 'RUNNING'
        }])
        self.assertIsNone(pr.get_end_state_vector())

        pr = PropagationResults([None, {
            'part_index': 'a',
            'calc_state': 'RUNNING',
            'stk_ephemeris': 'c'
        }, {
            'part_index': 'b',
            'calc_state': 'COMPLETED',
            'stk_ephemeris': """
some junk here
1 2 3 4 5 6 7
7 6 5 4 3 2 1
            """
        }])
        self.assertEqual([0.006, 0.005, 0.004, 0.003, 0.002, 0.001],
                         pr.get_end_state_vector())


if __name__ == '__main__':
    unittest.main()
