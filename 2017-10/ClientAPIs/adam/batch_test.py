from adam import Batch
from adam.batch import _set_url_base
from adam.rest_proxy import _RestProxyForTest
import unittest

class BatchTest(unittest.TestCase):

    def setUp(self):
        self._base = "http://BASE"
        _set_url_base(self._base)

    def test_good_submit(self):
        rest = _RestProxyForTest()
        def check_input(data_dict):
            self.assertEqual(data_dict['start_time'], 'AAA')
            self.assertEqual(data_dict['end_time'], 'BBB')
            opm = data_dict['opm_string']
            self.assertIsNotNone(opm)
            self.assertIn('EPOCH = CCC', opm)
            self.assertIn('X = 1', opm)
            self.assertIn('Y = 2', opm)
            self.assertIn('Z = 3', opm)
            self.assertIn('X_DOT = 4', opm)
            self.assertIn('Y_DOT = 5', opm)
            self.assertIn('Z_DOT = 6', opm)
            return True
        rest.expect_post(self._base + "/batch", check_input, 200, {'calc_state' : 'PENDING', 'uuid' : 'BLAH'})

        batch = Batch()
        batch.set_start_time("AAA")
        batch.set_end_time("BBB")
        batch.set_state_vector('CCC', [1, 2, 3, 4, 5, 6])
        batch.set_rest_accessor(rest)
        batch.submit()

        self.assertEqual(batch.get_calc_state(), 'PENDING')
        self.assertEqual(batch.get_uuid(), 'BLAH')

    def test_server_fails(self):
        rest = _RestProxyForTest()
        rest.expect_post(self._base + '/batch', lambda x : True, 404, {})
        batch = Batch()
        batch.set_start_time("AAA")
        batch.set_end_time("BBB")
        batch.set_state_vector('CCC', [1, 2, 3, 4, 5, 6])
        batch.set_rest_accessor(rest)
        with self.assertRaises(RuntimeError):
            batch.submit()

    def _verify_params(self, field):
        rest = _RestProxyForTest()
        batch = Batch()
        batch.set_start_time("AAA")
        batch.set_end_time("BBB")
        batch.set_state_vector('CCC', [1, 2, 3, 4, 5, 6])
        batch.set_rest_accessor(rest)
        setattr(batch, field, None)
        with self.assertRaises(KeyError):
            batch.submit()

    def test_params(self):
        for f in ['_start_time', '_end_time', '_epoch', '_state_vector']:
            self._verify_params(f)

    def test_is_ready_not_found(self):
        uuid = 'BLAH'
        rest = _RestProxyForTest()
        rest.expect_get(self._base + '/batch/' + uuid, 404, {})
        batch = Batch()
        batch._uuid = uuid
        batch.set_rest_accessor(rest)
        self.assertFalse(batch.is_ready())

    def test_is_ready_fails(self):
        uuid = 'BLAH'
        rest = _RestProxyForTest()
        rest.expect_get(self._base + '/batch/' + uuid, 500, {})
        batch = Batch()
        batch._uuid = uuid
        batch.set_rest_accessor(rest)
        with self.assertRaises(RuntimeError):
            batch.is_ready()

    def test_is_ready_fails(self):
        rest = _RestProxyForTest()
        batch = Batch()
        batch.set_rest_accessor(rest)
        with self.assertRaises(KeyError):
            batch.is_ready()

    def test_is_not_ready(self):
        uuid = 'BLAH'
        rest = _RestProxyForTest()
        rest.expect_get(self._base + '/batch/' + uuid, 200, {'calc_state' : 'RUNNING', 'parts_count': 5})
        batch = Batch()
        batch._uuid = uuid
        batch.set_rest_accessor(rest)
        self.assertFalse(batch.is_ready())
        self.assertEqual(batch.get_parts_count(), 5)

    def test_is_ready_completed(self):
        uuid = 'BLAH'
        rest = _RestProxyForTest()
        rest.expect_get(self._base + '/batch/' + uuid, 200,
                        {'calc_state': 'COMPLETED', 'parts_count': 42, 'summary': "ZQZ",
                         'error': 'No error!'})
        batch = Batch()
        batch._uuid = uuid
        batch.set_rest_accessor(rest)
        self.assertTrue(batch.is_ready())
        # TODO other fields

    def test_is_ready_failed(self):
        uuid = 'BLAH'
        rest = _RestProxyForTest()
        rest.expect_get(self._base + '/batch/' + uuid, 200,
                        {'calc_state': 'FAILED', 'parts_count': 42, 'summary': "ZQZ",
                         'error': 'No error!'})
        batch = Batch()
        batch._uuid = uuid
        batch.set_rest_accessor(rest)
        self.assertTrue(batch.is_ready())
        # TODO other fields

    def test_get_ephemeris_failed(self):
        uuid = 'BLAH'
        part = 3
        rest = _RestProxyForTest()
        rest.expect_get(self._base + '/batch/' + uuid + '/' + str(part), 200,
                        {'calc_state': 'FAILED','error': 'No error!', 'part_index': part})
        batch = Batch()
        batch._uuid = uuid
        batch._parts_count = 10
        batch._calc_state = 'FAILED'
        batch.set_rest_accessor(rest)
        with self.assertRaises(KeyError):
            batch.get_part_ephemeris(part)

    def test_get_ephemeris(self):
        uuid = 'BLAH'
        part = 3
        rest = _RestProxyForTest()
        rest.expect_get(self._base + '/batch/' + uuid + '/' + str(part), 200,
                            {'calc_state': 'COMPLETED', 'error': 'No error!', 'stk_ephemeris': 'something',
                             'part_index': part})
        batch = Batch()
        batch._uuid = uuid
        batch._parts_count = 10
        batch._calc_state = 'COMPLETED'
        batch.set_rest_accessor(rest)
        self.assertEqual(batch.get_part_ephemeris(part), 'something')
        self.assertEqual(batch.get_part_error(part), 'No error!')
        self.assertEqual(batch.get_part_state(part), 'COMPLETED')

    # Need to check if individual parts are ready
    # Need to check if part is within range
    # Need to check different errors: 200, 404, 500

if __name__ == '__main__':
    unittest.main()
