import unittest

from adam import PropagatorConfigs
from adam.propagator_config import PropagatorConfig
from adam.rest_proxy import _RestProxyForTest

FULL_CONFIG_JSON_INPUT = {
    "project": "00000000-0000-0000-0000-000000000001",
    "description": "everything",
    "sun": "POINT_MASS",
    "mercury": "POINT_MASS",
    "venus": "POINT_MASS",
    "earth": "POINT_MASS",
    "mars": "POINT_MASS",
    "jupiter": "POINT_MASS",
    "saturn": "POINT_MASS",
    "uranus": "POINT_MASS",
    "neptune": "POINT_MASS",
    "pluto": "POINT_MASS",
    "moon": "POINT_MASS",
    "asteroids": [
        "Ceres",
        "Pallas",
        "Juno",
        "Vesta",
        "Hebe",
        "Iris",
        "Hygeia",
        "Eunomia",
        "Psyche",
        "Amphitrite",
        "Europa",
        "Cybele",
        "Sylvia",
        "Thisbe",
        "Davida",
        "Interamnia"
    ],
}

# This will have all members of FULL_CONFIG_JSON_INPUT plus a couple that the server adds.
FULL_CONFIG_JSON_OUTPUT = dict({
    "uuid": "00000000-0000-0000-0000-000000000003",
    "asteroidsString": "Ceres,Pallas,Juno,Vesta,Hebe,Iris,Hygeia,Eunomia,Psyche,Amphitrite," +
                       "Europa,Cybele,Sylvia,Thisbe,Davida,Interamnia"
}, **FULL_CONFIG_JSON_INPUT)


class PropagatorConfigTest(unittest.TestCase):
    """Unit tests for PropagatorConfig object

    """

    def test_get_methods(self):
        # Minimal config.
        config = PropagatorConfig({
            "uuid": "a",
            "project": "b"
        })
        self.assertEqual("a", config.get_uuid())
        self.assertEqual("b", config.get_project())
        self.assertEqual(None, config.get_description())

        # Full config.
        config = PropagatorConfig(FULL_CONFIG_JSON_OUTPUT)
        self.assertEqual("00000000-0000-0000-0000-000000000003", config.get_uuid())
        self.assertEqual("00000000-0000-0000-0000-000000000001", config.get_project())
        self.assertEqual("everything", config.get_description())
        self.assertEqual(FULL_CONFIG_JSON_OUTPUT, config.get_config_json())

        # Too much config.
        with self.assertRaises(KeyError):
            config = PropagatorConfig({'this is not a field': 'wat'})


class PropagatorConfigsTest(unittest.TestCase):
    """Unit tests for PropagatorConfigs module

    """

    def test_new_config(self):
        rest = _RestProxyForTest()
        configs = PropagatorConfigs(rest)

        expected_data = {}

        def check_input(data_dict):
            self.assertEqual(expected_data, data_dict)
            return True

        expected_data = {'project': 'project'}
        rest.expect_post(PropagatorConfigs.REST_ENDPOINT_PREFIX, check_input, 200,
                         {'uuid': 'uuid', 'project': 'project'})
        config = configs.new_config({'project': 'project'})
        self.assertEqual("uuid", config.get_uuid())
        self.assertEqual("project", config.get_project())
        self.assertEqual(None, config.get_description())

        expected_data = FULL_CONFIG_JSON_INPUT
        rest.expect_post(PropagatorConfigs.REST_ENDPOINT_PREFIX, check_input, 200,
                         FULL_CONFIG_JSON_OUTPUT)
        config = configs.new_config(FULL_CONFIG_JSON_INPUT)
        self.assertEqual(FULL_CONFIG_JSON_OUTPUT, config.get_config_json())

        with self.assertRaises(KeyError):
            configs.new_config({'unrecognized': 'foo'})

        with self.assertRaises(KeyError):
            configs.new_config({'sun': 'not an option'})

    def test_get_config(self):
        rest = _RestProxyForTest()
        configs = PropagatorConfigs(rest)

        rest.expect_get(f"{PropagatorConfigs.REST_ENDPOINT_PREFIX}/aaa", 200,
                        {'uuid': 'aaa', 'project': 'bbb'})
        config = configs.get_config('aaa')
        self.assertEqual('aaa', config.get_uuid())
        self.assertEqual('bbb', config.get_project())

        # the public config exists
        rest.expect_get(
            f"{PropagatorConfigs.REST_ENDPOINT_PREFIX}/00000000-0000-0000-0000-000000000003",
            200, FULL_CONFIG_JSON_OUTPUT)
        config = configs.get_config("00000000-0000-0000-0000-000000000003")
        self.assertEqual(FULL_CONFIG_JSON_OUTPUT, config.get_config_json())

        # propagator config with id "aaa" does not exist
        rest.expect_get(f"{PropagatorConfigs.REST_ENDPOINT_PREFIX}/aaa", 404, {})
        config = configs.get_config('aaa')
        self.assertIsNone(config)

        rest.expect_get(f"{PropagatorConfigs.REST_ENDPOINT_PREFIX}/aaa", 403, {})
        with self.assertRaises(RuntimeError):
            config = configs.get_config('aaa')

    def test_get_configs(self):
        rest = _RestProxyForTest()
        configs_module = PropagatorConfigs(rest)

        rest.expect_get(PropagatorConfigs.REST_ENDPOINT_PREFIX, 200, {'items': []})
        configs = configs_module.get_configs()
        self.assertEqual(0, len(configs))

        rest.expect_get(PropagatorConfigs.REST_ENDPOINT_PREFIX, 200, {'items': [
            {'uuid': 'aaa', 'project': 'bbb'},
            {'uuid': 'ccc', 'project': 'ddd'}
        ]})
        configs = configs_module.get_configs()
        self.assertEqual(2, len(configs))
        self.assertEqual('aaa', configs[0].get_uuid())
        self.assertEqual('bbb', configs[0].get_project())
        self.assertEqual('ccc', configs[1].get_uuid())
        self.assertEqual('ddd', configs[1].get_project())

    def test_delete_config(self):
        rest = _RestProxyForTest()
        configs = PropagatorConfigs(rest)

        rest.expect_delete(f"{PropagatorConfigs.REST_ENDPOINT_PREFIX}/aaa", 204)
        configs.delete_config('aaa')

        # 200 isn't a valid return value for delete calls right now
        rest.expect_delete(f"{PropagatorConfigs.REST_ENDPOINT_PREFIX}/aaa", 200)
        with self.assertRaises(RuntimeError):
            configs.delete_config('aaa')

        rest.expect_delete(f"{PropagatorConfigs.REST_ENDPOINT_PREFIX}/aaa", 404)
        with self.assertRaises(RuntimeError):
            configs.delete_config('aaa')


if __name__ == '__main__':
    unittest.main()
