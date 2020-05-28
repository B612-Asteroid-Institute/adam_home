import json
import urllib


class ApsResults:
    @classmethod
    def fromRESTwithRawIds(self, rest, project_uuid, job_uuid):
        results_processor = ApsRestServiceResultsProcessor(rest, project_uuid)
        return ApsResults(results_processor, job_uuid)

    def __init__(self, results_processor, job_uuid):
        self._rp = results_processor
        self._job_uuid = job_uuid
        self._results_uuid = None
        self._results = None

    def __str__(self):
        return f'{self.json()}'

    def json(self):
        return { 'job_uuid': self._job_uuid,
                 'results': self._results}

    def check_status(self):
        return self._rp.check_status(self._job_uuid)

    def get_results(self, forceRefresh=True):
        if (forceRefresh or self._results is None):
            results = self._rp.get_results(self._job_uuid)
            self._results = results

        return self._results


class BatchPropagationResults(ApsResults):
    @classmethod
    def fromRESTwithRawIds(self, rest, project_uuid, job_uuid):
        results_processor = ApsRestServiceResultsProcessor(rest, project_uuid)
        return BatchPropagationResults(results_processor, job_uuid)

    def __init__(self, results_processor, job_uuid):
        ApsResults.__init__(self, results_processor, job_uuid)
        self._detailedOutputs = None

    def get_final_positions(self, forceUpdate=True):
        if (self._detailedOutputs is None or forceUpdate):
            results = self.get_results()
            self._detailedOutputs = json.loads(results['outputDetailsJson'])

        return self._detailedOutputs['finalPositionsByType']

    def get_result_ephemeris_count(self, forceUpdate=True):
        if (self._detailedOutputs is None or forceUpdate):
            results = self.get_results()
            self._detailedOutputs = json.loads(results['outputDetailsJson'])

        ephemeris = self._detailedOutputs['ephemeris']
        if (ephemeris is None):
            return 0

        ephemeris_objects = ephemeris['ephemerisResourcePath']
        if (ephemeris_objects is None):
            return 0

        return len(ephemeris_objects)

    def get_result_ephemeris(self, run_number, forceUpdate=True):
        if (self._detailedOutputs is None or forceUpdate):
            results = self.get_results()
            self._detailedOutputs = json.loads(results['outputDetailsJson'])

        ephemeris = self._detailedOutputs['ephemeris']
        ephemeris_resource_name = ephemeris['ephemerisResourcePath'][run_number]
        url = urllib.parse.urljoin(ephemeris['resourceBasePath'], ephemeris_resource_name)
        with urllib.request.urlopen(url) as response:
            return response.read().decode('utf-8')


class AdamProcessingService:
    def __init__(self, rest):
        self._rest = rest

    def __repr__(self):
        return "Adam Processing Service Class"

    def get_jobs(self, project):
        code, response = self._rest.get(f'/aps/{project}/jobs')
        return response

    def execute_batch_propagation(self, project, propagation_params, opm_params):
        #
        data = self._build_batch_creation_data(propagation_params, opm_params)

        code, response = self._rest.post(f'/aps/{project}/propagation/batch', data)

        if code != 200:
            raise RuntimeError("Server status code: %s; Response: %s" % (code, response))

        results_processor = ApsRestServiceResultsProcessor(self._rest, project)
        job_uuid = response['uuid']

        return ApsResults(results_processor, job_uuid)

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


class ApsRestServiceResultsProcessor:
    def __init__(self, rest, project):
        self._rest = rest
        self._project = project

    def __repr__(self):
        return "Adam Results Processing Class"

    def check_status(self, job_uuid):
        code, response = self._rest.get(f'/aps/{self._project}/job/{job_uuid}/status')
        if code != 200:
            raise RuntimeError("Server status code: %s; Response: %s" % (code, response))

        return response

    def get_results(self, job_uuid):
        code, response = self._rest.get(f'/aps/{self._project}/job/{job_uuid}/result')
        if code != 200:
            raise RuntimeError("Server status code: %s; Response: %s" % (code, response))

        return response



