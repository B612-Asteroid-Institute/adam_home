"""
    project.py
"""

from tabulate import tabulate
from adam.batch import OpmParams
from adam.batch import PropagationParams

class TypeAndUuid(object):
    def __init__(self, uuid, typee):
        self._uuid = uuid
        self._type = typee

    def get_uuid(self):
        return self._uuid

    def get_type(self):
        return self._type

class AdamObjectRunnableState(object):
    def __init__(self, response):
        self._uuid = response['uuid']
        self._calc_state = response['calculationState']
        self._error = response.get('error')
    
    def get_uuid(self):
        return self._uuid
    
    def get_calc_state(self):
        return self._calc_state
    
    def get_error(self):
        return self._error

class AdamObjects(object):
    """Module for managing AdamObjects.

    """
    def __init__(self, rest, obj_type):
        self._rest = rest
        self._type = obj_type

    def __repr__(self):
        return "AdamObjects module"

    def create(self, data):
        code, response = self._rest.post('/adam_object/individual/' + self._type, data)

        if code != 200:
            raise RuntimeError("Server status code: %s; Response: %s" % (code, response))

        return TypeAndUuid(response['uuid'], response['type'])

    
    def delete(self, uuid):
        code = self._rest.delete('/adam_object/individual/' + self._type + '/' + uuid)

        if code != 204:
            raise RuntimeError("Server status code: %s" % (code))
    
    def get_runnable_state(self, uuid):
        code, response = self._rest.get('/adam_object/runnable_state/individual/' + self._type + '/' + uuid)

        if code == 404:
            return None
        elif code != 200:
            raise RuntimeError("Server status code: %s; Response: %s" % (code, response))

        print(response)
        return AdamObjectRunnableState(response)
    
    def get_runnable_states(self, project):
        code, response = self._rest.get('/adam_object/runnable_state/by_project/' + self._type + '/' + project)

        if code == 404:
            return None
        elif code != 200:
            raise RuntimeError("Server status code: %s; Response: %s" % (code, response))

        print(response)
        return [AdamObjectRunnableState(r) for r in response['items']]
    
    def _get_json(self, uuid):
        code, response = self._rest.get('/adam_object/individual/' + self._type + '/' + uuid)

        if code == 404:
            return None
        elif code != 200:
            raise RuntimeError("Server status code: %s; Response: %s" % (code, response))

        return response
