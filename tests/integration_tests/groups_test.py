class TestGroups:
    """Integration test of group management.

    """

    def test_group_management(self, service, added_groups):
        groups = service.get_groups_module()

        group = groups.new_group("name", "description")
        added_groups.append(group)

        try:
            assert group.get_uuid() is not None
            assert group.get_name() == "name"
            assert group.get_description() == "description"
        finally:
            groups.delete_group(group.get_uuid())

    def _get_user_member_ids(self, members):
        return [member.get_id() for member in members if member.get_type() == "USER"]

    def _get_group_member_ids(self, members):
        return [member.get_id() for member in members if member.get_type() == "GROUP"]

    def test_membership_management(self, service, added_groups, me):
        groups = service.get_groups_module()

        g1 = groups.new_group("g1", "")
        added_groups.append(g1)

        # Current structure:
        #   me -> g1

        # assert I'm a member of g1
        my_memberships = groups.get_my_memberships()
        assert g1.get_uuid() in [g.get_uuid() for g in my_memberships]

        # assert g1 has only one USER member, and that's me
        g1_members = groups.get_group_members(g1.get_uuid())
        assert len(self._get_group_member_ids(g1_members)) == 0
        assert len(self._get_user_member_ids(g1_members)) == 1
        assert me in self._get_user_member_ids(g1_members)

        groups.add_user_to_group("u1", g1.get_uuid())

        # Current structure:
        #   me -> g1
        #   u1 -> g1

        # assert g1 has two USER mambers, me and "u1"
        g1_members = groups.get_group_members(g1.get_uuid())
        assert len(self._get_group_member_ids(g1_members)) == 0
        assert len(self._get_user_member_ids(g1_members)) == 2
        assert me in self._get_user_member_ids(g1_members)
        assert "u1" in self._get_user_member_ids(g1_members)

        g2 = groups.new_group("g2", "")
        added_groups.append(g2)

        # Current structure:
        #   me -> g1
        #   u1 -> g1
        #   me -> g2

        # assert I'm a member of g1 and g2
        my_memberships = groups.get_my_memberships()
        assert g1.get_uuid() in [g.get_uuid() for g in my_memberships]
        assert g2.get_uuid() in [g.get_uuid() for g in my_memberships]

        # assert I'm the only USER member of g2, and g2 has no GROUP members
        g2_members = groups.get_group_members(g2.get_uuid())
        assert len(self._get_group_member_ids(g2_members)) == 0
        assert len(self._get_user_member_ids(g2_members)) == 1
        assert me in self._get_user_member_ids(g2_members)

        groups.add_group_to_group(g1.get_uuid(), g2.get_uuid())

        # Current structure:
        #   me -> g1
        #   u1 -> g1
        #   me -> g2
        #   g1 -> g2

        my_memberships = groups.get_my_memberships()
        assert g1.get_uuid() in [g.get_uuid() for g in my_memberships]
        # Should not be duplicated, even though I'm in this group two ways.
        assert g2.get_uuid() in [g.get_uuid() for g in my_memberships]

        g2_members = groups.get_group_members(g2.get_uuid())
        assert len(self._get_group_member_ids(g2_members)) == 1
        # u1 is now a member of g2 transitively through g1. However, members of groups
        # are not retrieved recursively, so it won't show up in the list of direct
        # members of g2.
        assert len(self._get_user_member_ids(g2_members)) == 1
        assert me in self._get_user_member_ids(g2_members)
        assert g1.get_uuid() in self._get_group_member_ids(g2_members)

        groups.delete_group(g2.get_uuid())

        # Current structure:
        #   me -> g1
        #   u1 -> g1

        my_memberships = groups.get_my_memberships()
        assert g1.get_uuid() in [g.get_uuid() for g in my_memberships]
        assert g2.get_uuid() not in [g.get_uuid() for g in my_memberships]

        g1_members = groups.get_group_members(g1.get_uuid())
        assert len(self._get_group_member_ids(g1_members)) == 0
        assert len(self._get_user_member_ids(g1_members)) == 2
        assert me in self._get_user_member_ids(g1_members)
        assert "u1" in self._get_user_member_ids(g1_members)

        groups.delete_group(g1.get_uuid())

        # Current structure:

        my_memberships = groups.get_my_memberships()
        assert g1.get_uuid() not in [g.get_uuid() for g in my_memberships]
        assert g2.get_uuid() not in [g.get_uuid() for g in my_memberships]
