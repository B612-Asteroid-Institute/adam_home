"""
    project.py
"""

from tabulate import tabulate
from adam.batch import OpmParams
from adam.batch import PropagationParams

class AdamObject(object):
    def __init__(self, uuid, typee):
        self._uuid = uuid
        self._type = typee

    def get_uuid(self):
        return self._uuid

    def get_type(self):
        return self._type

class TargetedPropagation(object):
    def __init__(self, propagation_params, opm_params, targeting_params):
        self._propagation_params = propagation_params
        self._opm_params = opm_params
        self._targeting_params = targeting_params

    def get_propagation_params(self):
        return self._propagation_params

    def get_opm_params(self):
        return self._opm_params

    def get_targeting_params(self):
        return self._targeting_params

class TargetingParams(object):

    def __init__(self, params):
        """
        Param options are:
            target_distance_from_earth (float): 
                Target distance from the center of the earth, in km. Required!
            tolerance (float): 
                Tolerance on the target distance, in km. Must be > 0. Defaults to 1 km.
            run_nominal_only (boolean):
                Whether to run only the nominal sequence of the targeter. Defaults to false.

        Raises:
            KeyError if the given object does not include 'start_time' and 'end_time',
            or if unsupported parameters are provided
        """
        # Make this a bit easier to get right by checking for parameters by unexpected
        # names.
        supported_params = {'target_distance_from_earth', 'tolerance', 'run_nominal_only'}
        extra_params = params.keys() - supported_params
        if len(extra_params) > 0:
            raise KeyError("Unexpected parameters provided: %s" %
                           (extra_params))

        self._target_distance_from_earth = params['target_distance_from_earth']  # Required.
        self._tolerance = params.get('tolerance') or 1.0
        self._run_nominal_only = params.get('run_nominal_only') or False

    def __repr__(self):
        return "Targeting params [%s, %s, %s]" % (
            self._target_distance_from_earth, self._tolerance, self._run_nominal_only)

    def get_target_distance_from_earth(self):
        return self._target_distance_from_earth

    def get_tolerance(self):
        return self._tolerance

    def get_run_nominal_only(self):
        return self._run_nominal_only


class TargetedPropagations(object):
    """Module for managing targeted propagations.

    """
    def __init__(self, rest):
        self._rest = rest

    def __repr__(self):
        return "TargetedPropagations module"

    def _build_targeted_propagation_creation_data(self, propagation_params, opm_params, targeting_params):
        data = {'startTime': propagation_params.get_start_time(),
                'endTime': propagation_params.get_end_time(),
                'stepDurationSec': propagation_params.get_step_size(),
                'propagatorUuid': propagation_params.get_propagator_uuid(),
                'opmString': opm_params.generate_opm(),
                'description': propagation_params.get_description(),
                'targetDistanceFromEarth': targeting_params.get_target_distance_from_earth(),
                'tolerance': targeting_params.get_tolerance(),
                'runNominalOnly': targeting_params.get_run_nominal_only(),
                'project': propagation_params.get_project_uuid(),
                'description': propagation_params.get_description()}

        return data

    def new_targeted_propagation(self, propagation_params, opm_params, targeting_params):
        data = self._build_targeted_propagation_creation_data(propagation_params, opm_params, targeting_params)

        code, response = self._rest.post('/adam_object/TargetedPropagation', data)

        if code != 200:
            raise RuntimeError("Server status code: %s; Response: %s" % (code, response))

        return AdamObject(response['uuid'], response['type'])

    def new_batches(self, param_pairs):
        """ Expects a list of pairs of [propagation_params, opm_params].
            Returns a list of batch summaries for the submitted batches in the same order.
        """
        batch_dicts = []
        for pair in param_pairs:
            batch_dicts.append(self._build_batch_creation_data(pair[0], pair[1]))

        code, response = self._rest.post('/batches', {'requests': batch_dicts})

        # Check error code
        if code != 200:
            raise RuntimeError("Server status code: %s; Response: %s" % (code, response))

        if len(param_pairs) != len(response['requests']):
            raise RuntimeError("Expected %s results, only got %s" %
                               (len(param_pairs), len(response['requests'])))

        # Store response values
        summaries = []
        for i in range(len(response['requests'])):
            summaries.append(StateSummary(response['requests'][i]))

        return summaries

    def delete_batch(self, uuid):
        code = self._rest.delete('/batch/' + uuid)

        if code != 204:
            raise RuntimeError("Server status code: %s" % (code))

    def get_summary(self, uuid):
        code, response = self._rest.get('/batch/' + uuid)

        if code == 404:
            return None
        elif code != 200:
            raise RuntimeError("Server status code: %s; Response: %s" % (code, response))

        return StateSummary(response)

    def _get_summaries(self, project):
        code, response = self._rest.get('/batch?project_uuid=' + project)

        if code != 200:
            raise RuntimeError("Server status code: %s; Response: %s" % (code, response))

        return response['items']

    def get_summaries(self, project):
        summaries = {}
        for s in self._get_summaries(project):
            summaries[s['uuid']] = StateSummary(s)
        return summaries

    def print_summaries(self, project, keys="batch_uuid,calc_state"):
        batches = self._get_summaries(project)

        print(tabulate(batches, headers=keys, tablefmt="fancy_grid"))

    def _get_part(self, state_summary, index):
        # Parts IDs are 1-indexed, not 0-indexed.
        url = '/batch/' + state_summary.get_uuid() + '/' + str(index + 1)
        code, part_json = self._rest.get(url)

        if code == 404:    # Not found
            return None
        if code != 200:
            raise RuntimeError("Server status code: %s; Response %s" % (code, part_json))

        return part_json

    def get_propagation_results(self, state_summary):
        """ Returns a PropagationResults object with as many PropagationPart objects as
            the state summary  claims to have parts, or raises an error. Note that if
            state of given summary is not 'COMPLETED' or 'FAILED', not all parts are
            guaranteed to exist or to have an ephemeris.
        """
        if state_summary.get_parts_count() is None or state_summary.get_parts_count() < 1:
            print("Unable to retrieve results for batch with no parts")
            return None

        parts = [self._get_part(state_summary, i)
                 for i in range(state_summary.get_parts_count())]
        return PropagationResults(parts)
