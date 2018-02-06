# This is janky. Why do we have to do this?
import sys
sys.path.append('..')

from adam import Service

import json
import unittest

import os

class GroupsTest(unittest.TestCase):
    """Integration test of group management.
    
    """
    def _clean_up(self):
        groups = self.service.get_groups_module()
        my_groups = groups.get_my_memberships()
        if len(my_groups) > 0:
            print("Cleaning up " + str(len(my_groups)) + " groups...")
        for g in my_groups:
            groups.delete_group(g.get_uuid())
        
    
    def setUp(self):
        self.service = Service()
        self.assertTrue(self.service.setup_with_test_account(prod=False))
        self.me = "b612.adam.test@gmail.com"
        self._clean_up()

    def tearDown(self):
        self.service.teardown()
        self._clean_up()
        
    def test_group_management(self):
        groups = self.service.get_groups_module()
        
        group = groups.new_group("name", "description")
        self.assertTrue(group.get_uuid() is not None)
        self.assertTrue(group.get_name() == "name")
        self.assertTrue(group.get_description() == "description")
        
        groups.delete_group(group.get_uuid())
    
    def _get_user_member_ids(self, members):
        return [member.get_uuid() for member in members if member.get_type() == "USER"]
        
    def _get_group_member_ids(self, members):
        return [member.get_uuid() for member in members if member.get_type() == "GROUP"]
    
    def test_membership_management(self):
        groups = self.service.get_groups_module()
        
        my_memberships = groups.get_my_memberships()
        self.assertTrue(len(my_memberships) == 0)
        
        g1 = groups.new_group("g1", "")
        
        # Current structure:
        #   me -> g1
        
        my_memberships = groups.get_my_memberships()
        self.assertTrue(len(my_memberships) == 1)
        self.assertTrue(g1.get_uuid() in [g.get_uuid() for g in my_memberships])
        
        g1_members = groups.get_group_members(g1.get_uuid())
        self.assertTrue(len(self._get_group_member_ids(g1_members)) == 0)
        self.assertTrue(len(self._get_user_member_ids(g1_members)) == 1)
        self.assertTrue(self.me in self._get_user_member_ids(g1_members))
        
        groups.add_user_to_group("u1", g1.get_uuid())
        
        # Current structure:
        #   me -> g1
        #   u1 -> g1
        
        g1_members = groups.get_group_members(g1.get_uuid())
        self.assertTrue(len(self._get_group_member_ids(g1_members)) == 0)
        self.assertTrue(len(self._get_user_member_ids(g1_members)) == 2)
        self.assertTrue(self.me in self._get_user_member_ids(g1_members))
        self.assertTrue("u1" in self._get_user_member_ids(g1_members))
        
        g2 = groups.new_group("g2", "")
        
        # Current structure:
        #   me -> g1
        #   u1 -> g1
        #   me -> g2
        
        my_memberships = groups.get_my_memberships()
        self.assertTrue(len(my_memberships) == 2)
        self.assertTrue(g1.get_uuid() in [g.get_uuid() for g in my_memberships])
        self.assertTrue(g2.get_uuid() in [g.get_uuid() for g in my_memberships])
        
        g2_members = groups.get_group_members(g2.get_uuid())
        self.assertTrue(len(self._get_group_member_ids(g2_members)) == 0)
        self.assertTrue(len(self._get_user_member_ids(g2_members)) == 1)
        self.assertTrue(self.me in self._get_user_member_ids(g2_members))
        
        groups.add_group_to_group(g1.get_uuid(), g2.get_uuid())
        
        # Current structure:
        #   me -> g1
        #   u1 -> g1
        #   me -> g2
        #   g1 -> g2
        
        my_memberships = groups.get_my_memberships()
        self.assertTrue(len(my_memberships) == 2)
        self.assertTrue(g1.get_uuid() in [g.get_uuid() for g in my_memberships])
        # Should not be duplicated, even though I'm in this group two ways.
        self.assertTrue(g2.get_uuid() in [g.get_uuid() for g in my_memberships])
        
        g2_members = groups.get_group_members(g2.get_uuid())
        self.assertTrue(len(self._get_group_member_ids(g2_members)) == 1)
        # u1 is now a member of g2 transitively through g1. However, members of groups
        # are not retrieved recursively, so it won't show up in the list of direct
        # members of g2.
        self.assertTrue(len(self._get_user_member_ids(g2_members)) == 1)
        self.assertTrue(self.me in self._get_user_member_ids(g2_members))
        self.assertTrue(g1.get_uuid() in self._get_group_member_ids(g2_members))
        
        groups.delete_group(g2.get_uuid())
        
        # Current structure:
        #   me -> g1
        #   u1 -> g1
        
        my_memberships = groups.get_my_memberships()
        self.assertTrue(len(my_memberships) == 1)
        self.assertTrue(g1.get_uuid() in [g.get_uuid() for g in my_memberships])
        
        g1_members = groups.get_group_members(g1.get_uuid())
        self.assertTrue(len(self._get_group_member_ids(g1_members)) == 0)
        self.assertTrue(len(self._get_user_member_ids(g1_members)) == 2)
        self.assertTrue(self.me in self._get_user_member_ids(g1_members))
        self.assertTrue("u1" in self._get_user_member_ids(g1_members))
                
        groups.delete_group(g1.get_uuid())
        
        # Current structure:
        
        my_memberships = groups.get_my_memberships()
        self.assertTrue(len(my_memberships) == 0)
        

if __name__ == '__main__':
    unittest.main()