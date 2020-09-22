"""
    service.py
"""

import datetime

from adam import Batches
from adam import ConfigManager
from adam.adam_processing_service import AdamProcessingService
from adam.auth import Auth
from adam.config_profile import ADAM_CONFIG_PROFILE
from adam.group import Groups
from adam.permission import Permissions
from adam.project import Projects
from adam.rest_proxy import AuthenticatingRestProxy
from adam.rest_proxy import RestRequests
from adam.rest_proxy import RetryingRestProxy
from adam.timer import Timer


class Service(object):
    """Module wrapping the REST API and associated client libraries. The goal of this
    module is to make it very easy and readable to do basic operations against a prod or
    dev setup.

    """

    @classmethod
    def from_config(cls, config=None):
        if config is None:
            config = ConfigManager().get_config(environment=ADAM_CONFIG_PROFILE.profile_name)
        return cls(url=config['url'], project=config['workspace'])

    def __init__(self, url, project):
        self.url = url
        self.project = project

        self.working_projects = []

    def new_working_project(self, project_name=None):
        """Creates a new project under the root project (workspace) in the ADAM configuration.

        Args:
            project_name (str): The name for the new project.

        Returns:
            Project: the newly created project, or None, if there is no configured root project.
        """
        timer = Timer()
        timer.start(f"Create a new working project under project {self.project}")
        if self.project:
            project = self.projects.new_project(
                self.project, project_name,
                "Test project created at " + str(datetime.datetime.now())
            )
            self.working_projects.append(project)
            print("Set up project with uuid " + project.get_uuid())
            timer.stop()
            return project
        else:
            print("A root project must be configured in order to use other working projects " +
                  "(which live under the root project).")
            timer.stop()
            return None

    def setup(self):
        """Sets up the API client and modules for issuing requests to the ADAM API."""
        timer = Timer()
        timer.start("Setup")

        retrying_rest = RetryingRestProxy(RestRequests())
        self.rest = AuthenticatingRestProxy(retrying_rest)
        auth = Auth(self.rest)
        if not auth.authenticate():
            print("Could not authenticate.")
            return False

        self.projects = Projects(self.rest)
        self.batches = Batches(self.rest)
        self.groups = Groups(self.rest)
        self.permissions = Permissions(self.rest)
        self.processing_service = AdamProcessingService(self.rest)

        timer.stop()
        return True

    def teardown(self):
        timer = Timer()
        timer.start("Teardown")
        for project in self.working_projects:
            print("Cleaning up working project %s..." % (project.get_uuid()))
            self.projects.delete_project(project.get_uuid())
        timer.stop()

    def get_projects_module(self):
        return self.projects

    def get_batches_module(self):
        return self.batches

    def get_groups_module(self):
        return self.groups

    def get_permissions_module(self):
        return self.permissions
