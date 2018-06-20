"""
    project.py
"""

from tabulate import tabulate
from adam.batch import OpmParams
from adam.batch import PropagationParams
from adam.adam_objects import AdamObjects

import json

class BatchPropagation(object):
    M2KM = 1E-3  # meters to kilometers

    def __init__(self, uuid, propagation_params, opm_params, summary=None):
        self._uuid = uuid
        self._propagation_params = propagation_params
        self._opm_params = opm_params
        self._summary = summary
    
    def get_uuid(self):
        return self._uuid

    def get_propagation_params(self):
        return self._propagation_params

    def get_opm_params(self):
        return self._opm_params
    
    def get_summary(self):
        return self._summary
    
    def get_final_state_vectors(self):
        return [[(float(n) * self.M2KM) for n in sv.split()] for sv in self._summary.splitlines()]


class BatchPropagations(AdamObjects):
    """Module for managing batch propagations.

    """
    def __init__(self, rest):
        AdamObjects.__init__(self, rest, 'BatchPropagation')

    def __repr__(self):
        return "BatchPropagations module"

    def _build_batch_propagation_creation_data(self, propagation_params, opm_params, project_uuid):
        data = {'description': propagation_params.get_description(),
                'templatePropagationParameters': {
                    'start_time': propagation_params.get_start_time(),
                    'end_time': propagation_params.get_end_time(),
                    'propagator_uuid': propagation_params.get_propagator_uuid(),
                    'step_duration_sec': propagation_params.get_step_size(),
                    'opmFromString': opm_params.generate_opm(),
                },
                'project': project_uuid,
                }

        return data

    def new_batch_propagation(self, propagation_params, opm_params, project_uuid):
        data = self._build_batch_propagation_creation_data(propagation_params, opm_params, project_uuid)
        return AdamObjects.create(self, data)
    
    def get_batch_propagation(self, uuid):
        response = AdamObjects._get_json(self, uuid)
        print(json.dumps(response, indent=1))
        opmParams = OpmParams.fromJsonResponse(response['templatePropagationParameters']['opm'])
        propParams = PropagationParams.fromJsonResponse(
            response['templatePropagationParameters'], response.get('description'))
        summary = response.get('summary')
        return BatchPropagation(response['uuid'], propParams, opmParams, summary)
