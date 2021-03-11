from adam import Batch
from adam import PropagationParams
from adam import OpmParams
from adam import BatchRunManager

import datetime

import numpy as np
import numpy.testing as npt


class TestBackwardsPropagation:
    """Integration test of backwards propagation.

    """

    def _make_batch(self, state_vec, start_time, end_time, working_project):
        start_time_str = start_time.isoformat() + 'Z'
        end_time_str = end_time.isoformat() + 'Z'

        propagation_params = PropagationParams({
            'start_time': start_time_str,
            'end_time': end_time_str,
            'step_size': 86400,
            'project_uuid': working_project.get_uuid(),
            'description': 'Created by test at ' + start_time_str
        })
        opm_params = OpmParams({
            'epoch': start_time_str,
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

    def test_backwards_and_forwards(self, service, working_project):
        now = datetime.datetime.now()
        later = now + datetime.timedelta(10 * 365)  # 10 years

        state_vec = [130347560.13690618,
                     -74407287.6018632,
                     -35247598.541470632,
                     23.935241263310683,
                     27.146279819258538,
                     10.346605942591514]

        print("Starting at %s" % (state_vec))

        print("Propagating forward from %s to %s" % (now, later))
        batch = self._make_batch(state_vec, now, later, working_project)
        runner = BatchRunManager(service.get_batches_module(), [batch])
        runner.run()
        forward_end_state = batch.get_results().get_end_state_vector()
        print("Final state at %s" % forward_end_state)

        print("Propagating backward from %s to %s" % (later, now))
        batch = self._make_batch(forward_end_state, later, now, working_project)
        runner = BatchRunManager(service.get_batches_module(), [batch])
        runner.run()
        backwards_end_state = batch.get_results().get_end_state_vector()
        print("Final state at %s" % backwards_end_state)

        difference = np.subtract(state_vec, backwards_end_state)
        print("Difference is %s" % difference)

        # This test appears to be flaky. Usually it fails on the first of the following 2 asserts,
        # but sometimes, very rarely, it will pass on the first assert and fail on the second.
        # Example differences (subtracting backwards end state from initial state vector):
        # [ 4.60617244e-03  5.23680449e-03  1.98936462e-03
        #  -9.19317955e-10  5.18536325e-10  2.51514365e-10] <-- fails on 1st assert
        # [ 2.29061693e-02  2.58967876e-02  9.86936688e-03
        #  -4.50932092e-09  2.57853827e-09  1.22151356e-09] <-- fails on 1st assert
        # [ 6.06164336e-04  7.16790557e-04  2.69368291e-04
        #  -1.19317889e-10  7.85398413e-11  3.15143467e-11] <-- fails on 2nd assert
        npt.assert_allclose(difference[0:3], [0, 0, 0], rtol=0, atol=1e-3)
        npt.assert_allclose(difference[3:6], [0, 0, 0], rtol=0, atol=1e-10)
