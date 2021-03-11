from adam import PropagationParams
from adam import OpmParams
from adam import BatchPropagation
from adam import BatchPropagations
from adam import RunnableManager

import datetime


class TestRunnableManager:

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

            'mass': 500.5,
            'solar_rad_area': 25.2,
            'solar_rad_coeff': 1.2,
            'drag_area': 33.3,
            'drag_coeff': 2.5,

            'originator': 'Test',
            'object_name': 'TestObj',
            'object_id': 'TestObjId',
        })

        return BatchPropagation(propagation_params, opm_params)

    def test_runnable_manager(self, service, working_project):
        batch_propagations = [self._new_batch_propagation() for i in range(3)]
        batch_propagations_module = BatchPropagations(service.rest)

        manager = RunnableManager(
            batch_propagations_module, batch_propagations, working_project.get_uuid())
        manager.run()

        for prop in batch_propagations:
            assert 'COMPLETED' == prop.get_runnable_state().get_calc_state()

            assert len(prop.get_final_state_vectors()) == len(prop.get_children())
            for i in range(len(prop.get_final_state_vectors())):
                assert \
                    prop.get_final_state_vectors()[i] == \
                    prop.get_children()[i].get_final_state_vector()
