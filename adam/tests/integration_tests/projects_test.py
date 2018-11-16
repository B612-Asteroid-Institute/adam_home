from adam import Service
from adam import ConfigManager

import unittest

import os


class ProjectsTest(unittest.TestCase):
    """Integration test of project management.

    """

    def setUp(self):
        config = ConfigManager(os.getcwd() + '/test_adam_config.json').get_config()
        self.service = Service(config)
        self.assertTrue(self.service.setup())
        self.working_project = self.service.new_working_project()
        self.assertIsNotNone(self.working_project)

    def delete_children(self, project):
        projects = self.service.get_projects_module().get_projects()

        # First topographically sort all children of <project> so that we can delete
        # them in dependency-order.
        parent_map = {}
        for p in projects:
            parent_map[p.get_uuid()] = p.get_parent()

        children = [project.get_uuid()]
        change = 1
        while change > 0:
            change = 0
            for p in projects:
                if not p.get_uuid() in children and p.get_parent() in children:
                    children.append(p.get_uuid())
                    change = change + 1

        children = children[1:]
        if len(children) > 0:
            print("Cleaning up " + str(len(children))
                  + " children of " + project.get_uuid())
        for p in reversed(children):
            self.service.get_projects_module().delete_project(p)

    def tearDown(self):
        self.delete_children(self.working_project)
        self.service.teardown()

    def test_projects(self):
        parent = self.working_project
        p = self.service.get_projects_module()

        projects = p.get_projects()
        self.assertTrue(parent.get_uuid() in [p.get_uuid() for p in projects])

        p1 = p.new_project(parent.get_uuid(), 'p1', 'description')
        self.assertTrue(p1.get_uuid() is not None)
        self.assertTrue(p1.get_parent() == parent.get_uuid())
        self.assertTrue(p1.get_name() == 'p1')
        self.assertTrue(p1.get_description() == 'description')

        projects = p.get_projects()
        self.assertTrue(parent.get_uuid() in [p.get_uuid() for p in projects])
        self.assertTrue(p1.get_uuid() in [p.get_uuid() for p in projects])

        p2 = p.new_project(p1.get_uuid(), 'p2', 'another description')
        self.assertTrue(p2.get_uuid() is not None)
        self.assertTrue(p2.get_parent() == p1.get_uuid())

        projects = p.get_projects()
        self.assertTrue(parent.get_uuid() in [p.get_uuid() for p in projects])
        self.assertTrue(p1.get_uuid() in [p.get_uuid() for p in projects])
        self.assertTrue(p2.get_uuid() in [p.get_uuid() for p in projects])

        # Can't delete the project before its children are deleted.
        try:
            p.delete_project(p1.get_uuid())
            self.fail("Expected error deleting project that still has children.")
        except RuntimeError:
            pass  # This is expected

        p.delete_project(p2.get_uuid())
        p.delete_project(p1.get_uuid())


if __name__ == '__main__':
    unittest.main()
