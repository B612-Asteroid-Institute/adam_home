from adam import Service
from adam import ConfigManager
from adam import Permission
from adam import PropagationParams
from adam import OpmParams

import unittest

import os


class AnonymousTest(unittest.TestCase):
    """Tests anonymous access to API.

    """

    def setUp(self):
        self.config = ConfigManager(os.getcwd() + '/test_config.json').get_config()
        self.config.set_token("")
        self.service = Service(self.config)
        self.assertTrue(self.service.setup())

    def tearDown(self):
        self.service.teardown()

    def test_access(self):
        projects_module = self.service.get_projects_module()
        permissions_module = self.service.get_permissions_module()
        groups_module = self.service.get_groups_module()

        projects = projects_module.get_projects()
        self.assertEqual(1, len(projects))
        self.assertEqual("public", projects[0].get_name())

        # Can't add a project to public project.
        public_project = "00000000-0000-0000-0000-000000000001"
        with (self.assertRaises(RuntimeError)):
            projects_module.new_project(public_project, "", "")

        # Can't run a batch in the public project.
        batches_module = self.service.get_batches_module()
        dummy_propagation_params = PropagationParams({
            'start_time': 'AAA',
            'end_time': 'BBB',
            'project_uuid': 'CCC'
        })
        dummy_opm_params = OpmParams({
            'epoch': 'DDD',
            'state_vector': [1, 2, 3, 4, 5, 6]
        })
        with (self.assertRaises(RuntimeError)):
            batches_module.new_batch(dummy_propagation_params, dummy_opm_params)

        # Anon should have no permissions.
        permissions = permissions_module.get_my_permissions()
        self.assertEqual(1, len(permissions))
        self.assertEqual(0, len(permissions[""]))

        # And anon is in no groups.
        groups = groups_module.get_my_memberships()
        self.assertEqual(0, len(groups))

        # Therefore anon can grant no permissions.
        with (self.assertRaises(RuntimeError)):
            permissions_module.grant_user_permission(
                "dummy@fake.com", Permission("READ", "PROJECT", public_project))

        # And can add/modify no groups.
        with (self.assertRaises(RuntimeError)):
            groups_module.new_group("", "")
        all_group = "00000000-0000-0000-0000-000000000001"
        with (self.assertRaises(RuntimeError)):
            groups_module.add_user_to_group("dummy@fake.com", all_group)

        # Not even allowed to see the members of the magic all group.
        with (self.assertRaises(RuntimeError)):
            groups_module.get_group_members(all_group)


if __name__ == '__main__':
    unittest.main()
