import json
import time
import urllib
from enum import Enum

from adam import PropagationParams, OpmParams, stk


class ApsResults:
    """API for retrieving job details"""

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

    def job_id(self):
        return self._job_uuid

    def json(self):
        return {'job_uuid': self._job_uuid,
                'results': self._results}

    def check_status(self):
        return self._rp.check_status(self._job_uuid)['status']

    # TODO make this work
    def wait_for_complete(self, max_wait_sec=60, print_waiting=False):
        """Polls the job until the job completes.

        Args:
            max_wait_sec (int): the maximum time in seconds to run the wait.
                Defaults to 60.
            print_waiting (boolean): Whether to print the waiting status messages.
                Defaults to False.

        Returns:
            str: the job status.
        """

        sleep_time_sec = 1.0
        t0 = time.perf_counter()
        status = self.check_status()
        last_status = ''
        count = 0
        while status != 'COMPLETED':
            if print_waiting:
                if last_status != status:
                    print(status)
                    count = 0
                if count == 40:
                    count = 0
                    print()
                print('.', end='')
            elapsed = time.perf_counter() - t0
            if elapsed > max_wait_sec:
                raise RuntimeError(
                    f'Computation has exceeded desired wait period of {max_wait_sec} sec.')
            last_status = status
            time.sleep(sleep_time_sec)
            status = self.check_status()

    def get_results(self, force_update=True):
        if force_update or self._results is None:
            results = self._rp.get_results(self._job_uuid)
            self._results = results

        return self._results


class BatchPropagationResults(ApsResults):
    """API for retrieving propagation results and summaries"""

    class PositionOrbitType(Enum):
        """The type of orbit position in relation to a target body."""
        MISS = 'MISS'
        CLOSE_APPROACH = 'CLOSE_APPROACH'
        IMPACT = 'IMPACT'

    @classmethod
    def fromRESTwithRawIds(cls, rest, project_uuid, job_uuid):
        results_processor = ApsRestServiceResultsProcessor(rest, project_uuid)
        return BatchPropagationResults(results_processor, job_uuid)

    def __init__(self, results_processor, job_uuid):
        ApsResults.__init__(self, results_processor, job_uuid)
        self._detailedOutputs = None
        self._summary = None

    def get_summary(self, force_update=False):
        """Get the propagation results summary.

        Args:
            force_update(boolean): True if calling this method should be re-executed,
                otherwise False (default).

        Returns:
            dict: A summary of propagation results::

                {
                    'misses': number of misses,
                    'close_approach': number of close approaches,
                    'impacts': number of impacts,
                    'pc': probability of collision
                }

        """

        self.__update_results(force_update)
        # {"totalMisses": 6, "totalImpacts": 0, "totalCloseApproaches": 12}
        misses = self._summary.get('totalMisses')
        if misses is None:
            misses = 0
        close_approaches = self._summary.get('totalCloseApproaches')
        if close_approaches is None:
            close_approaches = 0
        impacts = self._summary.get('totalImpacts')
        if impacts is None:
            impacts = 0
        probability = impacts / (misses + impacts)
        return {
            'misses': misses,
            'close_approach': close_approaches,
            'impacts': impacts,
            'pc': probability
        }

    def get_final_positions(self, position_orbit_type: PositionOrbitType, force_update=False):
        """Get the final positions of all propagated objects in the job.

        Args:
            position_orbit_type (PositionOrbitType): the type of orbit position to filter.
            force_update (boolean): whether the request should be re-executed.

        Returns:
            list: A list of the final orbit positions, filtered by the position_orbit_type.
        """

        self.__update_results(force_update)
        position_type_string = position_orbit_type.value
        final_positions = self._detailedOutputs['finalPositionsByType'].get(position_type_string)
        if final_positions is None:
            return []
        positions = final_positions['finalPosition']
        return_data = list(map(lambda p: [p['x'], p['y'], p['z']], positions))
        return return_data

    def get_result_ephemeris_count(self, force_update=False):
        """Get the number of ephemerides.

        Args:
            force_update (boolean): whether the request should be re-executed.

        Returns:
            int: the number of ephemerides generated from the propagation.
        """

        self.__update_results(force_update)
        ephemeris = self._detailedOutputs.get('ephemeris')
        if ephemeris is None:
            return 0
        ephemeris_objects = ephemeris.get('ephemerisResourcePath')
        if ephemeris_objects is None:
            return 0
        return len(ephemeris_objects)

    def get_result_raw_ephemeris(self, run_number, force_update=False):
        """Get an ephemeris for a particular run in the batch.

        Args:
            force_update (boolean): whether the request should be re-executed.

        Returns:
            str: the ephemeris file as a string.
        """

        self.__update_results(force_update)
        ephemeris = self._detailedOutputs['ephemeris']
        ephemeris_resource_name = ephemeris['ephemerisResourcePath'][run_number]
        base_url = ephemeris['resourceBasePath']
        if not base_url.endswith('/'):
            base_url = base_url + '/'
        url = urllib.parse.urljoin(base_url, ephemeris_resource_name)
        with urllib.request.urlopen(url) as response:
            return response.read().decode('utf-8')

    def get_result_ephemeris(self, run_number, force_update=False):
        """Get an ephemeris for a particular run in the batch as a Panda DataFrame

        Args:
            force_update (boolean): whether the request should be re-executed.

        Returns:
            ephemeris: Ephemeris from file as a Pandas DataFrame
        """

        ephemeris_text = self.get_result_raw_ephemeris(run_number, force_update)
        ephemeris = stk.io.ephemeris_file_data_to_dataframe(ephemeris_text.splitlines())
        return ephemeris

    def __update_results(self, force_update):
        if force_update or self._detailedOutputs is None:
            results = self.get_results()
            self._summary = json.loads(results['outputSummaryJson'])
            self._detailedOutputs = json.loads(results['outputDetailsJson'])


class AdamProcessingService:
    """The ADAM service handling operations related to jobs."""

    def __init__(self, rest):
        self._rest = rest

    def __repr__(self):
        return "Adam Processing Service Class"

    def get_jobs(self, project):
        """Get the jobs within a certain workspace (project).

        Args:
            project (str): The workspace (project) id.

        Returns:
            list: a list of jobs within the workspace (project).
        """
        code, response = self._rest.get(f'/projects/{project}/jobs')
        return response

    def get_job_results(self, project, job_id):
        """Get the job results for a specific job for a specific project.

        Args:
            project (str): The workspace (project) id.
            job_id (str): The job id.

        Returns:
            result (ApsResults): a result object that can be used to query for data about the submitted job
        """
        results_processor = ApsRestServiceResultsProcessor(self._rest, project)

        return BatchPropagationResults(results_processor, job_id)


    def execute_batch_propagation(self,
                                  project,
                                  propagation_params: PropagationParams,
                                  opm_params: OpmParams) -> BatchPropagationResults:
        """Create a new job to run a batch propagation.

        Args:
            project (str): The workspace (project) id.
            propagation_params (PropagationParams): Parameters for the propagation.
            opm_params (OpmParams): Parameters specific to the OPM.

        Returns:
            BatchPropagationResults: a reference to batch propagation object.
        """

        data = self._build_batch_creation_data(propagation_params, opm_params)

        code, response = self._rest.post(f'/projects/{project}/jobs', data)

        if code != 200:
            raise RuntimeError("Server status code: %s; Response: %s" % (code, response))

        results_processor = ApsRestServiceResultsProcessor(self._rest, project)
        job_uuid = response['uuid']

        return BatchPropagationResults(results_processor, job_uuid)

    def _build_batch_creation_data(self, propagation_params, opm_params):
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
            'stopOnImpactDistanceMeters':
                propagation_params.get_stop_on_impact_distance_meters(),
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

        return data


class ApsRestServiceResultsProcessor:
    """AdamProcessingService REST service to check job status and results"""

    def __init__(self, rest, project):
        self._rest = rest
        self._project = project

    def __repr__(self):
        return "Adam Results Processing Class"

    def check_status(self, job_uuid):
        """Check the status of a job.

        Args:
            job_uuid (str): the job id.

        Returns:
            str: the job status.
        """

        code, response = self._rest.get(f'/projects/{self._project}/jobs/{job_uuid}/status')
        if code != 200:
            raise RuntimeError("Server status code: %s; Response: %s" % (code, response))

        return response

    def get_results(self, job_uuid):
        """Get the results of a job.

        Args:
            job_uuid (str): The job id.

        Returns:
            str: The job result, in JSON format::

                {
                    "uuid": id of the result record (string),
                    "jobUuid": job id (string),
                    "outputSummaryJson": the output summary e.g. counts (json),
                    "outputDetailsJson": the output details e.g. final positions (json)
                }
        """

        code, response = self._rest.get(f'/projects/{self._project}/jobs/{job_uuid}/result')
        if code != 200:
            raise RuntimeError("Server status code: %s; Response: %s" % (code, response))

        return response
