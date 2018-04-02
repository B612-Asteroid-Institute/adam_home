from adam import Permission
from adam import Permissions
from adam.rest_proxy import _RestProxyForTest
import unittest

class PermissionTest(unittest.TestCase):
    """Unit tests for permission object

    """
    
    def test_get_methods(self):
        permission = Permission("GRANT_READ", "PROJECT", "uuid")
        self.assertEqual("GRANT_READ", permission.get_right())
        self.assertEqual("PROJECT", permission.get_target_type())
        self.assertEqual("uuid", permission.get_target_uuid())

    def test_bad_inputs(self):
        with self.assertRaises(KeyError):
            Permission(None, "PROJECT", "id")
        with self.assertRaises(KeyError):
            Permission("Not a right", "PROJECT", "id")
        with self.assertRaises(KeyError):
            Permission("Admin", "PROJECT", "id")  # Case sensitive
        with self.assertRaises(KeyError):
            Permission("ADMIN", None, "id")
        with self.assertRaises(KeyError):
            Permission("ADMIN", "not a target type", "id")
        with self.assertRaises(KeyError):
            Permission("ADMIN", "pROJECT", "id")  # Case sensitive
        with self.assertRaises(KeyError):
            Permission("ADMIN", "PROJECT", None)  # Case sensitive

class PermissionsTest(unittest.TestCase):
    """Unit tests for permissions module

    """
    
    def test_grant_user_permission(self):
        rest = _RestProxyForTest()
        permissions = Permissions(rest)

        expected_data = {}
        def check_input(data_dict):
            self.assertEqual(expected_data, data_dict)
            return True
        
        expected_data = {'right': 'ADMIN', 'target_type': 'PROJECT', 'target_id': 'id'}
        rest.expect_post('/user_permission/u1', check_input, 200, expected_data)
        
        p1 = Permission('ADMIN', 'PROJECT', 'id')
        permissions.grant_user_permission('u1', p1)
        
        rest.expect_post('/user_permission/u1', check_input, 404, {})
        with self.assertRaises(RuntimeError):
            permissions.grant_user_permission('u1', p1)
    
    def test_grant_group_permission(self):
        rest = _RestProxyForTest()
        permissions = Permissions(rest)

        expected_data = {}
        def check_input(data_dict):
            self.assertEqual(expected_data, data_dict)
            return True
        
        expected_data = {'right': 'ADMIN', 'target_type': 'PROJECT', 'target_id': 'id'}
        rest.expect_post('/group_permission/g1', check_input, 200, expected_data)
        
        p1 = Permission('ADMIN', 'PROJECT', 'id')
        permissions.grant_group_permission('g1', p1)
        
        rest.expect_post('/group_permission/g1', check_input, 404, {})
        with self.assertRaises(RuntimeError):
            permissions.grant_group_permission('g1', p1)
        
    def test_revoke_user_permission(self):
        rest = _RestProxyForTest()
        permissions = Permissions(rest)
        
        rest.expect_delete(
            '/user_permission/u1?right=ADMIN&target_type=PROJECT&target_id=id', 204)
            
        p1 = Permission('ADMIN', 'PROJECT', 'id')
        permissions.revoke_user_permission('u1', p1)
        
        rest.expect_delete(
            '/user_permission/u1?right=ADMIN&target_type=PROJECT&target_id=id', 200)
            
        with self.assertRaises(RuntimeError):
            permissions.revoke_user_permission('u1', p1)
        
    def test_revoke_group_permission(self):
        rest = _RestProxyForTest()
        permissions = Permissions(rest)
        
        rest.expect_delete(
            '/group_permission/g1?right=ADMIN&target_type=PROJECT&target_id=id', 204)
            
        p1 = Permission('ADMIN', 'PROJECT', 'id')
        permissions.revoke_group_permission('g1', p1)
        
        rest.expect_delete(
            '/group_permission/g1?right=ADMIN&target_type=PROJECT&target_id=id', 200)
            
        with self.assertRaises(RuntimeError):
            permissions.revoke_group_permission('g1', p1)
            
    def test_get_my_permissions(self):
        rest = _RestProxyForTest()
        permissions = Permissions(rest)
        
        rest.expect_get('/user_permission?recursive=true', 200,
            {'': [{'right': 'ADMIN', 'target_type': 'PROJECT', 'target_id': 'id'}]})
        
        ps = permissions.get_my_permissions()
        self.assertEqual(ps, {'': [Permission('ADMIN', 'PROJECT', 'id')]})
            
    def test_get_your_permissions(self):
        rest = _RestProxyForTest()
        permissions = Permissions(rest)
        
        rest.expect_get('/user_permission/other_user?recursive=true', 200,
            {'': [{'right': 'ADMIN', 'target_type': 'PROJECT', 'target_id': 'id'}]})
        
        ps = permissions.get_my_permissions(user_superuser_only='other_user')
        self.assertEqual(ps, {'': [Permission('ADMIN', 'PROJECT', 'id')]})
            
    def test_get_group_permissions(self):
        rest = _RestProxyForTest()
        permissions = Permissions(rest)
        
        rest.expect_get('/group_permission/g1?recursive=true', 200,
            {'g1': [{'right': 'ADMIN', 'target_type': 'PROJECT', 'target_id': 'id'}],
             'g2': [{'right': 'READ', 'target_type': 'GROUP', 'target_id': 'id2'}]})
        
        ps = permissions.get_group_permissions('g1')
        self.assertEqual(ps, {'g1': [Permission('ADMIN', 'PROJECT', 'id')],
                              'g2': [Permission('READ', 'GROUP', 'id2')]})


if __name__ == '__main__':
    unittest.main()
