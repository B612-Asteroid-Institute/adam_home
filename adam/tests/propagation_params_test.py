from adam import PropagationParams

import unittest


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
        self.assertEqual(PropagationParams.DEFAULT_CONFIG_ID,
                         p.get_propagator_uuid())

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

    def test_from_json(self):
        json = {
            'start_time': 'foo',
            'end_time': 'bar',
            'step_duration_sec': 5,
            'propagator_uuid': 'config',
        }
        propParams = PropagationParams.fromJsonResponse(json, 'description')
        self.assertEqual('description', propParams.get_description())
        self.assertEqual('foo', propParams.get_start_time())
        self.assertEqual('bar', propParams.get_end_time())
        self.assertEqual(5, propParams.get_step_size())
        self.assertEqual('config', propParams.get_propagator_uuid())


if __name__ == '__main__':
    unittest.main()
