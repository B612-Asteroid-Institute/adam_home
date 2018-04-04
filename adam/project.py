"""
    project.py
"""

from tabulate import tabulate


class Project(object):
    def __init__(self, uuid, parent=None, name=None, description=None):
        self._uuid = uuid
        self._parent = parent
        self._name = name
        self._description = description

    def __repr__(self):
        return "Project %s" % (self._uuid)

    def get_uuid(self):
        return self._uuid

    def get_parent(self):
        return self._parent

    def get_name(self):
        return self._name

    def get_description(self):
        return self._description


class Projects(object):
    """Module for managing projects.

    """

    def __init__(self, rest):
        self._rest = rest

    def __repr__(self):
        return "Projects module"

    def _get_projects(self):
        code, response = self._rest.get('/project')

        if code != 200:
            raise RuntimeError("Server status code: %s; Response: %s" % (code, response))

        return response['items']

    def get_sub_projects(self, parent):
        # For now, this just filters the returned values by parent project. We may eventually
        # choose to implement this server-side, in which case we will call into whatever API
        # that exposes.
        return [p for p in self.get_projects() if p.get_parent() == parent]

    def get_projects(self):
        projects = []
        for p in self._get_projects():
            project = Project(p['uuid'], p.get('parent'), p.get('name'), p.get('description'))
            projects.append(project)

        return projects

    def print_projects(self):
        projects = self._get_projects()

        for p in projects:
            if len(p['description']) > 50:
                p['description'] = p['description'][:50] + "..."

        print(tabulate(projects, headers="keys", tablefmt="fancy_grid"))

    def get_project(self, uuid):
        if uuid is None:
            raise KeyError("UUID is required.")

        code, response = self._rest.get('/project/' + uuid)

        if code == 404:
            # Project not found.
            return None
        elif code != 200:
            raise RuntimeError("Server status code: %s; Response: %s" % (code, response))

        return Project(uuid,
                       response.get('parent'),
                       response.get('name'),
                       response.get('description'))

    def new_project(self, parent, name, description):
        code, response = self._rest.post(
            '/project',
            {'parent': parent, 'name': name, 'description': description})

        if code != 200:
            raise RuntimeError("Server status code: %s; Response: %s" % (code, response))

        return Project(response['uuid'], parent, name, description)

    def delete_project(self, uuid):
        code = self._rest.delete('/project/' + uuid)

        if code != 204:
            raise RuntimeError("Server status code: %s" % (code))
