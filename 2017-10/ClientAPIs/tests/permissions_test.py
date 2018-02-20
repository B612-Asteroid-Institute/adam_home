# This is janky. Why do we have to do this?
import sys
sys.path.append('..')

from adam import Service
from adam import Permission

import json
import unittest
from tabulate import tabulate

import os

class PermissionsTest(unittest.TestCase):
    """Integration test of permissions management.
    
    """
    def _clean_up(self):
        # Clean up all the groups. This should automatically clean up any permissions
        # associated with them.
        groups = self.service.get_groups_module()
        my_groups = groups.get_my_memberships()
        if len(my_groups) > 0:
            print("Cleaning up " + str(len(my_groups)) + " groups...")
        for g in my_groups:
            groups.delete_group(g.get_uuid())
        
    
    def setUp(self):
        self.service = Service()
        self.assertTrue(self.service.setup_with_test_account())
        self.me = "b612.adam.test@gmail.com"
        self._clean_up()

    def tearDown(self):
        self.service.teardown()
        self._clean_up()
        
        
    def test_permission_management(self):
        permissions = self.service.get_permissions_module()
        
        # Create three groups to grant permission to.
        groups = self.service.get_groups_module()
        group1 = groups.new_group("name1", "description1")
        group2 = groups.new_group("name2", "description2")
        group3 = groups.new_group("name3", "description3")
        
        # All permissions lists should be empty.
        pms = permissions.get_group_permissions(group1.get_uuid())
        self.assertEqual(pms, {group1.get_uuid(): []})
        pms = permissions.get_group_permissions(group2.get_uuid())
        self.assertEqual(pms, {group2.get_uuid(): []})
        pms = permissions.get_group_permissions(group3.get_uuid())
        self.assertEqual(pms, {group3.get_uuid(): []})
        
        # I should have permission to all three groups.
        pms = permissions.get_my_permissions()
        self.assertTrue(Permission('ADMIN', 'GROUP', group1.get_uuid()) in pms[''])
        self.assertTrue(Permission('ADMIN', 'GROUP', group2.get_uuid()) in pms[''])
        self.assertTrue(Permission('ADMIN', 'GROUP', group3.get_uuid()) in pms[''])
        
        # Add WRITE permission for group1 on group2.
        pm1 = Permission('WRITE', 'GROUP', group2.get_uuid())
        permissions.grant_group_permission(group1.get_uuid(), pm1)
        
        # group1 should have that permissions listed. Other groups should be unaffected.
        pms = permissions.get_group_permissions(group1.get_uuid())
        self.assertEqual(pms, {group1.get_uuid(): [pm1]})
        pms = permissions.get_group_permissions(group2.get_uuid())
        self.assertEqual(pms, {group2.get_uuid(): []})
        pms = permissions.get_group_permissions(group3.get_uuid())
        self.assertEqual(pms, {group3.get_uuid(): []})
        
        # Add READ permission for group2 on group3.
        pm2 = Permission('READ', 'GROUP', group3.get_uuid())
        permissions.grant_group_permission(group2.get_uuid(), pm2)
        
        # That should show up in group2's list.
        pms = permissions.get_group_permissions(group1.get_uuid())
        self.assertEqual(pms, {group1.get_uuid(): [pm1]})
        pms = permissions.get_group_permissions(group2.get_uuid())
        self.assertEqual(pms, {group2.get_uuid(): [pm2]})
        pms = permissions.get_group_permissions(group3.get_uuid())
        self.assertEqual(pms, {group3.get_uuid(): []})
        
        # Add group1 as a member of group2. Now pm2 should show up transitively in
        # group1's list as well.
        groups.add_group_to_group(group1.get_uuid(), group2.get_uuid())
        pms = permissions.get_group_permissions(group1.get_uuid())
        self.assertEqual(pms, {group1.get_uuid(): [pm1],
                               group2.get_uuid(): [pm2]})
        pms = permissions.get_group_permissions(group2.get_uuid())
        self.assertEqual(pms, {group2.get_uuid(): [pm2]})
        pms = permissions.get_group_permissions(group3.get_uuid())
        self.assertEqual(pms, {group3.get_uuid(): []})
        
        # Add group2 to group3 and add ADMIN permission for group3 on group1
        # (yes, cycles are OK).
        pm3 = Permission('ADMIN', 'GROUP', group1.get_uuid())
        permissions.grant_group_permission(group3.get_uuid(), pm3)
        groups.add_group_to_group(group2.get_uuid(), group3.get_uuid())
        
        # pm3 should show up for everybody.
        pms = permissions.get_group_permissions(group1.get_uuid())
        self.assertEqual(pms, {group1.get_uuid(): [pm1],
                               group2.get_uuid(): [pm2],
                               group3.get_uuid(): [pm3]})
        pms = permissions.get_group_permissions(group2.get_uuid())
        self.assertEqual(pms, {group2.get_uuid(): [pm2],
                               group3.get_uuid(): [pm3]})
        pms = permissions.get_group_permissions(group3.get_uuid())
        self.assertEqual(pms, {group3.get_uuid(): [pm3]})
        
        # All of these transitive permissions should show up in my permissions.
        pms = permissions.get_my_permissions()
        self.assertEqual(pms[group1.get_uuid()], [pm1])
        self.assertEqual(pms[group2.get_uuid()], [pm2])
        self.assertEqual(pms[group3.get_uuid()], [pm3])
        
        # Remove pm3, which should be removed from everybody's lists. The lists should
        # still include an item for group3 because membership hasn't changed, just with 
        # no permissions directly granted.
        permissions.revoke_group_permission(group3.get_uuid(), pm3)
        pms = permissions.get_group_permissions(group1.get_uuid())
        self.assertEqual(pms, {group1.get_uuid(): [pm1],
                               group2.get_uuid(): [pm2],
                               group3.get_uuid(): []})
        pms = permissions.get_group_permissions(group2.get_uuid())
        self.assertEqual(pms, {group2.get_uuid(): [pm2],
                               group3.get_uuid(): []})
        pms = permissions.get_group_permissions(group3.get_uuid())
        self.assertEqual(pms, {group3.get_uuid(): []})
        pms = permissions.get_my_permissions()
        self.assertEqual(pms[group1.get_uuid()], [pm1])
        self.assertEqual(pms[group2.get_uuid()], [pm2])
        self.assertEqual(pms[group3.get_uuid()], [])
        
        # Delete group1. All permissions (pm1) involving group1 should no longer exist.
        groups.delete_group(group1.get_uuid())
        pms = permissions.get_group_permissions(group2.get_uuid())
        self.assertEqual(pms, {group2.get_uuid(): [pm2],
                               group3.get_uuid(): []})  # It's still in group3
        pms = permissions.get_group_permissions(group3.get_uuid())
        self.assertEqual(pms, {group3.get_uuid(): []})
        pms = permissions.get_my_permissions()
        self.assertFalse(group1.get_uuid() in pms)
        self.assertEqual(pms[group2.get_uuid()], [pm2])
        self.assertEqual(pms[group3.get_uuid()], [])
        
        # Delete group2. This should remove pm2.
        groups.delete_group(group2.get_uuid())
        pms = permissions.get_my_permissions()
        self.assertFalse(group1.get_uuid() in pms)
        self.assertFalse(group2.get_uuid() in pms)
        self.assertEqual(pms[group3.get_uuid()], [])
        
        # Now grant and revoke a user permission, just to show it doesn't die.
        permissions.grant_user_permission(
            "u1", Permission('READ', 'GROUP', group3.get_uuid()))
        permissions.revoke_user_permission(
            "u1", Permission('READ', 'GROUP', group3.get_uuid()))
        
        groups.delete_group(group3.get_uuid())
    
    def test_permission_mismanagement(self):
        permissions = self.service.get_permissions_module()
        
        # Target object does not exist.
        with self.assertRaises(RuntimeError):
            permissions.grant_user_permission(
                'u1', Permission('READ', 'GROUP', 'wat this is not a group'))
                
        groups = self.service.get_groups_module()
        group1 = groups.new_group("name1", "description1")
        
        # Recipient of permission does not exist.
        with self.assertRaises(RuntimeError):
            permissions.grant_group_permission(
                'g1', Permission('READ', 'GROUP', group1.get_uuid()))
        
        # Target does not exist.
        with self.assertRaises(RuntimeError):
            permissions.grant_group_permission(
                group1.get_uuid(), Permission('READ', 'GROUP', 'wat this is not a group'))
        
        # Finally this works.
        permissions.grant_group_permission(
            group1.get_uuid(), Permission('READ', 'GROUP', group1.get_uuid()))
        
        # Unable to check authorization (target does not exist).
        with self.assertRaises(RuntimeError):
            permissions.revoke_user_permission(
                "u1", Permission('READ', 'GROUP', 'wat this is not a group'))
        with self.assertRaises(RuntimeError):
            permissions.revoke_group_permission(
                group1.get_uuid(), Permission('READ', 'GROUP', 'wat this is not a group'))
        
        # But this is fine. Deleting something that doesn't exist.
        permissions.revoke_group_permission(
            'not a group', Permission('READ', 'GROUP', group1.get_uuid()))
        
        # Can't inspect nonexistent things either.
        with self.assertRaises(RuntimeError):
            permissions.get_group_permissions('not a group')
        
        # Not permitted to inspect other users.
        with self.assertRaises(RuntimeError):
            permissions.get_my_permissions(user_superuser_only="some other user")
        
        groups.delete_group(group1.get_uuid())


if __name__ == '__main__':
    unittest.main()