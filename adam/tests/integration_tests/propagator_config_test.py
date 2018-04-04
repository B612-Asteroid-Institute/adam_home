from adam import Service
from adam import ConfigManager
from adam import PropagatorConfigs

import unittest

import os


class PropagatorConfigTest(unittest.TestCase):
    """Test of propagator config manipulation.

    """

    def setUp(self):
        config = ConfigManager(os.getcwd() + '/test_config.json').get_config()
        self.service = Service(config)
        self.assertTrue(self.service.setup())

    def tearDown(self):
        self.service.teardown()
    
    def test_get_public_configs(self):
        # Config management isn't very common, doesn't merit direct addition to service.
        configs = PropagatorConfigs(self.service.rest)

        public_config_1 = configs.get_config(PropagatorConfigs.PUBLIC_CONFIG_ALL_PLANETS_AND_MOON)
        self.assertEqual("00000000-0000-0000-0000-000000000001", public_config_1.get_uuid())

        public_config_2 = configs.get_config(PropagatorConfigs.PUBLIC_CONFIG_SUN_ONLY)
        self.assertEqual("00000000-0000-0000-0000-000000000002", public_config_2.get_uuid())

        public_config_3 = configs.get_config(PropagatorConfigs.PUBLIC_CONFIG_ALL_PLANETS_AND_MOON_AND_ASTEROIDS)
        self.assertEqual("00000000-0000-0000-0000-000000000003", public_config_3.get_uuid())

    def test_config_management(self):
        # Config management isn't very common, doesn't merit direct addition to service.
        configs = PropagatorConfigs(self.service.rest)

        project = self.service.new_working_project()
        self.assertIsNotNone(project)

        config = configs.new_config({'project': project.get_uuid(), 'description': 'test config'})
        self.assertEqual(project.get_uuid(), config.get_project())

        my_configs = configs.get_configs()
        self.assertIn(config.get_uuid(), [c.get_uuid() for c in my_configs])

        config_again = configs.get_config(config.get_uuid())
        self.assertEqual(config.get_config_json(), config_again.get_config_json())

        configs.delete_config(config.get_uuid())

        my_configs = configs.get_configs()
        self.assertNotIn(config.get_uuid(), [c.get_uuid() for c in my_configs])


if __name__ == '__main__':
    unittest.main()
