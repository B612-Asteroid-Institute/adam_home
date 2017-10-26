from adam import Batch
from adam.batch import _set_url_base
from adam.rest_proxy import _RestProxyForTest
import unittest

class BatchTest(unittest.TestCase):
    """Unit tests for running batch job

    TODO:
        - Check if individual parts are ready
        - Check if part is within range
        - Check different errors: 200, 404, 500
    """

    def setUp(self):
        """"Set up base URL

        This function sets up the base URL to a dummy URL.

        """
        self._base = "http://BASE"
        _set_url_base(self._base)

    def test_good_submit(self):
        """Test a good/passing batch submit

        This function tests a good batch submit run.

        """

        # Use REST proxy for testing
        rest = _RestProxyForTest()

        def check_input(data_dict):
            """Check input data

            Checks input data by asserting the following:
                - start time = 'AAA'
                - end time = 'BBB'
                - opm string in data dictionary is not None
                - epoch and state vector are 'CCC' and [1, 2, 3, 4, 5, 6], respectively

            Args:
                data_dict (dict) - input data for POST

            Returns:
                True
            """
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

        # Set expected 'POST' request (good)
        rest.expect_post(self._base + "/batch", check_input, 200, {'calc_state' : 'PENDING', 'uuid' : 'BLAH'})

        # Initiate Batch class
        batch = Batch()

        # Set start time, end time, and state vector with epoch
        batch.set_start_time("AAA")
        batch.set_end_time("BBB")
        batch.set_state_vector('CCC', [1, 2, 3, 4, 5, 6])

        # Override network access with proxy
        batch.set_rest_accessor(rest)

        # Submit job
        batch.submit()

        # Assert that the calc state is 'PENDING' and the UUID is 'BLAH'
        self.assertEqual(batch.get_calc_state(), 'PENDING')
        self.assertEqual(batch.get_uuid(), 'BLAH')

    def test_server_fails(self):
        """Test a failing server

        This function tests a failed submit on the server side (i.e. code returned is not 200).

        """

        # Use REST proxy for testing
        rest = _RestProxyForTest()

        # Set expected 'POST' request with 404 error
        rest.expect_post(self._base + '/batch', lambda x : True, 404, {})

        # Initiate Batch class
        batch = Batch()

        # Set start time, end time, and state vector with epoch
        batch.set_start_time("AAA")
        batch.set_end_time("BBB")
        batch.set_state_vector('CCC', [1, 2, 3, 4, 5, 6])

        # Override network access with proxy
        batch.set_rest_accessor(rest)

        # Assert that the error code raises a RuntimeError with batch submission
        with self.assertRaises(RuntimeError):
            batch.submit()

    def _verify_params(self, field):
        """(Private) Verify parameters (fields) raise KeyErrors if not found

        This function tests that a given field set to None will raise a KeyError.

        Args:
            field (str) - attribute to set to None
        """

        # Use REST proxy for testing
        rest = _RestProxyForTest()

        # Initiate Batch class
        batch = Batch()

        # Set start time, end time, and state vector with epoch
        batch.set_start_time("AAA")
        batch.set_end_time("BBB")
        batch.set_state_vector('CCC', [1, 2, 3, 4, 5, 6])

        # Override network access with proxy
        batch.set_rest_accessor(rest)

        # Set batch attribute (field) to None
        setattr(batch, field, None)

        # Assert that a missing field will return a KeyError with batch submission
        with self.assertRaises(KeyError):
            batch.submit()

    def test_params(self):
        """Test parameters for raising KeyErrors

        This function will test all possible batch attributes to ensure any missing one will raise a KeyError.

        """

        # Loop through all batch attributes and verify each raises a KeyError
        for f in ['_start_time', '_end_time', '_epoch', '_state_vector']:
            self._verify_params(f)

    def test_is_ready_not_found(self):
        """Test that a job is not ready if not found

        This function tests that if a job is not found from a UUID, it will not return as 'ready'.

        """

        # Dummy UUID for testing
        uuid = 'BLAH'

        # Use REST proxy for testing
        rest = _RestProxyForTest()

        # Set expected 'GET' request with 404 error
        rest.expect_get(self._base + '/batch/' + uuid, 404, {})

        # Initiate Batch class
        batch = Batch()

        # Set UUID
        batch._uuid = uuid

        # Override network access with proxy
        batch.set_rest_accessor(rest)

        # Assert that the job does not show as ready
        self.assertFalse(batch.is_ready())

    def test_is_ready_fails_error_code(self):
        """Test that a failed job returns a RuntimeError when retrieved

        This function tests that a failed error code will return a RuntimeError when attempting to check if it is ready.

        """

        # Dummy UUID for testing
        uuid = 'BLAH'

        # Use REST proxy for testing
        rest = _RestProxyForTest()

        # Set expected 'GET' request with 500 error (fail)
        rest.expect_get(self._base + '/batch/' + uuid, 500, {})

        # Initiate Batch class
        batch = Batch()

        # Set UUID
        batch._uuid = uuid

        # Override network access with proxy
        batch.set_rest_accessor(rest)

        # Assert that a RuntimeError is raised when checking if it is ready
        with self.assertRaises(RuntimeError):
            batch.is_ready()

    def test_is_ready_fails_no_uuid(self):
        """Test that no specified UUID will raise a KeyError when retrieved

        This function tests that checking if a job is ready without specifying the UUID will result in a KeyError.

        """

        # Use REST proxy for testing
        rest = _RestProxyForTest()

        # Initiate Batch class
        batch = Batch()

        # Override network access with proxy
        batch.set_rest_accessor(rest)

        # Assert that a KeyError is raised when checking if it is ready
        with self.assertRaises(KeyError):
            batch.is_ready()

    def test_is_not_ready(self):
        """Test when a job is not ready

        This function tests that a job will correctly indicate when it is not ready and returns the expected number of
        ephemeris parts count.

        """

        # Dummy UUID for testing
        uuid = 'BLAH'

        # Use REST proxy for testing
        rest = _RestProxyForTest()

        # Set expected 'GET' request with calc_state as 'RUNNING'
        rest.expect_get(self._base + '/batch/' + uuid, 200, {'calc_state' : 'RUNNING', 'parts_count': 5})

        # Initiate Batch class
        batch = Batch()

        # Set UUID
        batch._uuid = uuid

        # Override network access with proxy
        batch.set_rest_accessor(rest)

        # Assert that checking if the batch is ready will return False
        self.assertFalse(batch.is_ready())

        # Assert that the number of expected parts is returned
        self.assertEqual(batch.get_parts_count(), 5)

    def test_is_ready_completed(self):
        """Test that job is ready when completed

        This function tests that a job will indicate that it is ready if it has completed.

        TODO:
            Other fields
        """

        # Dummy UUID for testing
        uuid = 'BLAH'

        # Use REST proxy for testing
        rest = _RestProxyForTest()

        # Set expected 'GET' request with calc_state as 'COMPLETED'
        rest.expect_get(self._base + '/batch/' + uuid, 200,
                        {'calc_state': 'COMPLETED', 'parts_count': 42, 'summary': "ZQZ",
                         'error': 'No error!'})

        # Initiate Batch class
        batch = Batch()

        # Set UUID
        batch._uuid = uuid

        # Override network access with proxy
        batch.set_rest_accessor(rest)

        # Assert that checking if the batch is ready will return True
        self.assertTrue(batch.is_ready())

    def test_is_ready_failed(self):
        """Test that job is ready when failed

        This function tests that a job will indicate that it is ready if it has failed.

        TODO:
            Other fields
        """

        # Dummy UUID for testing
        uuid = 'BLAH'

        # Use REST proxy for testing
        rest = _RestProxyForTest()

        # Set expected 'GET' request with calc_state as 'FAILED'
        rest.expect_get(self._base + '/batch/' + uuid, 200,
                        {'calc_state': 'FAILED', 'parts_count': 42, 'summary': "ZQZ",
                         'error': 'No error!'})

        # Initiate Batch class
        batch = Batch()

        # Set UUID
        batch._uuid = uuid

        # Override network access with proxy
        batch.set_rest_accessor(rest)

        # Assert that checking if the batch is ready will return True
        self.assertTrue(batch.is_ready())

    def test_get_ephemeris_failed(self):
        """Test that a failed run will raise a KeyError if retrieving ephemeris

        This function tests that attempting to get the ephemeris will return a KeyError if the batch job has failed.

        """

        # Dummy UUID and part number for testing
        uuid = 'BLAH'
        part = 3

        # Use REST proxy for testing
        rest = _RestProxyForTest()

        # Set expected 'GET' request with calc_state as 'FAILED' for specific part
        rest.expect_get(self._base + '/batch/' + uuid + '/' + str(part), 200,
                        {'calc_state': 'FAILED','error': 'No error!', 'part_index': part})

        # Initiate Batch class
        batch = Batch()

        # Set UUID, parts count, and overall calc state (as 'FAILED')
        batch._uuid = uuid
        batch._parts_count = 10
        batch._calc_state = 'FAILED'

        # Override network access with proxy
        batch.set_rest_accessor(rest)

        # Assert that an overall calc state as 'FAILED' will return a KeyError
        with self.assertRaises(KeyError):
            batch.get_part_ephemeris(part)

    def test_get_ephemeris(self):
        """Test that an ephemeris is returned if the job has completed successfully

        This function tests that a job that is completed successfully will return the expected ephemeris.

        """

        # Dummy UUID and part number for testing
        uuid = 'BLAH'
        part = 3

        # Use REST proxy for testing
        rest = _RestProxyForTest()

        # Set expected 'GET' request with calc_state as 'COMPLETED' for specific part
        rest.expect_get(self._base + '/batch/' + uuid + '/' + str(part), 200,
                            {'calc_state': 'COMPLETED', 'error': 'No error!', 'stk_ephemeris': 'something',
                             'part_index': part})

        # Initiate Batch class
        batch = Batch()

        # Set UUID, parts count, and overall calc state (as 'COMPLETED')
        batch._uuid = uuid
        batch._parts_count = 10
        batch._calc_state = 'COMPLETED'

        # Override network access with proxy
        batch.set_rest_accessor(rest)

        # Assert that an overall calc state as 'COMPLETED' will return the expected ephemeris
        self.assertEqual(batch.get_part_ephemeris(part), 'something')

        # Assert that the error is as expected
        self.assertEqual(batch.get_part_error(part), 'No error!')

        # Assert that the calc state for the specific part's run is as expected
        self.assertEqual(batch.get_part_state(part), 'COMPLETED')


if __name__ == '__main__':
    unittest.main()
