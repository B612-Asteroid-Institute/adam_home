from adam import Batch
from adam import PropagationParams
from adam import OpmParams
from adam import BatchRunManager

import datetime

import numpy.testing as npt


class TestBatchRunner:
    """Integration test of batch running.

    """

    def _new_dummy_batch(self, t0, t1, working_project):

        propagation_params = PropagationParams({
            'start_time': t0.isoformat() + 'Z',
            'end_time':   t1.isoformat() + 'Z',
            'step_size': 60 * 60,  # 1 hour.
            'project_uuid': working_project.get_uuid(),
            'description': 'Created by test at ' + str(datetime.datetime.utcnow()) + 'Z'
        })

        state_vec = [130347560.13690618,
                     -74407287.6018632,
                     -35247598.541470632,
                     23.935241263310683,
                     27.146279819258538,
                     10.346605942591514]
        opm_params = OpmParams({
            'epoch': t0.isoformat() + 'Z',
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

        return Batch(propagation_params, opm_params)

    def test_small_batch(self, service, working_project):
        num_batches = 3

        duration = 365  # 1 year
        t0 = datetime.datetime(2017, 11, 28, 23, 55, 59, 342380)
        t1 = t0 + datetime.timedelta(duration)

        batches = [self._new_dummy_batch(t0, t1, working_project) for i in range(num_batches)]

        runner = BatchRunManager(service.get_batches_module(), batches)
        runner.run()
        statuses = runner.get_latest_statuses()
        assert len(statuses['PENDING']) == 0
        assert len(statuses['RUNNING']) == 0
        assert len(statuses['COMPLETED']) == num_batches
        assert len(statuses['FAILED']) == 0

        # computed with ADAM on Mon, Feb 3rd 2020
        end_state_vec = [-37528896.96992882, 492948945.1669399, 204481649.0688463,
                         -11.337383565615387, 7.184818329914017, 3.3596872712864]

        for batch in batches:
            npt.assert_allclose(end_state_vec,
                                batch.get_results().get_end_state_vector(),
                                rtol=1e-11,
                                atol=0)
