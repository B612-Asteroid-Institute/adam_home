class AdamProcessingService:
    def __init__(self, rest):
        self._rest = rest

    def __repr__(self):
        return "Adam Processing Service Module"

    def get_jobs(self, project):
        code, response = self._rest.get(f'/aps/{project}/jobs')
        return response

    def execute_batch_propagation(self, project, propagation_params, opm_params):
        #
        data = self._build_batch_creation_data(propagation_params, opm_params)

        code, response = self._rest.post(f'/aps/{project}/propagation/batch', data)

        if code != 200:
            raise RuntimeError("Server status code: %s; Response: %s" % (code, response))

        return response

    def _build_batch_creation_data(self, propagation_params, opm_params):
        propagation_params_json = {'start_time': propagation_params.get_start_time(),
            'end_time': propagation_params.get_end_time(),
            'step_duration_sec': propagation_params.get_step_size(),
            'propagator_uuid': propagation_params.get_propagator_uuid(),
            'project': propagation_params.get_project_uuid(),
            'monteCarloDraws': propagation_params.get_monte_carlo_draws(),
            'propagationType': propagation_params.get_propagation_type(),
        }

        if propagation_params.get_cartesian_sigma() is not None:
            propagation_params_json['cartesianSigma'] = propagation_params.get_cartesian_sigma()

        if propagation_params.get_keplerian_sigma() is not None:
            propagation_params_json['keplerianSigma'] = propagation_params.get_keplerian_sigma()

        data = {
            'templatePropagationParameters': propagation_params_json,
            'opm_string': opm_params.generate_opm(),
        }


        return data
