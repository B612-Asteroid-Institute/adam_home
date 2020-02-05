from adam import PropagationParams
from adam import OpmParams
from adam import RunnableManager
from adam import TargetedPropagation
from adam import TargetedPropagations
from adam import TargetingParams


class TestTargetedPropagationTest:

    def _new_targeted_propagation(self, initial_maneuver, working_project):
        start = '2013-05-25T00:00:02.000000Z'
        end = '2018-04-25T03:06:14.200000Z'
        propagation_params = PropagationParams({
            'start_time': start,
            'end_time': end,
            'project_uuid': working_project.get_uuid(),
            'description': 'Created by test at ' + start
        })

        state_vec = [-1.4914794358536252e+8,
                     1.0582106861692128e+8,
                     6.0492834101479955e+7,
                     -11.2528789273597756,
                     -22.3258231726462242,
                     -9.7271222877710155]
        opm_params = OpmParams({
            'epoch': start,
            'state_vector': state_vec,
            'initial_maneuver': initial_maneuver,
        })

        return TargetedPropagation(propagation_params, opm_params, TargetingParams(
            {'target_distance_from_earth': 1.0e4, 'tolerance': 1.0}))

    def test_targeted_propagation(self, service, working_project):
        targeted_propagation = self._new_targeted_propagation([0, 0, 0], working_project)

        props = TargetedPropagations(service.rest)

        props.insert(targeted_propagation, working_project.get_uuid())
        uuid = targeted_propagation.get_uuid()
        assert uuid is not None

        runnable_state = props.get_runnable_state(uuid)
        assert runnable_state is not None
        while (runnable_state.get_calc_state() != 'COMPLETED' and
               runnable_state.get_calc_state() != 'FAILED'):
            runnable_state = props.get_runnable_state(uuid)
            assert runnable_state is not None
        assert 'COMPLETED' == runnable_state.get_calc_state()
        assert runnable_state.get_error() is None

        runnable_state_list = props.get_runnable_states(working_project.get_uuid())
        assert len(runnable_state_list) == 1

        props.update_with_results(targeted_propagation)
        assert targeted_propagation.get_ephemeris() is not None
        maneuver = targeted_propagation.get_maneuver()

        fresh_targeted_prop = props.get(uuid)
        assert fresh_targeted_prop is not None
        assert fresh_targeted_prop.get_uuid() == uuid

        props.delete(uuid)

        assert props.get(uuid) is None

        # Create a new propagation with the given maneuver as the initial maneuver.
        # It should report no additional maneuver needed.
        targeted_propagation2 = self._new_targeted_propagation(maneuver, working_project)

        RunnableManager(props, [targeted_propagation2],
                        working_project.get_uuid()).run()
        assert maneuver[0] == targeted_propagation2.get_maneuver()[0]
        assert maneuver[1] == targeted_propagation2.get_maneuver()[1]
        assert maneuver[2] == targeted_propagation2.get_maneuver()[2]
