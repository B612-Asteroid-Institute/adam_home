from adam import Groups
from adam.group import Group
from adam.group import GroupMember
from adam.rest_proxy import _RestProxyForTest
import unittest

class GroupTest(unittest.TestCase):
    """Unit tests for group object

    """
    
    def test_get_methods(self):
        group = Group("uuid", None, None)
        self.assertEqual("uuid", group.get_uuid())
        self.assertEqual(None, group.get_name())
        self.assertEqual(None, group.get_description())
        
        group = Group("uuid","name", "description")
        self.assertEqual("uuid", group.get_uuid())
        self.assertEqual("name", group.get_name())
        self.assertEqual("description", group.get_description())

class GroupMemberTest(unittest.TestCase):
    """Unit tests for group member object

    """
    
    def test_get_methods(self):
        member = GroupMember("uuid", "USER")
        self.assertEqual("uuid", member.get_uuid())
        self.assertEqual("USER", member.get_type())

class GroupsTest(unittest.TestCase):
    """Unit tests for groups module

    """
    
    def test_new_group(self):
        rest = _RestProxyForTest()
        groups = Groups(rest)

        expected_data = {}
        def check_input(data_dict):
            self.assertEqual(expected_data, data_dict)
            return True
            
        expected_data = {'name': None, 'description': None}
        rest.expect_post("/group", check_input, 200, {'uuid': 'aaa'})
        group = groups.new_group(None, None)
        self.assertEqual("aaa", group.get_uuid())
        self.assertEqual(None, group.get_name())
        self.assertEqual(None, group.get_description())
            
        expected_data = {'name': 'nnn', 'description': 'ddd'}
        rest.expect_post("/group", check_input, 200, {'uuid': 'ccc'})
        group = groups.new_group('nnn', 'ddd')
        self.assertEqual("ccc", group.get_uuid())
        self.assertEqual('nnn', group.get_name())
        self.assertEqual('ddd', group.get_description())
        
        
        rest.expect_post("/group", check_input, 404, {})
        with self.assertRaises(RuntimeError):
            group = groups.new_group('nnn', 'ddd')
        
    def test_delete_group(self):
        rest = _RestProxyForTest()
        groups = Groups(rest)
        
        rest.expect_delete("/group/aaa", 204)
        groups.delete_group('aaa')
        
        # 200 isn't a valid return value for delete calls right now
        rest.expect_delete("/group/aaa", 200)
        with self.assertRaises(RuntimeError):
            groups.delete_group('aaa')
            
        rest.expect_delete("/group/aaa", 404)
        with self.assertRaises(RuntimeError):
            groups.delete_group('aaa')
    
    def test_add_group_member(self):
        rest = _RestProxyForTest()
        groups = Groups(rest)

        expected_data = {}
        def check_input(data_dict):
            self.assertEqual(expected_data, data_dict)
            return True
            
        expected_data = {'member_uuid': "aaa", 'member_type': "USER"}
        rest.expect_post("/group_member/g1", check_input, 200, {})
        groups.add_user_to_group('aaa', 'g1')
            
        expected_data = {'member_uuid': "bbb", 'member_type': "GROUP"}
        rest.expect_post("/group_member/g1", check_input, 200, {})
        groups.add_group_to_group('bbb', 'g1')
    
    def test_delete_group_member(self):
        rest = _RestProxyForTest()
        groups = Groups(rest)
            
        rest.expect_delete("/group_member/g1?member_uuid=aaa&member_type=USER", 204)
        groups.remove_user_from_group('aaa', 'g1')
            
        rest.expect_delete("/group_member/g1?member_uuid=aaa&member_type=GROUP", 204)
        groups.remove_group_from_group('aaa', 'g1')
            
        rest.expect_delete("/group_member/g1?member_uuid=aaa&member_type=USER", 404)
        with self.assertRaises(RuntimeError):
            groups.remove_user_from_group('aaa', 'g1')
            
        rest.expect_delete("/group_member/g1?member_uuid=aaa&member_type=GROUP", 404)
        with self.assertRaises(RuntimeError):
            groups.remove_group_from_group('aaa', 'g1')
        
    def test_group_memberships(self):
        rest = _RestProxyForTest()
        groups = Groups(rest)
        
        rest.expect_get('/group_membership?recursive=true&expand=true&group_uuid=g1', 200, 
            {'items': []})
        memberships = groups.get_group_memberships('g1')
        self.assertTrue(len(memberships) == 0)
        
        rest.expect_get('/group_membership?recursive=true&expand=true&group_uuid=g1', 200, 
            {'items': [{'uuid': 'g2', 'name': 'n', 'description': 'd'}, {'uuid': 'g3'}]})
        memberships = groups.get_group_memberships('g1')
        self.assertTrue(len(memberships) == 2)
        self.assertTrue('g2' in [g.get_uuid() for g in memberships])
        self.assertTrue('g3' in [g.get_uuid() for g in memberships])
        
        rest.expect_get('/group_membership?recursive=true&expand=true', 200, 
            {'items': [{'uuid': 'g2', 'name': 'n', 'description': 'd'}, {'uuid': 'g3'}]})
        memberships = groups.get_my_memberships()
        self.assertTrue(len(memberships) == 2)
        self.assertTrue('g2' in [g.get_uuid() for g in memberships])
        self.assertTrue('g3' in [g.get_uuid() for g in memberships])
    
    def test_group_members(self):
        rest = _RestProxyForTest()
        groups = Groups(rest)
        
        rest.expect_get('/group_member/g1', 200, {'items': []})
        members = groups.get_group_members('g1')
        self.assertTrue(len(members) == 0)
        
        rest.expect_get('/group_member/g1', 200,
            {'items': [{'member_uuid': 'u1', 'member_type': 'USER'},
                       {'member_uuid': 'g2', 'member_type': 'GROUP'}]})
        members = groups.get_group_members('g1')
        self.assertTrue(len(members) == 2)
        self.assertTrue('u1' in [g.get_uuid() for g in members if g.get_type() == 'USER'])
        self.assertTrue('g2' in [g.get_uuid() for g in members if g.get_type() == 'GROUP'])


if __name__ == '__main__':
    unittest.main()
