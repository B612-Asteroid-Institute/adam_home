"""
    project.py
"""

from tabulate import tabulate
from adam.batch import OpmParams
from adam.batch import PropagationParams
from adam.adam_objects import AdamObjects

import json

M2KM = 1E-3  # meters to kilometers

class BatchPropagation(object):

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
        return [[(float(n) * M2KM) for n in sv.split()] for sv in self._summary.splitlines()]

class SinglePropagation(object):
    def __init__(self, uuid, propagation_params, opm_params, ephemeris, final_state_vector):
        self._uuid = uuid
        self._propagation_params = propagation_params
        self._opm_params = opm_params
        self._ephemeris = ephemeris
        self._final_state_vector = None if final_state_vector is None else [float(n) * M2KM for n in final_state_vector.split()]
    
    def get_uuid(self):
        return self._uuid

    def get_propagation_params(self):
        return self._propagation_params

    def get_opm_params(self):
        return self._opm_params
    
    def get_ephemeris(self):
        return self._ephemeris
    
    def get_final_state_vector(self):
        return self._final_state_vector

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
        if response is None:
            return None
            
        opmParams = OpmParams.fromJsonResponse(response['templatePropagationParameters']['opm'])
        propParams = PropagationParams.fromJsonResponse(
            response['templatePropagationParameters'], response.get('description'))
        summary = response.get('summary')
        return BatchPropagation(response['uuid'], propParams, opmParams, summary)

    def get_ephemerides_for_batch_propagation(self, uuid):
        response = AdamObjects._get_children_json(self, uuid)
        if response is None:
            return []

        children = []
        for child, child_type in zip(response['children'], response['childTypes']):
            # All child types should be SinglePropagation, but ignore those that aren't just in case.
            if not child_type == 'SinglePropagation':
                print('Skipping child of unexpected type ' + child_type)
                continue
            
            childOpmParams = OpmParams.fromJsonResponse(child['propagationParameters']['opm'])
            childPropParams = PropagationParams.fromJsonResponse(
                child['propagationParameters'], child.get('description'))
            children.append(SinglePropagation(
                child['uuid'], childPropParams, childOpmParams, child.get('ephemeris'), child.get('finalStateVector')))
                
        return children

