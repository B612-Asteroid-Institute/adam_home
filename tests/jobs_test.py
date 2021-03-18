import json
import unittest

import requests
from _pytest.monkeypatch import MonkeyPatch

from adam import MonteCarloResults, ApsRestServiceResultsProcessor
from adam import rest_proxy
from adam.batch_propagation_results import OrbitEventType

TEST_EPHEMERIS = """stk.v.11.0
BEGIN Ephemeris
ScenarioEpoch 04 Oct 2017 00:00:00.000000
CentralBody SUN
CoordinateSystem ICRF
InterpolationMethod HERMITE
InterpolationOrder 5
NumberOfEphemerisPoints 8

EphemerisTimePosVel
0.000000000000e+00 -1.171227408637e+11 7.394528972513e+10 -1.886900039366e+08 -1.805003133491e+04 -2.613130100309e+04 4.269828657914e+01
8.640000000000e+04 -1.186603535533e+11 7.167391360041e+10 -1.849657911829e+08 -1.754196084124e+04 -2.644508876501e+04 4.350736052997e+01
1.728000000000e+05 -1.201538407399e+11 6.937588390458e+10 -1.811724508700e+08 -1.702864879933e+04 -2.674826848501e+04 4.429841985657e+01
2.592000000000e+05 -1.216027602267e+11 6.705212053148e+10 -1.773115500950e+08 -1.651034235804e+04 -2.704076352149e+04 4.507122044427e+01
3.456000000000e+05 -1.230066911904e+11 6.470354970875e+10 -1.733846765215e+08 -1.598728908384e+04 -2.732250389334e+04 4.582553031036e+01
4.320000000000e+05 -1.243652342076e+11 6.233110342436e+10 -1.693934373387e+08 -1.545973675328e+04 -2.759342623225e+04 4.656112940984e+01
5.184000000000e+05 -1.256780112648e+11 5.993571885754e+10 -1.653394582410e+08 -1.492793314949e+04 -2.785347372795e+04 4.727780939013e+01
6.048000000000e+05 -1.269446657501e+11 5.751833781487e+10 -1.612243824298e+08 -1.439212586335e+04 -2.810259606631e+04 4.797537329159e+01


END Ephemeris
"""  # noqa: E501

TEST_STATE_MISS_CSV = """#JobId=fake-job-id
#OrbitEventType=MISS
#TargetBody=EARTH
#ReferenceFrame=ICRF
"runIndex","epoch","x","y","z","xdot","ydot","zdot"
1,"2017-10-11T00:00:00Z",-2.6928320340093042E11,1.6022403675955437E10,-1.8148301336128895E10,-14391.520617284257,-28102.889176245717,47.97595140196477
6,"2017-10-11T00:00:00Z",-2.6927902909850153E11,1.6031095307447838E10,-1.814831862395507E10,-14393.382789069336,-28101.99278765522,47.97271237115176
0,"2017-10-11T00:00:00Z",-2.6928328668619446E11,1.602224049369976E10,-1.8148301392883297E10,-14391.486057970975,-28102.904725877295,47.97580739547921
5,"2017-10-11T00:00:00Z",-2.6927799778258698E11,1.6033161567941444E10,-1.8148302001562466E10,-14393.814114921532,-28101.793804430377,47.96871923716484
3,"2017-10-11T00:00:00Z",-2.69284718478173E11,1.6019298007097527E10,-1.8148304914219505E10,-14390.860984829254,-28103.20139699668,47.97836551868571
2,"2017-10-11T00:00:00Z",-2.6928504396610657E11,1.601857800914592E10,-1.8148301346135536E10,-14390.703095767129,-28103.28187390892,47.97775726810272
4,"2017-10-11T00:00:00Z",-2.6928973541010596E11,1.6008862722833298E10,-1.814828052941111E10,-14388.628730803535,-28104.274203197452,47.981107351489186
0,"2017-10-11T00:00:00Z",-2.6927908342440625E11,1.6030934266210243E10,-1.8148305729730843E10,-14393.34066219399,-28102.018211036244,47.97205789159622
9,"2017-10-11T00:00:00Z",-2.692784995611245E11,1.603216543571679E10,-1.814832390142105E10,-14393.608654252786,-28101.887506819032,47.972511264452265
7,"2017-10-11T00:00:00Z",-2.6928314112298157E11,1.6022503599238663E10,-1.8148293786665375E10,-14391.535819973327,-28102.885062509853,47.973634273398694
8,"2017-10-11T00:00:00Z",-2.6927385149503604E11,1.6041788987288612E10,-1.8148330927382935E10,-14395.656479752755,-28100.907244629958,47.96694967102391
"""  # noqa: E501

class MockResponse(object):
    def __init__(self, text, status_code):
        self.text = text
        self.status_code = status_code

    def json(self):
        return json.loads(self.text)


class JobsTest(unittest.TestCase):

    def setUp(self):
        self.monkeypatch = MonkeyPatch()
        self.fake_project_id = 'fake-project-id'
        self.fake_job_id = 'fake-job-id'
        self.job_output_path = (f'https://storage.googleapis.com/{self.fake_project_id}/output'
                                f'/job/{self.fake_job_id}')
        self.test_rest_proxy = rest_proxy._RestProxyForTest()
        self.api = MonteCarloResults(
            ApsRestServiceResultsProcessor(self.test_rest_proxy, self.fake_project_id),
            self.fake_job_id)

    def test_list_single_ephem_page(self):
        expected_data = {
            'resourceBasePath': f'https://storage.googleapis.com/{self.fake_project_id}',
            'ephemerisResourcePath': [
                f'output/job/{self.fake_job_id}/stk-ephemerides/MISS/run-0-00000-of-00001.e'],
            'nextPageToken': 'fake-page-token'
        }
        self.test_rest_proxy.expect_get(
            f"/projects/{self.fake_project_id}/jobs/{self.fake_job_id}/ephemerides?pageSize=1",
            200, expected_data)

        result = self.api.list_result_ephemerides_files(page_size=1)

        self.assertEqual((200, expected_data), result)

    def test_list_all_ephems(self):
        expected_data = {
            'resourceBasePath': f'https://storage.googleapis.com/{self.fake_project_id}',
            'ephemerisResourcePath': [
                f'output/job/{self.fake_job_id}/stk-ephemerides/MISS/run-0-00000-of-00001.e',
                f'output/job/{self.fake_job_id}/stk-ephemerides/MISS/run-1-00000-of-00001.e',
                f'output/job/{self.fake_job_id}/stk-ephemerides/MISS/run-2-00000-of-00001.e',
                f'output/job/{self.fake_job_id}/stk-ephemerides/MISS/run-3-00000-of-00001.e',
                f'output/job/{self.fake_job_id}/stk-ephemerides/MISS/run-4-00000-of-00001.e',
                f'output/job/{self.fake_job_id}/stk-ephemerides/MISS/run-5-00000-of-00001.e',
                f'output/job/{self.fake_job_id}/stk-ephemerides/MISS/run-6-00000-of-00001.e',
                f'output/job/{self.fake_job_id}/stk-ephemerides/MISS/run-7-00000-of-00001.e'],
        }
        # list_all_ephemerides_files() does not accept a pageSize parameter but uses the default
        # pageSize=100.
        self.test_rest_proxy.expect_get(
            f"/projects/{self.fake_project_id}/jobs/{self.fake_job_id}/ephemerides?pageSize=100",
            200, expected_data)

        result = self.api.list_all_ephemerides_files()

        self.assertEqual((200, expected_data), result)

    def test_get_ephemeris_content(self):
        results_data = {
            'outputSummaryJson': '{}',
            'outputDetailsJson': json.dumps({
                'jobOutputPath': self.job_output_path,
                'ephemeridesDirectoryPrefix': 'stk-ephemerides'
            })
        }

        def mock_get(*args, **kwargs):
            assert args[0].startswith(self.job_output_path)
            return MockResponse(TEST_EPHEMERIS, 200)

        self.monkeypatch.setattr(requests, 'get', mock_get)
        self.test_rest_proxy.expect_get(
            f"/projects/{self.fake_project_id}/jobs/{self.fake_job_id}/result",
            200, results_data)
        result = self.api.get_ephemeris_content(run_index=1)

        self.assertEqual(TEST_EPHEMERIS, result)

    def test_get_ephemeris_content_not_found_raises(self):
        results_data = {
            'outputSummaryJson': '{}',
            'outputDetailsJson': json.dumps({
                'jobOutputPath': self.job_output_path,
                'ephemeridesDirectoryPrefix': 'stk-ephemerides'
            })
        }

        def mock_get(*args, **kwargs):
            assert args[0].startswith(self.job_output_path)
            return MockResponse(TEST_EPHEMERIS, 404)

        self.monkeypatch.setattr(requests, 'get', mock_get)
        self.test_rest_proxy.expect_get(
            f"/projects/{self.fake_project_id}/jobs/{self.fake_job_id}/result",
            200, results_data)

        with self.assertRaises(RuntimeError):
            self.api.get_ephemeris_content(run_index=1, orbit_event_type=OrbitEventType.IMPACT)

    def test_get_ephemeris_content_other_error_raises(self):
        results_data = {
            'outputSummaryJson': '{}',
            'outputDetailsJson': json.dumps({
                'jobOutputPath': (f'https://storage.googleapis.com/{self.fake_project_id}/output'
                                  f'/job/{self.fake_job_id}'),
                'ephemeridesDirectoryPrefix': 'stk-ephemerides'
            })
        }

        def mock_get(*args, **kwargs):
            assert args[0].startswith(self.job_output_path)
            return MockResponse(TEST_EPHEMERIS, 500)

        self.monkeypatch.setattr(requests, 'get', mock_get)
        self.test_rest_proxy.expect_get(
            f"/projects/{self.fake_project_id}/jobs/{self.fake_job_id}/result",
            200, results_data)

        with self.assertRaises(RuntimeError):
            self.api.get_ephemeris_content(run_index=1)

    def test_list_state_files(self):
        results_data = {
            'outputSummaryJson': '{}',
            'outputDetailsJson': json.dumps({
                'jobOutputPath': (f'https://storage.googleapis.com/{self.fake_project_id}/output'
                                  f'/job/{self.fake_job_id}'),
                'states': [
                    'states/MISS-00000-of-00001.csv',
                    'states/IMPACT-00000-of-00001.csv',
                    'states/CLOSE_APPROACH-00000-of-00001.csv'
                ]
            })
        }
        expected_states = [
            (f'https://storage.googleapis.com/{self.fake_project_id}/output'
             f'/job/{self.fake_job_id}/states/MISS-00000-of-00001.csv'),
            (f'https://storage.googleapis.com/{self.fake_project_id}/output'
             f'/job/{self.fake_job_id}/states/IMPACT-00000-of-00001.csv'),
            (f'https://storage.googleapis.com/{self.fake_project_id}/output'
             f'/job/{self.fake_job_id}/states/CLOSE_APPROACH-00000-of-00001.csv'),
        ]
        self.test_rest_proxy.expect_get(
            f"/projects/{self.fake_project_id}/jobs/{self.fake_job_id}/result",
            200, results_data)

        result = self.api.list_state_files()

        self.assertEqual(expected_states, result)

    def test_get_states_file(self):
        results_data = {
            'outputSummaryJson': '{}',
            'outputDetailsJson': json.dumps({
                'jobOutputPath': self.job_output_path,
                'states': [
                    'states/MISS-00000-of-00001.csv',
                    'states/IMPACT-00000-of-00001.csv',
                    'states/CLOSE_APPROACH-00000-of-00001.csv'
                ]
            })
        }

        def mock_get(*args, **kwargs):
            assert args[0].startswith(self.job_output_path)
            return MockResponse(TEST_STATE_MISS_CSV, 200)

        self.monkeypatch.setattr(requests, 'get', mock_get)
        self.test_rest_proxy.expect_get(
            f"/projects/{self.fake_project_id}/jobs/{self.fake_job_id}/result",
            200, results_data)

        result = self.api.get_states_content(OrbitEventType.MISS)

        self.assertEqual(TEST_STATE_MISS_CSV, result)
