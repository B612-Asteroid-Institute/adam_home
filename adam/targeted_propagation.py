"""
    project.py
"""

from tabulate import tabulate
from adam.adam_objects import AdamObjects
from adam.opm_params import OpmParams
from adam.propagation_params import PropagationParams

import json

class TargetedPropagation(object):
    def __init__(self, uuid, propagation_params, opm_params, targeting_params, ephemeris=None, maneuver=None):
        self._uuid = uuid
        self._propagation_params = propagation_params
        self._opm_params = opm_params
        self._targeting_params = targeting_params
        self._ephemeris = ephemeris
        self._maneuver = maneuver
    
    def get_uuid(self):
        return self._uuid

    def get_propagation_params(self):
        return self._propagation_params

    def get_opm_params(self):
        return self._opm_params

    def get_targeting_params(self):
        return self._targeting_params
    
    def get_ephemeris(self):
        return self._ephemeris
    
    def get_maneuver(self):
        return self._maneuver

class TargetingParams(object):
    @classmethod
    def fromJsonResponse(cls, response_targeting_params):
        return TargetingParams({
            'target_distance_from_earth': response_targeting_params['targetDistanceFromEarth'],
            'tolerance': response_targeting_params['tolerance'],
            'run_nominal_only': response_targeting_params['runNominalOnly'],
        })

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


class TargetedPropagations(AdamObjects):
    """Module for managing targeted propagations.

    """

    def __init__(self, rest):
        AdamObjects.__init__(self, rest, 'TargetedPropagation')

    def __repr__(self):
        return "TargetedPropagations module"

    def _build_targeted_propagation_creation_data(self, propagation_params, opm_params, targeting_params, project_uuid):
        data = {'description': propagation_params.get_description(),
                'initialPropagationParameters': {
                    'start_time': propagation_params.get_start_time(),
                    'end_time': propagation_params.get_end_time(),
                    'propagator_uuid': propagation_params.get_propagator_uuid(),
                    'stepDurationSec': propagation_params.get_step_size(),
                    'opmFromString': opm_params.generate_opm(),
                },
                'targetingParameters': {
                    'targetDistanceFromEarth': targeting_params.get_target_distance_from_earth(),
                    'tolerance': targeting_params.get_tolerance(),
                    'runNominalOnly': targeting_params.get_run_nominal_only(),
                },
                'project': project_uuid}

        return data

    def new_targeted_propagation(self, propagation_params, opm_params, targeting_params, project_uuid):
        data = self._build_targeted_propagation_creation_data(propagation_params, opm_params, targeting_params, project_uuid)
        return AdamObjects.create(self, data)
    
    def get_targeted_propagation(self, uuid):
        response = AdamObjects._get_json(self, uuid)
        if response is None:
            return None
            
        opmParams = OpmParams.fromJsonResponse(response['initialPropagationParameters']['opm'])
        propParams = PropagationParams.fromJsonResponse(
            response['initialPropagationParameters'], response.get('description'))
        targetingParams = TargetingParams.fromJsonResponse(response['targetingParameters'])
        ephemeris = response.get('ephemeris')
        maneuver = None
        if 'maneuverX' in response:
            maneuver = [response['maneuverX'], response['maneuverY'], response['maneuverZ']]
        return TargetedPropagation(response['uuid'], propParams, opmParams, targetingParams, ephemeris, maneuver)
