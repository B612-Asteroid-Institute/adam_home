"""
    project.py
"""


class Project(object):
    """Project class.

    An ADAM Project is like a folder for work executed in the ADAM platform.
    """
    def __init__(self, uuid, parent=None, name=None, description=None):
        """Initialize the Project data class.

        Args:
            uuid (str): the project ID.
            parent (str): the project parent ID. Defaults to `None`.
            name (str): the name of the project.
            description (str): the project description.
        """
        self._uuid = uuid
        self._parent = parent
        self._name = name
        self._description = description

    def __repr__(self):
        return (
            f"Project(uuid={self._uuid}, parent={self._parent}, "
            f"name={self._name}, description={self._description})")

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

    _REST_ENDPOINT_PREFIX = '/projects'

    def __init__(self, rest):
        """Initialize the Projects API client.

        Args:
            rest (RestProxy): a RestProxy that makes calls to the ADAM API.
        """
        self._rest = rest

    def __repr__(self):
        return f"Projects(${self._rest})"

    def _get_projects(self):
        code, response = self._rest.get(self._REST_ENDPOINT_PREFIX)

        if code != 200:
            raise RuntimeError("Server status code: %s; Response: %s" % (code, response))

        return response['items']

    def get_sub_projects(self, parent) -> [Project]:
        """Get the projects under specified parent project.

        For now, this just filters the returned values by parent project. We may eventually
        choose to implement this server-side, in which case we will call into whatever API
        that exposes.

        Args:
            parent (str): the project ID for which to get its sub-projects.

        Returns:
            list: A list of Projects.
        """
        return [p for p in self.get_projects() if p.get_parent() == parent]

    def get_projects(self):
        """Gets projects that the current user has access to read.

        Returns:
            list(Project): a list of Projects.

        Raises:
            RuntimeError if the server returns a non-200.
        """
        projects = []
        for p in self._get_projects():
            project = Project(p['uuid'], p.get('parent'), p.get('name'), p.get('description'))
            projects.append(project)

        return projects

    def get_project(self, uuid) -> Project:
        """Gets project details.

        Args:
            uuid (str): the id of the project to get.

        Returns:
            Project: the newly-created Project.

        Raises:
            RuntimeError if the server returns a non-200.
        """
        if uuid is None:
            raise KeyError("Project id is required.")

        code, response = self._rest.get(f'{self._REST_ENDPOINT_PREFIX}/{uuid}')

        if code == 404:
            return None
        elif code != 200:
            raise RuntimeError("Server status code: %s; Response: %s" % (code, response))

        return Project(uuid,
                       response.get('parent'),
                       response.get('name'),
                       response.get('description'))

    def new_project(self, parent, name, description) -> Project:
        """Creates a new project.

        Args:
            parent (str): the parent project id.
            name (str): the name of the project.
            description (str): the description of this project.

        Returns:
            Project: the newly-created Project.

        Raises:
            RuntimeError if the server returns a non-200.
        """
        code, response = self._rest.post(
            self._REST_ENDPOINT_PREFIX,
            {'parent': parent, 'name': name, 'description': description})

        if code != 200:
            raise RuntimeError("Server status code: %s; Response: %s" % (code, response))

        return Project(response['uuid'], parent, name, description)

    def delete_project(self, uuid):
        """Deletes a project.

        Args:
            uuid (str): the id of the project to delete.

        Raises:
            RuntimeError if the server returns a non-204.
        """
        code, _ = self._rest.delete(f'{self._REST_ENDPOINT_PREFIX}/{uuid}')

        if code != 204:
            raise RuntimeError("Server status code: %s" % (code))
