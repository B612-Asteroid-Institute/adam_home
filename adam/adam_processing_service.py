from adam import PropagationParams, OpmParams, Project
from adam import ApsRestServiceResultsProcessor, MonteCarloResults
from adam import AuthenticatingRestProxy, RestRequests


class AdamProcessingService:
    """The ADAM service handling operations related to jobs."""

    def __init__(self, rest=AuthenticatingRestProxy(RestRequests())):
        self._rest = rest

    def __repr__(self):
        return "Adam Processing Service Class"

    def execute_batch_propagation(self,
                                  project,
                                  propagation_params: PropagationParams,
                                  opm_params: OpmParams,
                                  object_id=None,
                                  user_defined_id=None) -> MonteCarloResults:
        """Create a new job to run a batch propagation.

        Args:
            project (str | Project): The workspace (project) id or project object
            propagation_params (PropagationParams): Parameters for the propagation.
            opm_params (OpmParams): Parameters specific to the OPM.
            object_id (str): The object id
            user_defined_id (str): The user-defined id

        Returns:
            MonteCarloResults: a reference to batch propagation object.
        """

        project_id = project.get_uuid() if type(project) is Project else project
        data = self._build_batch_creation_data(propagation_params, opm_params,
                                               object_id, user_defined_id)

        code, response = self._rest.post(f'/projects/{project_id}/jobs', data)

        if code != 200:
            raise RuntimeError("Server status code: %s; Response: %s" % (code, response))

        results_processor = ApsRestServiceResultsProcessor(self._rest, project)
        job_uuid = response['uuid']

        return MonteCarloResults(results_processor, job_uuid)

    def _build_batch_creation_data(self, propagation_params, opm_params, object_id,
                                   user_defined_id):
        propagation_params_json = {
            'start_time': propagation_params.get_start_time(),
            'end_time': propagation_params.get_end_time(),
            'step_duration_sec': propagation_params.get_step_size(),
            'propagator_uuid': propagation_params.get_propagator_uuid(),
            'project': propagation_params.get_project_uuid(),
            'monteCarloDraws': propagation_params.get_monte_carlo_draws(),
            'propagationType': propagation_params.get_propagation_type(),
            'stopOnImpact': propagation_params.get_stop_on_impact(),
            'cartesianSigma': propagation_params.get_cartesian_sigma(),
            'stopOnCloseApproach': propagation_params.get_stop_on_close_approach(),
            'stopOnImpactAltitudeMeters':
                propagation_params.get_stop_on_impact_altitude_meters(),
            'stopOnCloseApproachAfterEpoch':
                propagation_params.get_stop_on_close_approach_after_epoch(),
            'closeApproachRadiusFromTargetMeters':
                propagation_params.get_close_approach_radius_from_target_meters(),
            'singularMatrixThreshold':
                propagation_params.get_singular_matrix_threshold()
        }

        if propagation_params.get_cartesian_sigma() is not None:
            propagation_params_json['cartesianSigma'] = propagation_params.get_cartesian_sigma()

        if propagation_params.get_keplerian_sigma() is not None:
            propagation_params_json['keplerianSigma'] = propagation_params.get_keplerian_sigma()

        data = {
            'templatePropagationParameters': propagation_params_json,
            'opm_string': opm_params.generate_opm(),
            'description': propagation_params.get_description(),
        }

        if (object_id is not None):
            data['objectId'] = object_id

        if (user_defined_id is not None):
            data['userDefinedId'] = user_defined_id

        return data
