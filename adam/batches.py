"""
    batches.py
"""

from adam.batch import StateSummary
from adam.batch import PropagationResults

# from tabulate import tabulate


class Batches(object):
    def __init__(self, rest):
        self._rest = rest

    def __repr__(self):
        return "Batches module"

    def _build_batch_creation_data(self, propagation_params, opm_params):
        data = {'start_time': propagation_params.get_start_time(),
                'end_time': propagation_params.get_end_time(),
                'step_duration_sec': propagation_params.get_step_size(),
                'propagator_uuid': propagation_params.get_propagator_uuid(),
                'project': propagation_params.get_project_uuid(),
                'opm_string': opm_params.generate_opm()}

        if propagation_params.get_description() is not None:
            data['description'] = propagation_params.get_description()

        return data

    def new_batch(self, propagation_params, opm_params):
        data = self._build_batch_creation_data(propagation_params, opm_params)

        code, response = self._rest.post('/batch', data)

        if code != 200:
            raise RuntimeError("Server status code: %s; Response: %s" % (code, response))

        return StateSummary(response)

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
        code, _ = self._rest.delete('/batch/' + uuid)

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

    # def print_summaries(self, project, keys="batch_uuid,calc_state"):
    #    batches = self._get_summaries(project)

    #    print(tabulate(batches, headers=keys, tablefmt="fancy_grid"))

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
