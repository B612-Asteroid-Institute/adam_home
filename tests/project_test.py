import unittest

from adam import Projects
from adam.project import Project
from adam.rest_proxy import _RestProxyForTest


class ProjectTest(unittest.TestCase):
    """Unit tests for project object

    """

    def test_get_methods(self):
        project = Project("uuid", None, None, None)
        self.assertEqual("uuid", project.get_uuid())
        self.assertEqual(None, project.get_parent())
        self.assertEqual(None, project.get_name())
        self.assertEqual(None, project.get_description())

        project = Project("uuid", "parent", "name", "description")
        self.assertEqual("uuid", project.get_uuid())
        self.assertEqual("parent", project.get_parent())
        self.assertEqual("name", project.get_name())
        self.assertEqual("description", project.get_description())


class ProjectsTest(unittest.TestCase):
    """Unit tests for projects module

    """

    def test_new_project(self):
        rest = _RestProxyForTest()
        projects = Projects(rest)

        expected_data = {}

        def check_input(data_dict):
            self.assertEqual(expected_data, data_dict)
            return True

        expected_data = {'parent': None, 'name': None, 'description': None}
        rest.expect_post(Projects._REST_ENDPOINT_PREFIX, check_input, 200, {'uuid': 'aaa'})
        project = projects.new_project(None, None, None)
        self.assertEqual("aaa", project.get_uuid())
        self.assertEqual(None, project.get_parent())
        self.assertEqual(None, project.get_name())
        self.assertEqual(None, project.get_description())

        expected_data = {'parent': 'ppp', 'name': 'nnn', 'description': 'ddd'}
        rest.expect_post(Projects._REST_ENDPOINT_PREFIX, check_input, 200, {'uuid': 'ccc'})
        project = projects.new_project('ppp', 'nnn', 'ddd')
        self.assertEqual("ccc", project.get_uuid())
        self.assertEqual('ppp', project.get_parent())
        self.assertEqual('nnn', project.get_name())
        self.assertEqual('ddd', project.get_description())

        rest.expect_post(Projects._REST_ENDPOINT_PREFIX, check_input, 404, {})
        with self.assertRaises(RuntimeError):
            project = projects.new_project('ppp', 'nnn', 'ddd')

    def test_get_project(self):
        rest = _RestProxyForTest()
        projects = Projects(rest)

        rest.expect_get(f"{Projects._REST_ENDPOINT_PREFIX}/aaa", 200, {'uuid': 'aaa'})
        project = projects.get_project('aaa')
        self.assertEqual("aaa", project.get_uuid())
        self.assertEqual(None, project.get_parent())
        self.assertEqual(None, project.get_name())
        self.assertEqual(None, project.get_description())

        rest.expect_get(f"{Projects._REST_ENDPOINT_PREFIX}/ccc", 200, {'uuid': 'ccc',
                                                                       'parent': 'ppp',
                                                                       'name': 'nnn',
                                                                       'description': 'ddd'})
        project = projects.get_project('ccc')
        self.assertEqual("ccc", project.get_uuid())
        self.assertEqual('ppp', project.get_parent())
        self.assertEqual('nnn', project.get_name())
        self.assertEqual('ddd', project.get_description())

        rest.expect_get(f"{Projects._REST_ENDPOINT_PREFIX}/aaa", 404, {})
        project = projects.get_project('aaa')
        self.assertEqual(project, None)

        rest.expect_get(f"{Projects._REST_ENDPOINT_PREFIX}/aaa", 403, {})
        with self.assertRaises(RuntimeError):
            project = projects.get_project('aaa')

    def test_get_projects(self):
        rest = _RestProxyForTest()
        projects_module = Projects(rest)

        rest.expect_get(Projects._REST_ENDPOINT_PREFIX, 200,
                        {'items': [{'uuid': 'aaa'}, {'uuid': 'bbb'}]})
        projects = projects_module.get_projects()
        self.assertEqual(2, len(projects))
        self.assertEqual('aaa', projects[0].get_uuid())
        self.assertEqual('bbb', projects[1].get_uuid())

    def test_get_sub_projects(self):
        rest = _RestProxyForTest()
        projects_module = Projects(rest)

        projects_response = {'items': [
            {'uuid': 'aaa', 'parent': 'p1'},
            {'uuid': 'bbb', 'parent': 'p2'},
            {'uuid': 'ccc'},
            {'uuid': 'ddd', 'parent': 'p2'}]}

        rest.expect_get(Projects._REST_ENDPOINT_PREFIX, 200, projects_response)
        projects = projects_module.get_sub_projects('p1')
        self.assertEqual(1, len(projects))
        self.assertEqual('aaa', projects[0].get_uuid())

        rest.expect_get(Projects._REST_ENDPOINT_PREFIX, 200, projects_response)
        projects = projects_module.get_sub_projects('p2')
        self.assertEqual(2, len(projects))
        self.assertEqual('bbb', projects[0].get_uuid())
        self.assertEqual('ddd', projects[1].get_uuid())

        rest.expect_get(Projects._REST_ENDPOINT_PREFIX, 200, projects_response)
        projects = projects_module.get_sub_projects(None)
        self.assertEqual(1, len(projects))
        self.assertEqual('ccc', projects[0].get_uuid())

    def test_delete_project(self):
        rest = _RestProxyForTest()
        projects = Projects(rest)

        rest.expect_delete(f"{Projects._REST_ENDPOINT_PREFIX}/aaa", 204)
        projects.delete_project('aaa')

        # 200 isn't a valid return value for delete calls right now
        rest.expect_delete(f"{Projects._REST_ENDPOINT_PREFIX}/aaa", 200)
        with self.assertRaises(RuntimeError):
            projects.delete_project('aaa')

        rest.expect_delete(f"{Projects._REST_ENDPOINT_PREFIX}/aaa", 404)
        with self.assertRaises(RuntimeError):
            projects.delete_project('aaa')


if __name__ == '__main__':
    unittest.main()
