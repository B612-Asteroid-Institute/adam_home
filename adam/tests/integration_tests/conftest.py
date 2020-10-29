import pytest

from adam import ConfigManager
from adam import Service


@pytest.fixture(scope="class")
def service(request):
    # a class may be tagged to run in a different environment
    marker = request.node.get_closest_marker("env")
    env = marker.args[0] if marker else None

    config = ConfigManager().get_config(env)
    adam_service = Service.from_config(config)
    assert adam_service.setup()

    yield adam_service

    adam_service.teardown()


@pytest.fixture(scope="class")
def working_project(service):
    working_project = service.new_working_project()
    assert working_project is not None

    return working_project


@pytest.fixture(scope="class")
def added_groups(service):
    added_groups = []

    yield added_groups

    groups = service.get_groups_module()
    if len(added_groups) > 0:
        print("Cleaning up " + str(len(added_groups)) + " groups...")
    for g in added_groups:
        try:
            groups.delete_group(g.get_uuid())
        except RuntimeError:
            pass  # No big deal. Probably it was already deleted.


@pytest.fixture
def me(service):
    return "b612.adam.test@gmail.com"
