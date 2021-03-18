"""
    batch_propagation_results.py
"""
import enum
import io
import json
import time
import urllib
from typing import List, Optional, Dict

import numpy as np
import pandas as pd
import requests
from dateutil import parser as dateparser

from adam import stk, ApsRestServiceResultsProcessor, AuthenticatingRestProxy, RestRequests


class OrbitEventType(enum.Enum):
    """Events of interest, from an orbit propagation.

    This is the same as PositionOrbitType, but with updated naming to be consistent with the
    server-side enum.
    """

    MISS = 'MISS'
    CLOSE_APPROACH = 'CLOSE_APPROACH'
    IMPACT = 'IMPACT'


class ResultsClient(object):
    """Module for managing results interactions.

    """

    def __init__(self, rest=AuthenticatingRestProxy(RestRequests())):
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
            result (MonteCarloResults): a result object that can be used to query for data about the
            submitted job
        """
        results_processor = ApsRestServiceResultsProcessor(self._rest,
                                                           job.get_project_id())

        return MonteCarloResults(results_processor, job.get_uuid())


class ApsResults:
    """API for retrieving job details"""

    @classmethod
    def _from_rest_with_raw_ids(cls, rest, project_uuid, job_uuid):
        results_processor = ApsRestServiceResultsProcessor(rest, project_uuid)
        return ApsResults(results_processor, job_uuid)

    def __init__(self, client, job_uuid):
        self._rp = client
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

    class PositionOrbitType(enum.Enum):
        """The type of orbit position in relation to a target body."""
        MISS = 'MISS'
        CLOSE_APPROACH = 'CLOSE_APPROACH'
        IMPACT = 'IMPACT'

    @classmethod
    def _from_rest_with_raw_ids(cls, rest, project_uuid, job_uuid):
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

        self._update_results(force_update)
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

        denominator = misses + impacts
        probability = 0
        if denominator > 0:
            probability = impacts / (misses + impacts)
        return MonteCarloSummary(
            misses=misses,
            close_approach=close_approaches,
            impacts=impacts,
            pc=probability
        )

    def get_final_positions(self, position_orbit_type: PositionOrbitType, force_update=False):
        """Get the final positions of all propagated objects in the job.

        Args:
            position_orbit_type (PositionOrbitType): the type of orbit position to filter.
            force_update (boolean): whether the request should be re-executed.

        Returns:
            list: A list of the final orbit positions, filtered by the position_orbit_type.
        """

        self._update_results(force_update)
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

        self._update_results(force_update)
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

        self._update_results(force_update)
        ephemeris = self._detailedOutputs['ephemeris']
        ephemeris_resource_name = ephemeris['ephemerisResourcePath'][run_number]
        base_url = ephemeris['resourceBasePath']
        if not base_url.endswith('/'):
            base_url = base_url + '/'
        url = urllib.parse.urljoin(base_url, ephemeris_resource_name)
        with urllib.request.urlopen(url) as response:
            return response.read().decode('utf-8')

    def get_result_ephemeris(self, run_number, force_update=False) -> pd.DataFrame:
        """Get an ephemeris for a particular run in the batch as a Pandas DataFrame

        Args:
            force_update (boolean): whether the request should be re-executed.

        Returns:
            ephemeris: Ephemeris from file as a Pandas DataFrame
        """

        ephemeris_text = self.get_result_raw_ephemeris(run_number, force_update)
        ephemeris = stk.io.ephemeris_file_data_to_dataframe(ephemeris_text.splitlines())
        return ephemeris

    def list_result_ephemerides_files(
            self, page_size: int = 100, page_token: str = None) -> Dict:
        """List one page of ephemerides files from the job results.

        Args:
            page_size (int): The size of the results to retrieve
            page_token (str): Which page to retrieve

        Returns:
            Dict containing the ephemerides paths
        """
        params = {}
        if page_size < 0 or page_size > 100:
            page_size = 100
        params['pageSize'] = page_size
        if page_token:
            params['pageToken'] = page_token
        ephs = self._rp._rest.get(
            f'/projects/{self._rp._project}/jobs/{self._job_uuid}'
            f'/ephemerides?{urllib.parse.urlencode(params)}')
        return ephs

    def list_all_ephemerides_files(self) -> Dict:
        """Lists all ephemerides from the job results.

        Performs all the paging without user intervention.

        Returns:
            Dict containing the ephemerides paths
        """
        ephs = self.list_result_ephemerides_files()
        while 'nextPageToken' in ephs:
            next_page_token = ephs['nextPageToken']
            _, e = self.list_result_ephemerides_files(page_token=next_page_token)
            ephs['ephemerisResourcePath'].extend(e['ephemerisResourcePath'])
        return ephs

    def get_ephemeris_content(self, run_index: int,
                              orbit_event_type: Optional[OrbitEventType] = None,
                              force_update: bool = False) -> str:
        """Retrieves an ephemeris file and returns the text content.

        This doesn't use the ADAM REST wrapper, since that class assumes the response will be in
        json, and this is an ephemeris. For now, it's fine to use `requests` directly.

        Args:
            run_index (int): The run number of the ephemeris
            orbit_event_type (Optional[OrbitEventType]): The OrbitEventType of the ephemeris
            force_update (bool): Whether the results should be reloaded from the server

        Returns:
            str: The ephemeris content, as a string.
        """

        self._update_results(force_update)
        file_prefix = (f"{self._detailedOutputs['jobOutputPath']}"
                       f"/{self._detailedOutputs['ephemeridesDirectoryPrefix']}")
        eph_name = f'run-{run_index}-00000-of-00001.e'
        # Retrieve all the file paths, ignoring 404s. Ephems are supposed to only map to either
        # MISS or IMPACT. If the orbit_event_type isn't provided, then brute-force try to get the
        # the file path for both MISS and IMPACT. We wouldn't know which one exists without
        # listing the bucket, and sometimes that might just be too much to wade through.
        file_paths = []
        if orbit_event_type is None:
            file_paths.append(f"{file_prefix}/{OrbitEventType.MISS.value}/{eph_name}")
            file_paths.append(f"{file_prefix}/{OrbitEventType.IMPACT.value}/{eph_name}")
        else:
            file_paths.append(f"{file_prefix}/{orbit_event_type.value}/{eph_name}")
        responses = [r for r in [requests.get(f) for f in file_paths] if r.status_code != 404]
        # There should just be 1 successful response (assuming the orbit_event_type and run_index
        # are correct)
        if responses and responses[0].status_code < 300:
            return responses[0].text
        resp_tuples = [(r.status_code, r.text) for r in responses]
        raise RuntimeError(f'There was a problem getting the ephemeris.\n{resp_tuples}')

    def get_ephemeris_as_dataframe(self, run_index: int,
                                   orbit_event_type: Optional[
                                       OrbitEventType] = None) -> pd.DataFrame:
        """Get ephemeris content and convert it to a pandas DataFrame.

        Args:
            run_index (int): The run number of the ephemeris
            orbit_event_type (Optional[OrbitEventType]): The OrbitEventType of the ephemeris

        Returns:
            pandas.DataFrame: The STK ephemeris in a pandas DataFrame.
        """
        ephem_text = self.get_ephemeris_content(run_index=run_index,
                                                orbit_event_type=orbit_event_type)
        return stk.io.ephemeris_file_data_to_dataframe(ephem_text.splitlines())

    def list_state_files(self, force_update: bool = False) -> List[str]:
        """List the state files generated during the propagation.

        Args:
            force_update (bool): Whether the results should be reloaded from the server

        Returns:
            list (str): a list of URL strings for the state files.
        """
        self._update_results(force_update)
        state_files = self._detailedOutputs['states']
        file_prefix = self._detailedOutputs['jobOutputPath']
        return [f"{file_prefix}/{s}" for s in state_files]

    def get_states_content(self, orbit_event_type: OrbitEventType,
                           force_update: bool = False) -> str:
        """Retrieves a states file and returns the content as a string.

        This doesn't use the ADAM REST wrapper, since that class assumes the response will be in
        json, and this is an ephemeris. For now, it's fine to use `requests` directly.

        Args:
            orbit_event_type (OrbitEventType): The type of OrbitEvent for which to retrieve the
                states output.
            force_update (bool): Whether the results should be reloaded from the server

        Returns:
            str: The content of the state file.
        """
        self._update_results(force_update)
        state_files = [f"{self._detailedOutputs['jobOutputPath']}/{f}" for f in
                       self._detailedOutputs['states'] if
                       f'states/{orbit_event_type.value}' in f]
        if not state_files:
            return ''
        response = requests.get(state_files[0])
        if response.status_code >= 300:
            raise RuntimeError(
                f"Unable to retrieve state file: HTTP status code={response.status_code}, "
                f"response={response.text}")
        return response.text

    def get_states_dataframe(self, orbit_event_type: OrbitEventType,
                             force_update: bool = False) -> pd.DataFrame:
        """Retrieves a states file and returns it as a pandas DataFrame.

        This doesn't use the ADAM REST wrapper, since that class assumes the response will be in
        json, and this is an ephemeris. For now, it's fine to use `requests` directly.

        Args:
            orbit_event_type (OrbitEventType): The type of OrbitEvent for which to retrieve the
                states output.
            force_update (bool): Whether the results should be reloaded from the server

        Returns:
            pandas.DataFrame: The STK ephemeris in a pandas DataFrame.
        """
        states_content = self.get_states_content(orbit_event_type, force_update)
        if states_content:
            return pd.read_csv(io.StringIO(states_content), comment='#', index_col=0).sort_values(
                'runIndex')
        return pd.DataFrame()

    def _update_results(self, force_update):
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
