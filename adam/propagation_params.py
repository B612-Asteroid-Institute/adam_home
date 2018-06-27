"""
    propagation_params.py
"""


class PropagationParams(object):

    DEFAULT_CONFIG_ID = "00000000-0000-0000-0000-000000000001"

    @classmethod
    def fromJsonResponse(cls, response_prop_params, description):
        # Ignores opm, which should be processed separately.
        return PropagationParams({
            'start_time': response_prop_params['start_time'],
            'end_time': response_prop_params['end_time'],
            'step_size': response_prop_params['step_duration_sec'],
            'propagator_uuid': response_prop_params['propagator_uuid'],
            'description': description,
        })

    def __init__(self, params):
        """
        Param options are:

            --- start_time and end_time are required! ---
            start_time (str): start time of the run
            end_time (str): end time of the run

            step_size (int): step size in seconds. Defaults to 86400, or one day.
            propagator_uuid (str): propagator settings to use (default is the Sun,
                all planets, and the Moon as point masses [no asteroids])
            description (str): human-readable description of the run

        Raises:
            KeyError if the given object does not include 'start_time' and 'end_time',
            or if unsupported parameters are provided
        """
        # Make this a bit easier to get right by checking for parameters by unexpected
        # names.
        supported_params = {'start_time', 'end_time', 'step_size',
                            'propagator_uuid', 'project_uuid', 'description'}
        extra_params = params.keys() - supported_params
        if len(extra_params) > 0:
            raise KeyError("Unexpected parameters provided: %s" %
                           (extra_params))

        self._start_time = params['start_time']  # Required.
        self._end_time = params['end_time']  # Required.
        # Check explicitly for None, since 0 is a valid value.
        self._step_size = params.get('step_size') if params.get(
            'step_size') is not None else 86400
        self._propagator_uuid = params.get(
            'propagator_uuid') or self.DEFAULT_CONFIG_ID
        self._project_uuid = params.get('project_uuid')
        self._description = params.get('description')

    def __repr__(self):
        return "Batch params [%s, %s, %s, %s, %s, %s]" % (
            self._start_time, self._end_time, self._step_size,
            self._propagator_uuid, self._project_uuid, self._description)

    def get_start_time(self):
        return self._start_time

    def get_end_time(self):
        return self._end_time

    def get_step_size(self):
        return self._step_size

    def get_propagator_uuid(self):
        return self._propagator_uuid

    def get_project_uuid(self):
        return self._project_uuid

    def get_description(self):
        return self._description
