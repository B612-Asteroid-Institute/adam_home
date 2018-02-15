"""
    permission.py
"""

from datetime import datetime
from tabulate import tabulate

class Permission(object):
    def __init__(self, right, target_type, target_uuid):
        """Creates representation of permission.
        
        Args:
            right: must be one of "READ", "WRITE", "ADMIN", "GRANT_READ", "GRANT_WRITE"
            target_type: must be one of "PROJECT", "BATCH", "GROUP"
            target_uuid: uuid of object to be granted permission to
        """
        self._right = right
        self._target_type = target_type
        self._target_uuid = target_uuid

    def __repr__(self):
        return "Permission [%s, %s, %s]" % (self._right, self._target_type, self._target_uuid)
    
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
        
    
    def new_group(self, name, description):
        code, response = self._rest.post('/group', 
            {'name': name, 'description': description})
        
        if code != 200:
            raise RuntimeError("Server status code: %s; Response: %s" % (code, response))
        
        return Group(response['uuid'], name, description)
    
    def delete_group(self, uuid):
        code = self._rest.delete('/group/' + uuid)
        
        if code != 204:
            raise RuntimeError("Server status code: %s" % (code))
    
    def add_user_to_group(self, user, group):
        code, response = self._rest.post('/group/' + group + '/member',
            {'member_id': user, 'member_type': 'USER'})
        
        if code != 200:
            raise RuntimeError("Server status code: %s; Response: %s" % (code, response))
    
    def remove_user_from_group(self, user, group):
        code = self._rest.delete('/group/' + group + '/member?member_id=' + user + '&member_type=USER')
        
        if code != 204:
            raise RuntimeError("Server status code: %s" % (code))
    
    def add_group_to_group(self, group1, group2):
        code, response = self._rest.post('/group/' + group2 + '/member',
            {'member_id': group1, 'member_type': 'GROUP'})
        
        if code != 200:
            raise RuntimeError("Server status code: %s; Response: %s" % (code, response))
    
    def remove_group_from_group(self, group1, group2):
        code = self._rest.delete('/group/' + group2 + '/member?member_id=' + group1 + '&member_type=GROUP')
        
        if code != 204:
            raise RuntimeError("Server status code: %s" % (code))
    
    def _get_group_members(self, group):
        code, response = self._rest.get('/group/' + group + '/member')
        
        if code != 200:
            raise RuntimeError("Server status code: %s; Response: %s" % (code, response))
        
        return response['items']
    
    def get_group_members(self, group):
        return [GroupMember(m['member_id'], m['member_type']) for m in self._get_group_members(group)]
    
    def print_group_members(self, group):
        members = self._get_group_members(group)
        print(tabulate(members, headers="keys", tablefmt="fancy_grid"))
    
    def _get_memberships(self, group=None):
        url = '/group_membership?recursive=true&expand=true'
        if group is not None:
            url = url + '&group_uuid=' + group
        code, response = self._rest.get(url)
        
        if code != 200:
            raise RuntimeError("Server status code: %s; Response: %s" % (code, response))
        
        return response['items']
    
    def get_group_memberships(self, group):
        return [Group(g['uuid'], g.get('name'), g.get('description')) for g in self._get_memberships(group)]
    
    def print_group_memberships(self, group):
        groups = self._get_memberships(group)
        print(tabulate(groups, headers="keys", tablefmt="fancy_grid"))
    
    def get_my_memberships(self):
        return self.get_group_memberships(None)
        
    def print_my_memberships(self):
        self.print_group_memberships(None)
