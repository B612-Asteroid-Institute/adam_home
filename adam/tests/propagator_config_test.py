from adam import PropagatorConfigs
from adam.propagator_config import PropagatorConfig
from adam.rest_proxy import _RestProxyForTest
import unittest

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
        config_json = {
            "uuid": "00000000-0000-0000-0000-000000000003",
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
            "asteroidsString": "Ceres,Pallas,Juno,Vesta,Hebe,Iris,Hygeia,Eunomia,Psyche,Amphitrite,Europa,Cybele,Sylvia,Thisbe,Davida,Interamnia"
        }
        config = PropagatorConfig(config_json)
        self.assertEqual("00000000-0000-0000-0000-000000000003", config.get_uuid())
        self.assertEqual("00000000-0000-0000-0000-000000000001", config.get_project())
        self.assertEqual("everything", config.get_description())
        self.assertEqual(config_json, config.get_config_json())

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
        rest.expect_post("/config", check_input, 200, {'uuid': 'uuid', 'project': 'project'})
        config = configs.new_config({'project': 'project'})
        self.assertEqual("uuid", config.get_uuid())
        self.assertEqual("project", config.get_project())
        self.assertEqual(None, config.get_description())



    
    # def test_new_project(self):
    #     rest = _RestProxyForTest()
    #     projects = Projects(rest)

    #     expected_data = {}
    #     def check_input(data_dict):
    #         self.assertEqual(expected_data, data_dict)
    #         return True
            
    #     expected_data = {'parent': None, 'name': None, 'description': None}
    #     rest.expect_post("/project", check_input, 200, {'uuid': 'aaa'})
    #     project = projects.new_project(None, None, None)
    #     self.assertEqual("aaa", project.get_uuid())
    #     self.assertEqual(None, project.get_parent())
    #     self.assertEqual(None, project.get_name())
    #     self.assertEqual(None, project.get_description())
            
    #     expected_data = {'parent': 'ppp', 'name': 'nnn', 'description': 'ddd'}
    #     rest.expect_post("/project", check_input, 200, {'uuid': 'ccc'})
    #     project = projects.new_project('ppp', 'nnn', 'ddd')
    #     self.assertEqual("ccc", project.get_uuid())
    #     self.assertEqual('ppp', project.get_parent())
    #     self.assertEqual('nnn', project.get_name())
    #     self.assertEqual('ddd', project.get_description())
        
        
    #     rest.expect_post("/project", check_input, 404, {})
    #     with self.assertRaises(RuntimeError):
    #         project = projects.new_project('ppp', 'nnn', 'ddd')
        
    # def test_get_project(self):
    #     rest = _RestProxyForTest()
    #     projects = Projects(rest)
        
    #     rest.expect_get("/project/aaa", 200, {'uuid': 'aaa'})
    #     project = projects.get_project('aaa')
    #     self.assertEqual("aaa", project.get_uuid())
    #     self.assertEqual(None, project.get_parent())
    #     self.assertEqual(None, project.get_name())
    #     self.assertEqual(None, project.get_description())
        
    #     rest.expect_get("/project/ccc", 200, {'uuid': 'ccc', 'parent': 'ppp', 'name': 'nnn', 'description': 'ddd'})
    #     project = projects.get_project('ccc')
    #     self.assertEqual("ccc", project.get_uuid())
    #     self.assertEqual('ppp', project.get_parent())
    #     self.assertEqual('nnn', project.get_name())
    #     self.assertEqual('ddd', project.get_description())
        
        
    #     rest.expect_get("/project/aaa", 404, {})
    #     project = projects.get_project('aaa')
    #     self.assertEqual(project, None)
        
    #     rest.expect_get("/project/aaa", 403, {})
    #     with self.assertRaises(RuntimeError):
    #         project = projects.get_project('aaa')
        
    def test_delete_config(self):
        rest = _RestProxyForTest()
        configs = PropagatorConfigs(rest)
        
        rest.expect_delete("/config/aaa", 204)
        configs.delete_config('aaa')
        
        # 200 isn't a valid return value for delete calls right now
        rest.expect_delete("/config/aaa", 200)
        with self.assertRaises(RuntimeError):
            configs.delete_config('aaa')
            
        rest.expect_delete("/config/aaa", 404)
        with self.assertRaises(RuntimeError):
            configs.delete_config('aaa')

if __name__ == '__main__':
    unittest.main()
