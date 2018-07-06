"""
    targeted_propagation.py
"""
from adam.adam_objects import AdamObject
from adam.adam_objects import AdamObjects
from adam.batch_propagation import SinglePropagation
from adam.opm_params import OpmParams
from adam.propagation_params import PropagationParams

from datetime import datetime, timedelta


class AccessCalculation(AdamObject):
    def __init__(self, propagation_params, opm_params, asteroid_propagation_uuid,
                access_start_time, access_end_time, pointings_table_name):
        """
            asteroid_propagation_uuid (string): UUID of SinglePropagation to use as asteroid location.
                Either asteroid_propagation_uuid or propagation_params/opm_params are required.
            access_start_time (string): Start time of interval in which accesses should be computed.
                (ISO format, UTC). Required!
            access_end_time (string): End time of interval in which accesses should be computed.
                (ISO format, UTC). Required!
            pointings_table_name (string): Name of the sql table in which the telescope pointings are stored.
        """
        AdamObject.__init__(self)
        self._propagation_params = propagation_params
        self._opm_params = opm_params
        self._asteroid_propagation_uuid = asteroid_propagation_uuid
        self._access_start_time = access_start_time
        self._access_end_time = access_end_time
        self._pointings_table_name = pointings_table_name
        self._accesses = None

    # Accesses format:
    #    List of [JD start, JD end, datetime start, datetime end]
    def set_accesses(self, accesses):
        self._accesses = accesses

    def _parse_isoformat_date(self, date):
        # TODO(jcarrico): Find a more precise datetime library.
        parts = date.split(".")
        micros = float("0." + parts[1].replace('Z', ''))

        parsed = datetime.strptime(parts[0], "%Y-%m-%dT%H:%M:%S")
        parsed = parsed + timedelta(microseconds=micros * 1000000)
        return parsed
    
    def set_accesses_from_str(self, accesses):
        if accesses is None:
            self._accesses = []
        else:
            self._accesses = []
            for a in accesses:
                if a == '':
                    continue

                jdates = [float(time) for time in a.split(';')[0].split(',')]
                datetimes = [self._parse_isoformat_date(time) for time in a.split(';')[1].split(',')]
                self._accesses.append([jdates[0], jdates[1], datetimes[0], datetimes[1]])
            # default implementation seems to sort by elements of subarrays in order.
            self._accesses.sort()

    def get_propagation_params(self):
        return self._propagation_params

    def get_opm_params(self):
        return self._opm_params

    def get_asteroid_propagation_uuid(self):
        return self._asteroid_propagation_uuid
    
    def get_access_start_time(self):
        return self._access_start_time
    
    def get_access_end_time(self):
        return self._access_end_time
    
    def get_pointings_table_name(self):
        return self._pointings_table_name

    def get_accesses(self):
        return self._accesses

class AccessCalculations(AdamObjects):
    def __init__(self, rest):
        AdamObjects.__init__(self, rest, 'LsstAccessCalculation')

    def __repr__(self):
        return "AccessCalculations module"

    def _build_access_calculation_creation_data(self, access_calculation):
        propagation_params = access_calculation.get_propagation_params()
        opm_params = access_calculation.get_opm_params()
        data = {
            'description': propagation_params.get_description() if propagation_params is not None else '',
            'asteroidPropagationUuid': access_calculation.get_asteroid_propagation_uuid(),
            'accessStartTime': access_calculation.get_access_start_time(),
            'accessEndTime': access_calculation.get_access_end_time(),
            'pointingsTableName': access_calculation.get_pointings_table_name(),
        }

        if propagation_params is not None:
            data['asteroidPropagationParameters'] = {
                'start_time': propagation_params.get_start_time(),
                'end_time': propagation_params.get_end_time(),
                'propagator_uuid': propagation_params.get_propagator_uuid(),
                'step_duration_sec': propagation_params.get_step_size(),
                'opmFromString': opm_params.generate_opm(),
            }

        return data
    
    def insert_all(self, access_calculations, project_uuid):
        all_data = {'requests': [], 'project': project_uuid}
        for access_calculation in access_calculations:
            all_data['requests'].append(self._build_access_calculation_creation_data(access_calculation))
        uuids = AdamObjects._insert_all(self, all_data)
        for i in range(len(uuids)):
            access_calculations[i].set_uuid(uuids[i])

    def insert(self, access_calculation, project_uuid):
        data = self._build_access_calculation_creation_data(access_calculation)
        data['project'] = project_uuid
        access_calculation.set_uuid(AdamObjects._insert(self, data))

    def update_with_results(self, access_calculation):
        uuid = access_calculation.get_uuid()
        response = AdamObjects._get_json(self, uuid)
        if response is None:
            raise RuntimeError("Could not retrieve results for " + uuid)

        access_calculation.set_accesses_from_str(response.get('accesses'))
    
    def _access_calculation_from_json_response(self, response):
        opm_params = None
        prop_params = None
        if 'asteroidPropagationParameters' in response:
            opm_params = OpmParams.fromJsonResponse(
                response['asteroidPropagationParameters']['opm'])
            prop_params = PropagationParams.fromJsonResponse(
                response['asteroidPropagationParameters'], response.get('description'))

        access_calculation = AccessCalculation(
            prop_params, opm_params, response.get('asteroidPropagationUuid'), 
            response.get('accessStartTime'), response.get('accessEndTime'),
            response.get('pointingsTableName'))
        uuid = response['uuid']
        access_calculation.set_uuid(uuid)
        access_calculation.set_accesses_from_str(response.get('accesses'))

        return access_calculation

    def get(self, uuid):
        response = AdamObjects._get_json(self, uuid)
        if response is None:
            return None
        
        return self._access_calculation_from_json_response(response)

    def get_children(self, uuid, skip_access_children=True):
        children_types_and_uuids = AdamObjects._get_children_types_and_uuids(self, uuid)

        # We want to skip the LsstAccessCalculations, since their results will have been summarized
        # into the parent (so fetching is redundant).

        children = []
        for child_type, child_uuid in children_types_and_uuids:
            if skip_access_children and child_type == 'LsstAccessCalculation':
                continue
            
            childJson, child_runnable_state, child_type = AdamObjects._get_child_json(
                self, child_type, child_uuid)

            child = None
            if child_type == 'SinglePropagation':
                childOpmParams = OpmParams.fromJsonResponse(
                    childJson['propagationParameters']['opm'])
                childPropParams = PropagationParams.fromJsonResponse(
                    childJson['propagationParameters'], childJson.get('description'))
                child = SinglePropagation(childPropParams, childOpmParams)
                child.set_uuid(childJson['uuid'])
                child.set_ephemeris(childJson.get('ephemeris'))
                child.set_final_state_vector(childJson.get('finalStateVector'))
            elif child_type == 'LsstAccessCalculation':
                child = self._access_calculation_from_json_response(childJson)
            else:
                print('Skipping child of unexpected type ' + child_type)
                continue

            child.set_runnable_state(child_runnable_state)
            children.append(child)

        return children
