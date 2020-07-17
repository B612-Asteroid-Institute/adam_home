import pytest

from adam import Batch
from adam import BatchRunManager
from adam import OpmParams
from adam import PropagationParams
from adam import PropagatorConfigs


class TestPropagatorConfig:
    """Test of propagator config manipulation.

    """

    def test_get_public_configs(self, service):
        # Config management isn't very common, doesn't merit direct addition to service.
        configs = PropagatorConfigs(service.rest)

        public_config_1 = configs.get_config(PropagatorConfigs.PUBLIC_CONFIG_ALL_PLANETS_AND_MOON)
        assert "00000000-0000-0000-0000-000000000001" == public_config_1.get_uuid()

        public_config_2 = configs.get_config(PropagatorConfigs.PUBLIC_CONFIG_SUN_ONLY)
        assert "00000000-0000-0000-0000-000000000002" == public_config_2.get_uuid()

        public_config_3 = configs.get_config(
            PropagatorConfigs.PUBLIC_CONFIG_ALL_PLANETS_AND_MOON_AND_ASTEROIDS)
        assert "00000000-0000-0000-0000-000000000003" == public_config_3.get_uuid()

    def test_config_management(self, service):
        # Config management isn't very common, doesn't merit direct addition to service.
        configs = PropagatorConfigs(service.rest)

        project = service.new_working_project()
        assert project is not None

        config = configs.new_config({'project': project.get_uuid(), 'description': 'test config'})
        assert project.get_uuid() == config.get_project()

        my_configs = configs.get_configs()
        assert config.get_uuid() in [c.get_uuid() for c in my_configs]

        config_again = configs.get_config(config.get_uuid())
        assert config.get_config_json() == config_again.get_config_json()

        configs.delete_config(config.get_uuid())

        my_configs = configs.get_configs()
        assert config.get_uuid() not in [c.get_uuid() for c in my_configs]

    def test_config_in_use_pins_project(self, service):
        # Config management isn't very common, doesn't merit direct addition to service.
        configs = PropagatorConfigs(service.rest)
        projects = service.get_projects_module()

        project = service.new_working_project()
        project1 = projects.new_project(project.get_uuid(), "", "")
        assert project1 is not None
        project2 = projects.new_project(project.get_uuid(), "", "")
        assert project2 is not None
        print("Added child projects to working project: " +
              "[" + project1.get_uuid() + ", " + project2.get_uuid() + "]")

        config = configs.new_config({'project': project1.get_uuid(), 'description': 'test config'})
        assert project1.get_uuid() == config.get_project()

        batch = Batch(PropagationParams({
            'start_time': '2017-10-04T00:00:00Z',
            'end_time': '2017-10-05T00:00:00Z',
            'project_uuid': project2.get_uuid(),
            'propagator_uuid': config.get_uuid()
        }), OpmParams({
            'epoch': '2017-10-04T00:00:00Z',
            'state_vector': [130347560.13690618, -74407287.6018632, -35247598.541470632,
                             23.935241263310683, 27.146279819258538, 10.346605942591514]
        }))
        BatchRunManager(service.get_batches_module(), [batch]).run()

        # Attempt to delete the project with the config in it. It should refuse because the
        # config is still in use by the batch.
        with pytest.raises(RuntimeError):
            projects.delete_project(project1.get_uuid())

        # Then delete the batch. After that, the project with the config in it should
        # delete no problem.
        service.batches.delete_batch(batch.get_uuid())
        projects.delete_project(project1.get_uuid())

        # Clean up the batch holder project.
        projects.delete_project(project2.get_uuid())
