"""
    propagation_params.py
"""


class PropagationParams(object):
    """Represents the parameters to set for a propagation."""

    DEFAULT_CONFIG_ID = "00000000-0000-0000-0000-000000000001"
    DEFAULT_EXECUTOR = "STK"

    @classmethod
    def fromJsonResponse(cls, response_prop_params, description):
        # Ignores opm, which should be processed separately.
        return PropagationParams({
            'start_time': response_prop_params['start_time'],
            'end_time': response_prop_params['end_time'],
            'step_size': response_prop_params['step_duration_sec'],
            'propagator_uuid': response_prop_params['propagator_uuid'],
            'description': description,
            'executor': response_prop_params.get('executor',
                                                 PropagationParams.DEFAULT_EXECUTOR),
        })

    def __init__(self, params):
        """
        Args:
            params (dict): Propagation parameters

        Parameters consist of::

            --- start_time and end_time are required! ---
            start_time (str): start time of the run
            end_time (str): end time of the run

            step_size (int): step size in seconds. Defaults to 86400, or one day.
            propagator_uuid (str): propagator settings to use (default is the Sun,
                all planets, and the Moon as point masses [no asteroids])
            description (str): human-readable description of the run
            executor (str): particular type of software to use, defaults to STK
            propagationType (str): one of {'HYPERCUBE_FACES', 'HYPERCUBE_CORNERS',
                'MONTE_CARLO', 'USER_SPECIFIED'}
            monteCarloDraws (int): number of draws for a Monte Carlo propagation.
            keplerianSigma (dict): Keplerian elements uncertainty (semi_major_axis_km,
                eccentricity, inclination_deg, ra_of_asc_node_deg,
                arg_of_pericenter_deg, true_anomaly_deg, gm)
            cartesianSigma (dict): Cartesian elements uncertainty
                (x, y, z, x_dot, y_dot, z_dot)
            stopOnImpact (boolean): True if the propagation should stop upon impact.
            stopOnCloseApproach (boolean): True if the propagation should stop on
                the first close approach.
            stopOnImpactDistanceMeters (long): The stopping distance from the target's
                center for an impact.
            closeApproachRadiusFromTargetMeters (long): The distance from the target's
                center, within which a close approach should be recorded.
            singularMatrixThreshold (float):
                tolerance for non positive definite covariance matrix

        Raises:
            KeyError if the given object does not include 'start_time' and 'end_time',
            or if unsupported parameters are provided
        """
        # Make this a bit easier to get right by checking for parameters by unexpected
        # names.
        supported_params = {'start_time', 'end_time', 'step_size',
                            'propagator_uuid', 'project_uuid', 'description',
                            'executor', 'propagationType', 'monteCarloDraws',
                            'keplerianSigma', 'cartesianSigma', 'stopOnImpact',
                            'stopOnCloseApproach', 'stopOnImpactDistanceMeters',
                            'closeApproachRadiusFromTargetMeters',
                            'singularMatrixThreshold'}
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
        self._executor = params.get('executor') or self.DEFAULT_EXECUTOR

        self._propagation_type = params.get('propagationType')
        self._monte_carlo_draws = params.get('monteCarloDraws')
        self._keplerian_sigma = params.get('keplerianSigma')
        self._cartesian_sigma = params.get('cartesianSigma')
        self._stop_on_impact = params.get('stopOnImpact')
        self._stop_on_close_approach = params.get('stopOnCloseApproach')
        self._stop_on_impact_distance_meters = params.get('stopOnImpactDistanceMeters')
        self._stop_on_close_approach_after_epoch = params.get('stopOnCloseApproachAfterEpoch')
        self._singular_matrix_threshold = params.get('singularMatrixThreshold')
        if self._stop_on_close_approach_after_epoch is None:
            self._stop_on_close_approach_after_epoch = self._end_time
        self._close_approach_radius_from_target_meters = \
            params.get('closeApproachRadiusFromTargetMeters')

    def __repr__(self):
        return "Batch params [%s, %s, %s, %s, %s, %s, %s]" % (
            self._start_time, self._end_time, self._step_size,
            self._propagator_uuid, self._project_uuid, self._description,
            self._executor)

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

    def get_executor(self):
        return self._executor

    def get_propagation_type(self):
        return self._propagation_type

    def get_monte_carlo_draws(self):
        return self._monte_carlo_draws

    def get_keplerian_sigma(self):
        return self._keplerian_sigma

    def get_cartesian_sigma(self):
        return self._cartesian_sigma

    def get_stop_on_impact(self):
        return self._stop_on_impact

    def get_stop_on_close_approach(self):
        return self._stop_on_close_approach

    def get_stop_on_impact_distance_meters(self):
        return self._stop_on_impact_distance_meters

    def get_stop_on_close_approach_after_epoch(self):
        return self._stop_on_close_approach_after_epoch

    def get_close_approach_radius_from_target_meters(self):
        return self._close_approach_radius_from_target_meters

    def get_singular_matrix_threshold(self):
        return self._singular_matrix_threshold
