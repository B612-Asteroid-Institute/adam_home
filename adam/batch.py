"""
    batch.py
"""

from adam.opm_params import OpmParams
from adam.propagation_params import PropagationParams

from datetime import datetime, timedelta


class Batch(object):
    def __init__(self, propagation_params, opm_params):
        self._propagation_params = propagation_params
        self._opm_params = opm_params
        self._state_summary = None
        self._results = None

    def __repr__(self):
        return "Batch %s, %s" % (self.get_uuid(), self.get_calc_state())

    def get_propagation_params(self):
        return self._propagation_params

    def get_opm_params(self):
        return self._opm_params

    def get_state_summary(self):
        return self._state_summary

    def set_state_summary(self, state_summary):
        self._state_summary = state_summary

    def get_results(self):
        return self._results

    def set_results(self, results):
        self._results = results

    # Convenience method to get batch uuid.
    def get_uuid(self):
        if self._state_summary is None:
            return None
        return self._state_summary.get_uuid()

    # Convenience method to get batch calculation state.
    def get_calc_state(self):
        if self._state_summary is None:
            return None
        return self._state_summary.get_calc_state()

class StateSummary(object):
    def __init__(self, json):
        """ Requires a json response as returned from the server representing a batch
            state summary (e.g. from /batch/uuid or in bulk from batch/project_id)

            Raises:
                KeyError if the given object does not include 'uuid' and 'calc_state'
        """
        self._uuid = json['uuid']
        self._calc_state = json['calc_state']
        self._step_size = json.get('step_duration_sec')
        self._create_time = json.get('create_time')
        self._execute_time = json.get('execute_time')
        self._complete_time = json.get('complete_time')
        self._project_uuid = json.get('project')
        self._parts_count = json.get('parts_count')

    def __repr__(self):
        return "State summary for %s: %s" % (self._uuid, self._calc_state)

    def get_uuid(self):
        return self._uuid

    def get_step_size(self):
        return self._step_size

    def get_create_time(self):
        return self._create_time

    def get_execute_time(self):
        return self._execute_time

    def get_complete_time(self):
        return self._complete_time

    def get_project_uuid(self):
        return self._project_uuid

    def get_parts_count(self):
        return self._parts_count

    def get_calc_state(self):
        return self._calc_state


class PropagationResults(object):

    class Part(object):
        def __init__(self, part):
            """ Requires a json response as returned from the server representing a batch
                part state (e.g. from /batch/batch_uuid/part_index)

                Raises:
                    KeyError if the given object does not include 'part_index' and
                    'calc_state'
            """
            self._part_index = part['part_index']
            self._calc_state = part['calc_state']
            self._ephemeris = part.get('stk_ephemeris')
            self._error = part.get('error')

        def __repr__(self):
            return "PropagationPart [%s]" % (self._calc_state)

        def get_part_index(self):
            return self._part_index

        def get_calc_state(self):
            return self._calc_state

        def get_ephemeris(self):
            return self._ephemeris

        def get_error(self):
            return self._error

    M2KM = 1E-3  # meters to kilometers

    def __init__(self, parts):
        """ Should be called with a list of json responses from the server representing
            the parts_count parts of a batch propagation result.
        """
        if (len(parts) < 1):
            raise RuntimeError("Must provide at least one part.")

        # Fill in None responses (which may happen e.g. in case of 404s, or if the part
        # isn't ready yet) with Nones
        self._parts = [self.Part(p) if p is not None else None for p in parts]

    def __repr__(self):
        return "Propagation results with %s parts" % (len(self._parts))

    def get_parts(self):
        return self._parts

    def get_final_ephemeris(self):
        part = self._parts[-1]
        if part is None:
            print("Final part is not available")
            return None
        state = part.get_calc_state()
        if (state != 'COMPLETED'):
            print(
                "Final part is in state %s, not COMPLETED, so no ephemeris is available" % (state))
            return None
        return part.get_ephemeris()

    def _parse_date(self, date):
        # TODO(jcarrico): Find a more precise datetime library.
        parts = date.split(".")
        micros = float("0." + parts[1])

        parsed = datetime.strptime(parts[0], "%d %b %Y %H:%M:%S")
        parsed = parsed + timedelta(microseconds=micros * 1000000)
        return parsed

    def get_state_vector_at_time(self, target_epoch):
        """Get the state vector at the given time as a 6d list in [km, km/s]

        This function grabs the STK ephemeris from the final part. It parses the epoch given in
        the ephemeris in order to determine the times of all the state vectors given in the file.

        If a time is requested that does not have an explicit state vector, None will be returned.
        This will not interpolate.

        Args:
            target_epoch (datetime) - time at which a state vector is desired

        Returns:
            state_vector (list) - an array with 6 elements [rx, ry, rz, vx, vy, vz]
                                  [km, km/s]
        """
        stk_ephemeris = self.get_final_ephemeris()
        if stk_ephemeris is None:
            return None

        split_ephem = stk_ephemeris.splitlines()

        file_epoch = None
        for line in split_ephem:
            if line.startswith("ScenarioEpoch"):
                epoch_str = line.split('\t')[1]
                try:
                    file_epoch = self._parse_date(epoch_str)
                except ValueError as e:
                    print("Caught error, ignoring: " + str(e))
                    pass
        if file_epoch is None:
            print("No file epoch could be parsed")
            return None

        for line in split_ephem:
            split_line = line.split()
            # It's a state if it has more than 7 elements
            if len(split_line) >= 7:
                epoch = file_epoch + timedelta(seconds=float(split_line[0]))
                if abs((epoch - target_epoch).total_seconds()) <= 1e-6:
                    state_vector = [(float(i) * self.M2KM)
                                    for i in split_line][1:7]
                    return state_vector

        print("No state vector found at time " + str(target_epoch))
        return None

    def get_end_state_vector(self):
        """Get the end state vector as a 6d list in [km, km/s]

        This function first grabs the STK ephemeris from the final part
        The final state entry is returned as an array

        Args:

        Returns:
            state_vector (list) - an array with 6 elements [rx, ry, rz, vx, vy, vz]
                                  [km, km/s]
        """
        stk_ephemeris = self.get_final_ephemeris()
        if stk_ephemeris is None:
            return None

        split_ephem = stk_ephemeris.splitlines()
        state_vectors = []
        for line in split_ephem:
            split_line = line.split()
            # It's a state if it has more than 7 elements
            if len(split_line) >= 7:
                state_vector = [(float(i) * self.M2KM) for i in split_line]
                # Ignore time
                state_vectors.append(state_vector[1:7])

        # We want the last element
        return state_vectors[-1]
