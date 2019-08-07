"""
    permission.py
"""

# from tabulate import tabulate


class Permission(object):
    def __init__(self, right, target_type, target_uuid):
        """Creates representation of permission.

        Args:
            right: must be one of "READ", "WRITE", "ADMIN", "GRANT_READ", "GRANT_WRITE"
            target_type: must be one of "PROJECT", "GROUP"
            target_uuid: uuid of object to be granted permission to
        """
        accepted_rights = ["READ", "WRITE", "ADMIN", "GRANT_READ", "GRANT_WRITE"]
        if right not in accepted_rights:
            raise KeyError("Right must be one of %s." % (accepted_rights))

        accepted_targets = ["PROJECT", "GROUP"]
        if target_type not in accepted_targets:
            raise KeyError("Target type must be one of %s." % (accepted_targets))

        if target_uuid is None:
            raise KeyError("Target UUID is required.")

        self._right = right
        self._target_type = target_type
        self._target_uuid = target_uuid

    def __repr__(self):
        return "Permission [%s, %s, %s]" % (self._right, self._target_type, self._target_uuid)

    def __eq__(self, other):
        return isinstance(other, self.__class__) and self.__dict__ == other.__dict__

    def get_right(self):
        return self._right

    def get_target_type(self):
        return self._target_type

    def get_target_uuid(self):
        return self._target_uuid


class Permissions(object):
    """Module for managing permissions.

    """

    def __init__(self, rest):
        self._rest = rest

    def __repr__(self):
        return "Permissions module"

    def grant_user_permission(self, user_email, permission):
        code, response = self._rest.post('/user_permission/' + user_email,
                                         {'right': permission.get_right(),
                                          'target_type': permission.get_target_type(),
                                          'target_id': permission.get_target_uuid()})

        if code != 200:
            raise RuntimeError("Server status code: %s; Response: %s" % (code, response))

    def grant_group_permission(self, group_uuid, permission):
        code, response = self._rest.post('/group_permission/' + group_uuid,
                                         {'right': permission.get_right(),
                                          'target_type': permission.get_target_type(),
                                          'target_id': permission.get_target_uuid()})

        if code != 200:
            raise RuntimeError("Server status code: %s; Response: %s" % (code, response))

    def revoke_user_permission(self, user_email, permission):
        code = self._rest.delete(
            "/user_permission/%s?right=%s&target_type=%s&target_id=%s" % (
                user_email,
                permission.get_right(),
                permission.get_target_type(),
                permission.get_target_uuid()))

        if code != 204:
            raise RuntimeError("Server status code: %s" % (code))

    def revoke_group_permission(self, group_uuid, permission):
        code = self._rest.delete(
            "/group_permission/%s?right=%s&target_type=%s&target_id=%s" % (
                group_uuid,
                permission.get_right(),
                permission.get_target_type(),
                permission.get_target_uuid()))

        if code != 204:
            raise RuntimeError("Server status code: %s" % (code))

    def get_my_permissions(self, user_superuser_only=None):
        url = "/user_permission?recursive=true"
        if user_superuser_only is not None:
            url = "/user_permission/%s?recursive=true" % (user_superuser_only)

        code, response = self._rest.get(url)

        if code != 200:
            raise RuntimeError("Server status code: %s" % (code))

        permissions = {}
        for key in response:
            permissions[key] = [Permission(
                p['right'], p['target_type'], p['target_id']) for p in response[key]]

        return permissions

    # def print_my_permissions(self, user_superuser_only=None):
    #    permissions = self.get_my_permissions(user_superuser_only)

    #    table = []
    #    for k in permissions:
    #        for p in permissions[k]:
    #            via = "Group %s" % k if k != '' else 'Directly granted'
    #            table.append({
    #                'Right': p.get_right(),
    #                'Target': "%s %s" % (p.get_target_type(), p.get_target_uuid()),
    #                'Permitted via': via
    #            })

    #    print(tabulate(table, headers="keys", tablefmt="fancy_grid"))

    def get_group_permissions(self, group_uuid):
        code, response = self._rest.get(
            "/group_permission/%s?recursive=true" % (group_uuid))

        if code != 200:
            raise RuntimeError("Server status code: %s" % (code))

        permissions = {}
        for key in response:
            permissions[key] = [Permission(
                p['right'], p['target_type'], p['target_id']) for p in response[key]]

        return permissions

    # def print_group_permissions(self, group_uuid):
    #    permissions = self.get_group_permissions(group_uuid)

    #    table = []
    #    for k in permissions:
    #        for p in permissions[k]:
    #            via = "Group %s" % k if k != group_uuid else 'Directly granted'
    #            table.append({
    #                'Right': p.get_right(),
    #                'Target': "%s %s" % (p.get_target_type(), p.get_target_uuid()),
    #                'Permitted via': via
    #            })

    #    print(tabulate(table, headers="keys", tablefmt="fancy_grid"))
