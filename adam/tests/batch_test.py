from adam import Batch
from adam import PropagationParams
from adam import OpmParams
from adam.batch import StateSummary
from adam.batch import PropagationResults

from datetime import datetime
import numpy.testing as npt
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

    def test_get_state_at_time(self):
        pr = PropagationResults([None])
        self.assertIsNone(pr.get_state_vector_at_time(datetime.now()))

        pr = PropagationResults([{
            'part_index': 'a',
            'calc_state': 'RUNNING'
        }])
        self.assertIsNone(pr.get_state_vector_at_time(datetime.now()))

        pr = PropagationResults([None, {
            'part_index': 'a',
            'calc_state': 'COMPLETED',
            'stk_ephemeris': """
some junk here not a file epoch
1 2 3 4 5 6 7
7 6 5 4 3 2 1
            """
        }])
        self.assertIsNone(pr.get_state_vector_at_time(datetime.now()))

        pr = PropagationResults([None, {
            'part_index': 'b',
            'calc_state': 'COMPLETED',
            'stk_ephemeris': """
stk.v.9.0

# WrittenBy    STK_Components_2017 r4(17.4.392.0)

BEGIN Ephemeris

NumberOfEphemerisPoints	18252
ScenarioEpoch	21 Jul 2009 13:42:34.615999999999985
InterpolationMethod	Hermite
InterpolationSamplesM1	2
CentralBody	Sun
CoordinateSystem	ICRF

EphemerisTimePosVel

0 73136102939.90326 -133490160572.72543 8406324.905534467 28220.13126652218 22868.590558009368 -0.19231683186022774
-86400 70687762770.92772 -135447234231.29443 8421107.139721738 28452.654845207973 22433.79996994943 -0.1499638154415067
-172800 68219786459.42084 -137366684784.5862 8432255.918466914 28674.683201744967 21997.744385379105 -0.10821028857188271
-259200 65733077574.2293 -139248418103.58472 8439823.350024007 28886.293259423644 21560.77327825493 -0.06706343692839449
-345600 63228532421.91671 -141092369828.8071 8443862.153904703 29087.576060079045 21123.22618751113 -0.026530247821391004
-432000 60707038864.30396 -142898504487.95035 8444425.64979409 29278.635896145453 20685.43217483686 0.013382350455396062
-518400 58169475211.58147 -144666814569.93005 8441567.758123463 29459.589430332002 20247.709357212265 0.052667360276471335
-604800 55616709191.788055 -146397319561.69974 8435343.01074691 29630.564809218675 19810.364512470725 0.09131761180289957
-691200 53049596996.92381 -148090064954.06686 8425806.568807617 29791.700776677662 19373.692755679345 0.12932570231264304
-777600 50468982405.472176 -149745121222.51495 8413014.243413422 29943.145792593295 18937.977283700522 0.16668399446203316
            """  # NOQA
        }])
        # Wrong time, no match.
        self.assertEqual(None,
                         pr.get_state_vector_at_time(datetime.strptime("21 Jul 2009 13:42:35.616",
                                                                       "%d %b %Y %H:%M:%S.%f")))

        # Middle point.
        npt.assert_almost_equal(
            [70687762.77092772, -135447234.23129443, 8421.107139721738,
             28.452654845207973, 22.43379996994943, -0.0001499638154415067],
            pr.get_state_vector_at_time(datetime.strptime("20 Jul 2009 13:42:34.616",
                                                          "%d %b %Y %H:%M:%S.%f")))

        # Check last point.
        npt.assert_almost_equal(
            [50468982.405472176, -149745121.22251495, 8413.014243413422,
             29.943145792593295, 18.937977283700522, 0.00016668399446203316],
            pr.get_state_vector_at_time(datetime.strptime("12 Jul 2009 13:42:34.616",
                                                          "%d %b %Y %H:%M:%S.%f")))

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
