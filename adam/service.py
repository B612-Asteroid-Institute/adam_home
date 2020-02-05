"""
    service.py
"""

from adam.auth import Auth
from adam import Batches
from adam.group import Groups
from adam.permission import Permissions
from adam.project import Projects
from adam.timer import Timer
from adam.rest_proxy import RestRequests
from adam.rest_proxy import RetryingRestProxy
from adam.rest_proxy import AuthenticatingRestProxy

import datetime


class Service():
    """Module wrapping the REST API and associated client libraries. The goal of this
    module is to make it very easy and readable to do basic operations against a prod or
    dev setup.

    """

    @classmethod
    def from_config(cls, config):
        return cls(url=config['url'], workspace=config['workspace'], token=config['token'])

    def __init__(self, url, workspace, token):
        self.url = url
        self.workspace = workspace
        self.token = token

        self.working_projects = []

    def new_working_project(self):
        timer = Timer()
        timer.start("Generate working project")
        if self.workspace:
            project = self.projects.new_project(
                        self.workspace, None,
                        "Test project created at " + str(datetime.datetime.now())
                      )
            self.working_projects.append(project)
            print("Set up project with uuid " + project.get_uuid())
            timer.stop()
            return project
        else:
            print("Workspace must be configured in order to use working projects " +
                  "(which live in the workspace).")
            timer.stop()
            return None

    def setup(self):
        timer = Timer()
        timer.start("Setup")

        rest = RetryingRestProxy(RestRequests(self.url))
        auth = Auth(rest)
        if not auth.authenticate(self.token):
            print("Could not authenticate.")
            return False

        self.rest = AuthenticatingRestProxy(rest, self.token)
        self.projects = Projects(self.rest)
        self.batches = Batches(self.rest)
        self.groups = Groups(self.rest)
        self.permissions = Permissions(self.rest)

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
