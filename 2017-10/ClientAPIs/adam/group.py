"""
    group.py
"""

from datetime import datetime
from tabulate import tabulate

class Group(object):
    def __init__(self, uuid, name=None, description=None):
        self._uuid = uuid
        self._name = name
        self._description = description

    def __repr__(self):
        return "Group %s" % (self._uuid)
    
    def get_uuid(self):
        return self._uuid
        
    def get_name(self):
        return self._name
        
    def get_description(self):
        return self._description

class GroupMember(object):
    def __init__(self, uuid, type):
        self._uuid = uuid
        self._type = type
    
    def __repr__(self):
        return "Group member %s [%s]" % (self._uuid, self._type)
    
    def get_uuid(self):
        return self._uuid
    
    def get_type(self):
        return self._type

class Groups(object):
    """Module for managing groups.

    """
    
    def __init__(self, rest):
        self._rest = rest
        
    def __repr__(self):
        return "Groups module"
    
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
        code, response = self._rest.post('/group_member/' + group,
            {'member_uuid': user, 'member_type': 'USER'})
        
        if code != 200:
            raise RuntimeError("Server status code: %s; Response: %s" % (code, response))
    
    def remove_user_from_group(self, user, group):
        code = self._rest.delete('/group_member/' + group + '?member_uuid=' + user + '&member_type=USER')
        
        if code != 204:
            raise RuntimeError("Server status code: %s" % (code))
    
    def add_group_to_group(self, group1, group2):
        code, response = self._rest.post('/group_member/' + group2,
            {'member_uuid': group1, 'member_type': 'GROUP'})
        
        if code != 200:
            raise RuntimeError("Server status code: %s; Response: %s" % (code, response))
    
    def remove_group_from_group(self, group1, group2):
        code = self._rest.delete('/group_member/' + group2 + '?member_uuid=' + group1 + '&member_type=GROUP')
        
        if code != 204:
            raise RuntimeError("Server status code: %s" % (code))
    
    def _get_group_members(self, group):
        code, response = self._rest.get('/group_member/' + group)
        
        if code != 200:
            raise RuntimeError("Server status code: %s; Response: %s" % (code, response))
        
        return response['items']
    
    def get_group_members(self, group):
        return [GroupMember(m['member_uuid'], m['member_type']) for m in self._get_group_members(group)]
    
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
