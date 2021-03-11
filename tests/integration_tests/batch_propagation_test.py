from adam import PropagationParams
from adam import OpmParams
from adam import BatchPropagation
from adam import BatchPropagations

import datetime


class TestBatchPropagation:

    def _new_batch_propagation(self):
        now = datetime.datetime.utcnow()
        later = now + datetime.timedelta(10 * 365)

        propagation_params = PropagationParams({
            'start_time': now.isoformat() + 'Z',
            'end_time': later.isoformat() + 'Z',
            'step_size': 60 * 60,  # 1 hour.
            'description': 'Created by test at ' + str(now) + 'Z'
        })

        state_vec = [130347560.13690618,
                     -74407287.6018632,
                     -35247598.541470632,
                     23.935241263310683,
                     27.146279819258538,
                     10.346605942591514]
        opm_params = OpmParams({
            'epoch': now.isoformat() + 'Z',
            'state_vector': state_vec,

            # Comment out state_vector and uncomment this to try with keplerian elements instead.
            # 'keplerian_elements': {
            #     'semi_major_axis_km': 3.1307289138037175E8,
            #     'eccentricity': 0.5355029800000188,
            #     'inclination_deg': 23.439676743246295,
            #     'ra_of_asc_node_deg': 359.9942693176405,
            #     'arg_of_pericenter_deg': 328.5584374618295,
            #     'true_anomaly_deg': -127.01778914927144,
            #     'gm': 1.327124400419394E11
            # },

            'mass': 500.5,
            'solar_rad_area': 25.2,
            'solar_rad_coeff': 1.2,
            'drag_area': 33.3,
            'drag_coeff': 2.5,

            'originator': 'Test',
            'object_name': 'TestObj',
            'object_id': 'TestObjId',

            # Uncomment this to try a hypercube propagation.
            # Lower triangular covariance matrix (21 elements in a list)
            # 'covariance': [
            #     3.331349476038534e-04,
            #     4.618927349220216e-04, 6.782421679971363e-04,
            #     -3.070007847730449e-04, -4.221234189514228e-04, 3.231931992380369e-04,
            #     -3.349365033922630e-07, -4.686084221046758e-07, 2.484949578400095e-07, 4.296022805587290e-10,  # NOQA (we want to keep the visual triangle)
            #     -2.211832501084875e-07, -2.864186892102733e-07, 1.798098699846038e-07, 2.608899201686016e-10, 1.767514756338532e-10,  # NOQA
            #     -3.041346050686871e-07, -4.989496988610662e-07, 3.540310904497689e-07, 1.869263192954590e-10, 1.008862586240695e-10, 6.224444338635500e-10],  # NOQA
            # 'perturbation': 3,
            # 'hypercube': 'FACES',
        })

        return BatchPropagation(propagation_params, opm_params)

    def test_batch_propagation(self, service, working_project):
        batch_propagation = self._new_batch_propagation()
        props = BatchPropagations(service.rest)

        props.insert_all([batch_propagation], self.working_project.get_uuid())
        uuid = batch_propagation.get_uuid()
        assert uuid is not None
        print(uuid)

        runnable_state = props.get_runnable_state(uuid)
        assert runnable_state is not None
        while (runnable_state.get_calc_state() != 'COMPLETED'):
            print(runnable_state.get_calc_state())
            runnable_state = props.get_runnable_state(uuid)
            assert runnable_state is not None
        assert runnable_state.get_calc_state() == 'COMPLETED'
        assert runnable_state.get_error() is None

        runnable_state_list = props.get_runnable_states(working_project.get_uuid())
        assert len(runnable_state_list) == 1

        props.update_with_results(batch_propagation)
        assert batch_propagation is not None

        fresh_batch = props.get(uuid)
        assert fresh_batch is not None

        children = props.get_children(uuid)
        assert len(batch_propagation.get_final_state_vectors()) == len(children)
        for i in range(len(batch_propagation.get_final_state_vectors())):
            assert batch_propagation.get_final_state_vectors()[i] == \
                   children[i].get_final_state_vector()

        props.delete(uuid)

        assert props.get(uuid) is None
        assert len(props.get_children(uuid)) == 0
