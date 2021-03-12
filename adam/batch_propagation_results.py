"""
    batch_propagation_results.py
"""

import json
import time
import urllib
import datetime
from enum import Enum

import numpy as np
from dateutil import parser as dateparser

from adam import Project, Job, stk, ApsRestServiceResultsProcessor


class ResultsService(object):
    """Module for managing results interactions.

    """

    def __init__(self, rest):
        """Initialize the Results Service API client.

        Args:
            rest (RestProxy): a RestProxy that makes calls to the ADAM API.
        """
        self._rest = rest

    def get_monte_carlo_results(self, job):
        """Get the job results for a specific job for a specific project.

        Args:
            job (Job): The job id or Job object that has the Job ID in it

        Returns:
            result (ApsResults): a result object that can be used to query for data about the
            submitted job
        """
        results_processor = ApsRestServiceResultsProcessor(self._rest, job.get_project_id())

        return MonteCarloResults(results_processor, job.get_uuid())


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

        sleep_time_sec = 10.0
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


class MonteCarloResults(ApsResults):
    """API for retrieving propagation results and summaries"""

    class PositionOrbitType(Enum):
        """The type of orbit position in relation to a target body."""
        MISS = 'MISS'
        CLOSE_APPROACH = 'CLOSE_APPROACH'
        IMPACT = 'IMPACT'

    @classmethod
    def fromRESTwithRawIds(cls, rest, project_uuid, job_uuid):
        results_processor = ApsRestServiceResultsProcessor(rest, project_uuid)
        return MonteCarloResults(results_processor, job_uuid)

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
            summary (MonteCarloSummary)

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
        return MonteCarloSummary(misses=misses, close_approach=close_approaches, impacts=impacts, pc=probability)

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
        return_data = list(
            map(lambda p: [np.datetime64(dateparser.parse(p['epoch'])), p['x'], p['y'], p['z']],
                positions))
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


class MonteCarloSummary(object):
    def __init__(self, misses, close_approach, impacts, pc):
        self._misses = misses
        self._close_approach = close_approach
        self._impacts = impacts
        self._pc = pc

    def __repr__(self):
        return (
            f"MonteCarloSummary(misses={self._misses}, close_approaches={self._close_approach}, "
            f"impacts={self._impacts}, pc={self._pc})"
        )

    def get_misses(self):
        return self._misses

    def get_close_approaches(self):
        return self._close_approach

    def get_impacts(self):
        return self._impacts

    def get_pc(self):
        return self._pc


