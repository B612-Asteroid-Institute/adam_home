"""
    batch_propagation.py
"""

from adam.adam_objects import AdamObject
from adam.adam_objects import AdamObjects
from adam.opm_params import OpmParams
from adam.propagation_params import PropagationParams

M2KM = 1E-3  # meters to kilometers


class BatchPropagation(AdamObject):
    def __init__(self, propagation_params, opm_params):
        AdamObject.__init__(self)
        self._propagation_params = propagation_params
        self._opm_params = opm_params
        self._summary = None

    def set_summary(self, summary):
        self._summary = summary

    def get_propagation_params(self):
        return self._propagation_params

    def get_opm_params(self):
        return self._opm_params

    def get_summary(self):
        return self._summary

    def get_final_state_vectors(self):
        if self._summary is None:
            return []
        return [[(float(n) * M2KM) for n in sv.split()]
                for sv in self._summary.splitlines()]


class SinglePropagation(AdamObject):
    def __init__(self, propagation_params, opm_params):
        AdamObject.__init__(self)
        self._propagation_params = propagation_params
        self._opm_params = opm_params
        self._ephemeris = None
        self._final_state_vector = None

    def set_ephemeris(self, ephemeris):
        self._ephemeris = ephemeris

    def set_final_state_vector(self, final_state_vector):
        self._final_state_vector = None if final_state_vector is None else [
            float(n) * M2KM for n in final_state_vector.split()]

    def get_propagation_params(self):
        return self._propagation_params

    def get_opm_params(self):
        return self._opm_params

    def get_ephemeris(self):
        return self._ephemeris

    def get_final_state_vector(self):
        return self._final_state_vector


class BatchPropagations(AdamObjects):
    """Batch propagations using the runnables framework"""

    def __init__(self, rest):
        AdamObjects.__init__(self, rest, 'BatchPropagation')

    def __repr__(self):
        return "BatchPropagations module"

    def _build_batch_propagation_creation_data(
            self, propagation_params, opm_params, project_uuid):
        data = {
            'description': propagation_params.get_description(),
            'templatePropagationParameters': {
                'start_time': propagation_params.get_start_time(),
                'end_time': propagation_params.get_end_time(),
                'propagator_uuid': propagation_params.get_propagator_uuid(),
                'step_duration_sec': propagation_params.get_step_size(),
                'opmFromString': opm_params.generate_opm(),
                'executor': propagation_params.get_executor(),
                'monteCarloDraws': propagation_params.get_monte_carlo_draws(),
                'propagationType': propagation_params.get_propagation_type(),
                'singularMatrixThreshold': propagation_params.get_singular_matrix_threshold(),
            },
            'project': project_uuid,
        }

        return data

    def insert_all(self, batch_propagations, project_uuid):
        all_data = {'requests': [], 'project': project_uuid}
        for batch_propagation in batch_propagations:
            all_data['requests'].append(self._build_batch_propagation_creation_data(
                batch_propagation.get_propagation_params(),
                batch_propagation.get_opm_params()))
        uuids = AdamObjects._insert_all(self, all_data)
        for i in range(len(uuids)):
            batch_propagations[i].set_uuid(uuids[i])

    def insert(self, batch_propagation, project_uuid):
        data = self._build_batch_propagation_creation_data(
            batch_propagation.get_propagation_params(),
            batch_propagation.get_opm_params())
        data['project'] = project_uuid
        batch_propagation.set_uuid(AdamObjects._insert(self, data))

    def update_with_results(self, batch_propagation):
        uuid = batch_propagation.get_uuid()
        response = AdamObjects._get_json(self, uuid)
        if response is None:
            raise RuntimeError("Could not retrieve results for " + uuid)

        batch_propagation.set_summary(response.get('summary'))

    def get(self, uuid):
        response = AdamObjects._get_json(self, uuid)
        if response is None:
            return None

        # Values in [] are guaranteed to be present. Values in .get() may be missing.
        opmParams = OpmParams.fromJsonResponse(
            response['templatePropagationParameters']['opm'])
        propParams = PropagationParams.fromJsonResponse(
            response['templatePropagationParameters'], response.get('description'))
        batch_propagation = BatchPropagation(propParams, opmParams)

        batch_propagation.set_uuid(response['uuid'])
        batch_propagation.set_summary(response.get('summary'))
        return batch_propagation

    def get_children(self, uuid):
        child_response_list = AdamObjects._get_children_json(self, uuid)

        children = []
        for childJson, child_runnable_state, child_type in child_response_list:
            # All child types should be SinglePropagation, but ignore those
            # that aren't just in case.
            if not child_type == 'SinglePropagation':
                print('Skipping child of unexpected type ' + child_type)
                continue

            # Values in [] are guaranteed to be present. Values in .get() may be missing.
            childOpmParams = OpmParams.fromJsonResponse(
                childJson['propagationParameters']['opm'])
            childPropParams = PropagationParams.fromJsonResponse(
                childJson['propagationParameters'], childJson.get('description'))
            childProp = SinglePropagation(childPropParams, childOpmParams)
            childProp.set_uuid(childJson['uuid'])
            childProp.set_runnable_state(child_runnable_state)
            childProp.set_ephemeris(childJson.get('ephemeris'))
            childProp.set_final_state_vector(childJson.get('finalStateVector'))

            children.append(childProp)

        return children
