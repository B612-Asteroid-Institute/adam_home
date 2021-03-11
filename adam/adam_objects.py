"""
    adam_objects.py
"""


class AdamObject(object):
    def __init__(self):
        self._uuid = None
        self._runnable_state = None
        self._children = None

    def set_uuid(self, uuid):
        self._uuid = uuid

    def set_runnable_state(self, runnable_state):
        self._runnable_state = runnable_state

    def set_children(self, children):
        self._children = children

    def get_uuid(self):
        return self._uuid

    def get_runnable_state(self):
        return self._runnable_state

    def get_children(self):
        return self._children


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

    def _insert_all(self, all_data):
        code, response = self._rest.post(
            '/adam_object/batch/' + self._type, all_data)

        if code != 200:
            raise RuntimeError(
                "Server status code: %s; Response: %s" % (code, response))

        return [r['uuid'] for r in response['items']]

    def _insert(self, data):
        code, response = self._rest.post(
            '/adam_object/single/' + self._type, data)

        if code != 200:
            raise RuntimeError(
                "Server status code: %s; Response: %s" % (code, response))

        return response['uuid']

    def get_runnable_state(self, uuid):
        code, response = self._rest.get(
            '/adam_object/runnable_state/single/' + self._type + '/' + uuid)

        if code == 404:
            return None
        elif code != 200:
            raise RuntimeError(
                "Server status code: %s; Response: %s" % (code, response))

        return AdamObjectRunnableState(response)

    def get_runnable_states(self, project_uuid):
        code, response = self._rest.get(
            '/adam_object/runnable_state/by_project/' + self._type + '/' + project_uuid)

        if code == 404:
            return []
        elif code != 200:
            raise RuntimeError(
                "Server status code: %s; Response: %s" % (code, response))

        return [AdamObjectRunnableState(r) for r in response['items']]

    def _get_json(self, uuid):
        code, response = self._rest.get(
            '/adam_object/single/' + self._type + '/' + uuid)

        if code == 404:
            return None
        elif code != 200:
            raise RuntimeError(
                "Server status code: %s; Response: %s" % (code, response))

        return response

    def _get_in_project_json(self, project_uuid):
        code, response = self._rest.get(
            '/adam_object/by_project/' + self._type + '/' + project_uuid)

        if code == 404:
            return []
        elif code != 200:
            raise RuntimeError(
                "Server status code: %s; Response: %s" % (code, response))

        return response['items']

    def _get_children_types_and_uuids(self, uuid):
        code, response = self._rest.get(
            '/adam_object/by_parent/' + self._type + '/' + uuid)

        if code == 404:
            return []
        elif code != 200:
            raise RuntimeError(
                "Server status code: %s; Response: %s" % (code, response))

        if response is None:
            return []

        # Format will be like [['SinglePropagation', 'uuid1'], ['LsstAccessCalculation', 'uuid2']]
        return zip(response['childTypes'], response['childUuids'])

    def _get_child_json(self, child_type, child_uuid):
        retriever = AdamObjects(self._rest, child_type)
        return [retriever._get_json(child_uuid),
                retriever.get_runnable_state(child_uuid),
                child_type]

    def _get_children_json(self, uuid):
        child_json_list = []
        for child_type, child_uuid in self._get_children_types_and_uuids(uuid):
            print('Fetching ' + child_uuid + ' of type ' + child_type)
            child_json_list.append(
                self._get_child_json(child_type, child_uuid))
        return child_json_list

    def delete(self, uuid):
        code, _ = self._rest.delete(
            '/adam_object/single/' + self._type + '/' + uuid)

        if code != 204:
            raise RuntimeError("Server status code: %s" % (code))
