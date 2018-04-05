from adam import Service

from adam import Batch
from adam import BatchRunManager
from adam import ConfigManager
from adam import OpmParams
from adam import PropagationParams
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

        public_config_3 = configs.get_config(
            PropagatorConfigs.PUBLIC_CONFIG_ALL_PLANETS_AND_MOON_AND_ASTEROIDS)
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

    def test_config_in_use_pins_project(self):
        # Config management isn't very common, doesn't merit direct addition to service.
        configs = PropagatorConfigs(self.service.rest)
        projects = self.service.get_projects_module()

        project = self.service.new_working_project()
        project1 = projects.new_project(project.get_uuid(), "", "")
        self.assertIsNotNone(project1)
        project2 = projects.new_project(project.get_uuid(), "", "")
        self.assertIsNotNone(project2)
        print("Added child projects to working project: " +
              "[" + project1.get_uuid() + ", " + project2.get_uuid() + "]")

        config = configs.new_config({'project': project1.get_uuid(), 'description': 'test config'})
        self.assertEqual(project1.get_uuid(), config.get_project())

        batch = Batch(PropagationParams({
            'start_time': '2017-10-04T00:00:00Z',
            'end_time': '2017-10-05T00:00:00Z',
            'project_uuid': project2.get_uuid(),
            'propagator_uuid': config.get_uuid()
        }), OpmParams({
            'epoch': '2017-10-04T00:00:00Z',
            'state_vector': [130347560.13690618, -74407287.6018632, -35247598.541470632,
                             23.935241263310683, 27.146279819258538, 10.346605942591514]
        }))
        BatchRunManager(self.service.get_batches_module(), [batch]).run()

        # Attempt to delete the project with the config in it. It should refuse because the
        # config is still in use by the batch.
        with self.assertRaises(RuntimeError):
            projects.delete_project(project1.get_uuid())

        # Then delete the batch. After that, the project with the config in it should
        # delete no problem.
        self.service.batches.delete_batch(batch.get_uuid())
        projects.delete_project(project1.get_uuid())

        # Clean up the batch holder project.
        projects.delete_project(project2.get_uuid())


if __name__ == '__main__':
    unittest.main()
