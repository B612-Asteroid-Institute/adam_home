import json
import sys
import time
import urllib
from enum import Enum


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
        return self._rp.check_status(self._job_uuid)['status']

    # TODO make this work
    def wait_for_complete(self, max_wait_sec=60, print_waiting = False):
        sleep_time_sec = 0.1
        t0 = time.clock()
        status = self.check_status()
        last_status = ''
        while status != 'COMPLETED':
            if print_waiting:
                if last_status != status:
                    print(status)
                sys.stdout.write('.')
                sys.stdout.flush()
            if (time.clock() - t0) > max_wait_sec:
                raise RuntimeError(f'Computation has exceeded desired wait period of {max_wait_sec} sec.')
            last_status = status
            time.sleep(sleep_time_sec)
            status = self.check_status()

    def get_results(self, force_update=True):
        if force_update or self._results is None:
            results = self._rp.get_results(self._job_uuid)
            self._results = results

        return self._results


class BatchPropagationResults(ApsResults):
    class PositionOrbitType(Enum):
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
        total = misses + close_approaches + impacts
        probability = impacts / total
        return {
            'misses': misses,
            'close_approach': close_approaches,
            'impacts': impacts,
            'total': total,
            'pc': probability
        }

    def get_final_positions(self, position_orbit_type: PositionOrbitType, force_update=False):
        self.__update_results(force_update)
        position_type_string = position_orbit_type.value
        final_positions = self._detailedOutputs['finalPositionsByType'].get(position_type_string)
        if final_positions is None:
            return []
        positions = final_positions['finalPosition']
        return_data = list(map(lambda p: [p['x'], p['y'], p['z']], positions))
        return return_data

    def get_result_ephemeris_count(self, force_update=False):
        self.__update_results(force_update)
        ephemeris = self._detailedOutputs.get('ephemeris')
        if ephemeris is None:
            return 0
        ephemeris_objects = ephemeris.get('ephemerisResourcePath')
        if ephemeris_objects is None:
            return 0
        return len(ephemeris_objects)

    def get_result_ephemeris(self, run_number, force_update=False):
        self.__update_results(force_update)
        ephemeris = self._detailedOutputs['ephemeris']
        ephemeris_resource_name = ephemeris['ephemerisResourcePath'][run_number]
        base_url = ephemeris['resourceBasePath']
        if not base_url.endswith('/'):
            base_url = base_url + '/'
        url = urllib.parse.urljoin(base_url, ephemeris_resource_name)
        print(url)
        with urllib.request.urlopen(url) as response:
            return response.read().decode('utf-8')

    def __update_results(self, force_update):
        if force_update or self._detailedOutputs is None:
            results = self.get_results()
            self._summary = json.loads(results['outputSummaryJson'])
            self._detailedOutputs = json.loads(results['outputDetailsJson'])


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

        return BatchPropagationResults(results_processor, job_uuid)

    def _build_batch_creation_data(self, propagation_params, opm_params):
        propagation_params_json = {
            'start_time': propagation_params.get_start_time(),
            'end_time': propagation_params.get_end_time(),
            'description': propagation_params.get_description(),
            'step_duration_sec': propagation_params.get_step_size(),
            'propagator_uuid': propagation_params.get_propagator_uuid(),
            'project': propagation_params.get_project_uuid(),
            'monteCarloDraws': propagation_params.get_monte_carlo_draws(),
            'propagationType': propagation_params.get_propagation_type(),
            'stopOnImpact': propagation_params.get_stop_on_impact(),
            'cartesianSigma': propagation_params.get_cartesian_sigma(),
            'stopOnCloseApproach': propagation_params.get_stop_on_close_approach(),
            'stopOnImpactDistanceMeters': propagation_params.get_stop_on_impact_distance_meters(),
            'stopOnCloseApproachAfterEpoch': propagation_params.get_stop_on_close_approach_after_epoch(),
            'closeApproachRadiusFromTargetMeters': propagation_params.get_close_approach_radius_from_target_meters()
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



