from adam import Permission

import pytest


class TestPermissions:
    """Integration test of permissions management.

    """

    def test_permission_management(self, service, added_groups):
        permissions = service.get_permissions_module()

        # Create three groups to grant permission to.
        groups = service.get_groups_module()
        group1 = groups.new_group("name1", "description1")
        added_groups.append(group1)
        group2 = groups.new_group("name2", "description2")
        added_groups.append(group2)
        group3 = groups.new_group("name3", "description3")
        added_groups.append(group3)

        # All permissions lists should be empty.
        pms = permissions.get_group_permissions(group1.get_uuid())
        assert pms == {group1.get_uuid(): []}
        pms = permissions.get_group_permissions(group2.get_uuid())
        assert pms == {group2.get_uuid(): []}
        pms = permissions.get_group_permissions(group3.get_uuid())
        assert pms == {group3.get_uuid(): []}

        # I should have permission to all three groups.
        pms = permissions.get_my_permissions()
        assert Permission('ADMIN', 'GROUP', group1.get_uuid()) in pms['']
        assert Permission('ADMIN', 'GROUP', group2.get_uuid()) in pms['']
        assert Permission('ADMIN', 'GROUP', group3.get_uuid()) in pms['']

        # Add WRITE permission for group1 on group2.
        pm1 = Permission('WRITE', 'GROUP', group2.get_uuid())
        permissions.grant_group_permission(group1.get_uuid(), pm1)

        # group1 should have that permissions listed. Other groups should be unaffected.
        pms = permissions.get_group_permissions(group1.get_uuid())
        assert pms == {group1.get_uuid(): [pm1]}
        pms = permissions.get_group_permissions(group2.get_uuid())
        assert pms == {group2.get_uuid(): []}
        pms = permissions.get_group_permissions(group3.get_uuid())
        assert pms == {group3.get_uuid(): []}

        # Add READ permission for group2 on group3.
        pm2 = Permission('READ', 'GROUP', group3.get_uuid())
        permissions.grant_group_permission(group2.get_uuid(), pm2)

        # That should show up in group2's list.
        pms = permissions.get_group_permissions(group1.get_uuid())
        assert pms == {group1.get_uuid(): [pm1]}
        pms = permissions.get_group_permissions(group2.get_uuid())
        assert pms == {group2.get_uuid(): [pm2]}
        pms = permissions.get_group_permissions(group3.get_uuid())
        assert pms == {group3.get_uuid(): []}

        # Add group1 as a member of group2. Now pm2 should show up transitively in
        # group1's list as well.
        groups.add_group_to_group(group1.get_uuid(), group2.get_uuid())
        pms = permissions.get_group_permissions(group1.get_uuid())
        assert pms == {group1.get_uuid(): [pm1], group2.get_uuid(): [pm2]}
        pms = permissions.get_group_permissions(group2.get_uuid())
        assert pms == {group2.get_uuid(): [pm2]}
        pms = permissions.get_group_permissions(group3.get_uuid())
        assert pms == {group3.get_uuid(): []}

        # Add group2 to group3 and add ADMIN permission for group3 on group1
        # (yes, cycles are OK).
        pm3 = Permission('ADMIN', 'GROUP', group1.get_uuid())
        permissions.grant_group_permission(group3.get_uuid(), pm3)
        groups.add_group_to_group(group2.get_uuid(), group3.get_uuid())

        # pm3 should show up for everybody.
        pms = permissions.get_group_permissions(group1.get_uuid())
        assert pms == {group1.get_uuid(): [pm1],
                       group2.get_uuid(): [pm2],
                       group3.get_uuid(): [pm3]}
        pms = permissions.get_group_permissions(group2.get_uuid())
        assert pms == {group2.get_uuid(): [pm2],
                       group3.get_uuid(): [pm3]}
        pms = permissions.get_group_permissions(group3.get_uuid())
        assert pms == {group3.get_uuid(): [pm3]}

        # All of these transitive permissions should show up in my permissions.
        pms = permissions.get_my_permissions()
        assert pms[group1.get_uuid()] == [pm1]
        assert pms[group2.get_uuid()] == [pm2]
        assert pms[group3.get_uuid()] == [pm3]

        # Remove pm3, which should be removed from everybody's lists. The lists should
        # still include an item for group3 because membership hasn't changed, just with
        # no permissions directly granted.
        permissions.revoke_group_permission(group3.get_uuid(), pm3)
        pms = permissions.get_group_permissions(group1.get_uuid())
        assert pms == {group1.get_uuid(): [pm1],
                       group2.get_uuid(): [pm2],
                       group3.get_uuid(): []}
        pms = permissions.get_group_permissions(group2.get_uuid())
        assert pms == {group2.get_uuid(): [pm2],
                       group3.get_uuid(): []}
        pms = permissions.get_group_permissions(group3.get_uuid())
        assert pms == {group3.get_uuid(): []}
        pms = permissions.get_my_permissions()
        assert pms[group1.get_uuid()] == [pm1]
        assert pms[group2.get_uuid()] == [pm2]
        assert pms[group3.get_uuid()] == []

        # Delete group1. All permissions (pm1) involving group1 should no longer exist.
        groups.delete_group(group1.get_uuid())
        pms = permissions.get_group_permissions(group2.get_uuid())
        assert pms == {group2.get_uuid(): [pm2],
                       group3.get_uuid(): []}  # It's still in group3
        pms = permissions.get_group_permissions(group3.get_uuid())
        assert pms == {group3.get_uuid(): []}
        pms = permissions.get_my_permissions()
        assert not (group1.get_uuid() in pms)
        assert pms[group2.get_uuid()] == [pm2]
        assert pms[group3.get_uuid()] == []

        # Delete group2. This should remove pm2.
        groups.delete_group(group2.get_uuid())
        pms = permissions.get_my_permissions()
        assert not (group1.get_uuid() in pms)
        assert not (group2.get_uuid() in pms)
        assert pms[group3.get_uuid()] == []

        # Now grant and revoke a user permission, just to show it doesn't die.
        permissions.grant_user_permission(
            "u1", Permission('READ', 'GROUP', group3.get_uuid()))
        permissions.revoke_user_permission(
            "u1", Permission('READ', 'GROUP', group3.get_uuid()))

        groups.delete_group(group3.get_uuid())

    def test_permission_mismanagement(self, service, added_groups):
        permissions = service.get_permissions_module()

        # Target object does not exist.
        with pytest.raises(RuntimeError):
            permissions.grant_user_permission(
                'u1', Permission('READ', 'GROUP', 'wat this is not a group'))

        groups = service.get_groups_module()
        group1 = groups.new_group("name1", "description1")
        added_groups.append(group1)

        # Recipient of permission does not exist.
        with pytest.raises(RuntimeError):
            permissions.grant_group_permission(
                'g1', Permission('READ', 'GROUP', group1.get_uuid()))

        # Target does not exist.
        with pytest.raises(RuntimeError):
            permissions.grant_group_permission(
                group1.get_uuid(), Permission('READ', 'GROUP', 'wat this is not a group'))

        # Finally this works.
        permissions.grant_group_permission(
            group1.get_uuid(), Permission('READ', 'GROUP', group1.get_uuid()))

        # Unable to check authorization (target does not exist).
        # These won't raise any errors, as long as the caller has the permission to delete the
        # user permission and the deletion happens without any database errors, the API will
        # respond with a 204, *regardless* whether the permission data was actually valid or
        # not. In these cases, the permission data is invalid, but the API just returns an empty
        # response.
        #with pytest.raises(RuntimeError):
        #    permissions.revoke_user_permission(
        #        "u1", Permission('READ', 'GROUP', 'wat this is not a group'))
        #with pytest.raises(RuntimeError):
        #    permissions.revoke_group_permission(
        #        group1.get_uuid(), Permission('READ', 'GROUP', 'wat this is not a group'))

        # But this is fine. Deleting something that doesn't exist.
        permissions.revoke_group_permission(
            'not a group', Permission('READ', 'GROUP', group1.get_uuid()))

        # Can't inspect nonexistent things either.
        # This test won't fail. The API returns a set of the group permissions (if any) and does not
        # actually check the existence of the group.
        #with pytest.raises(RuntimeError):
        #    permissions.get_group_permissions('not a group')

        # Not permitted to inspect other users.
        with pytest.raises(RuntimeError):
            permissions.get_my_permissions(user_superuser_only="some other user")

        groups.delete_group(group1.get_uuid())
