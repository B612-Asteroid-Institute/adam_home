from adam import PropagationParams
from adam import OpmParams
from adam.adam_objects import AdamObjects
from adam.targeted_propagation import TargetedPropagation
from adam.targeted_propagation import TargetedPropagations
from adam.targeted_propagation import TargetingParams

import unittest


class TargetedPropagationTest(unittest.TestCase):
    """Unit tests for TargetedPropagation object

    """

    def test_get_and_set_methods(self):
        opm_params = {'any': 'object1'}
        prop_params = {'any': 'object2'}
        targeting_params = {'any': 'object3'}
        targeted_prop = TargetedPropagation(prop_params, opm_params, targeting_params)
        self.assertEqual(opm_params, targeted_prop.get_opm_params())
        self.assertEqual(prop_params, targeted_prop.get_propagation_params())
        self.assertEqual(targeting_params, targeted_prop.get_targeting_params())
        self.assertIsNone(targeted_prop.get_ephemeris())
        self.assertIsNone(targeted_prop.get_maneuver())

        targeted_prop.set_ephemeris('ephemeris')
        self.assertEqual('ephemeris', targeted_prop.get_ephemeris())
        targeted_prop.set_maneuver([1, 2, 3])
        self.assertEqual([1, 2, 3], targeted_prop.get_maneuver())


class TargetingParamsTest(unittest.TestCase):
    """Unit tests for TargetingParams object

    """

    def test_get_methods(self):
        p = TargetingParams({
            'target_distance_from_earth': 123,
            'tolerance': 321,
            'run_nominal_only': True
        })
        self.assertEqual(123, p.get_target_distance_from_earth())
        self.assertEqual(321, p.get_tolerance())
        self.assertEqual(True, p.get_run_nominal_only())

    def test_defaults(self):
        p = TargetingParams({'target_distance_from_earth': 123})
        self.assertEqual(1.0, p.get_tolerance())
        self.assertEqual(False, p.get_run_nominal_only())

    def test_required_keys(self):
        with self.assertRaises(KeyError):
            # Only target_distance_from_earth is required.
            TargetingParams({})

    def test_invalid_keys(self):
        with self.assertRaises(KeyError):
            TargetingParams({'unrecognized': 0})

    def test_from_json(self):
        json = {
            'targetDistanceFromEarth': 123,
            'tolerance': 321,
            'runNominalOnly': True,
        }
        p = TargetingParams.fromJsonResponse(json)
        self.assertEqual(123, p.get_target_distance_from_earth())
        self.assertEqual(321, p.get_tolerance())
        self.assertEqual(True, p.get_run_nominal_only())


class TargetedPropagationsTest(unittest.TestCase):
    """Unit tests for TargetedPropagations module

    """

    @classmethod
    def remove_non_static_fields(cls, opm_string):
        # Remove the CREATION_DATE stamp since that varies.
        return "\n".join([line for line in opm_string.splitlines()
                          if not line.startswith('CREATION_DATE')])

    dummy_propagation_params = PropagationParams({
        'start_time': 'AAA',
        'end_time': 'BBB',
    })
    dummy_opm_params = OpmParams({
        'epoch': 'DDD',
        'state_vector': [1.0, 2.0, 3.0, 4.0, 5.0, 6.0]
    })
    dummy_targeting_params = TargetingParams({
        'target_distance_from_earth': 123
    })
    dummy_opm_params_as_api_response = {
        "header": {
            "originator": "ADAM_User",
            "creation_date": "2018-06-21 19:13:27.261813"
        },
        "metadata": {
            "comments": [
                "Cartesian coordinate system"
            ],
            "object_name": "dummy",
            "object_id": "001",
            "center_name": "SUN",
            "ref_frame": "ICRF",
            "time_system": "UTC"
        },
        "spacecraft": {
            "mass": 1000.0,
            "solar_rad_area": 20.0,
            "solar_rad_coeff": 1.0,
            "drag_area": 20.0,
            "drag_coeff": 2.2
        },
        "ccsds_opm_vers": "2.0",
        "state_vector": {
            "epoch": "DDD",
            "x": 1.0,
            "y": 2.0,
            "z": 3.0,
            "x_dot": 4.0,
            "y_dot": 5.0,
            "z_dot": 6.0
        }
    }

    def test_insert_targeted_propagation(self):
        dummy_rest = {'not': 'used'}
        targeted_props = TargetedPropagations(dummy_rest)

        # Override AdamObjects._insert to just dump out a copy of the data passed.
        passed_data = []

        def store_data(self, data, passed_data=passed_data):
            passed_data.append(data)
            return 'uuid'
        tmp_insert = AdamObjects._insert
        AdamObjects._insert = store_data

        prop = TargetedPropagation(
            self.dummy_propagation_params,
            self.dummy_opm_params,
            self.dummy_targeting_params)
        targeted_props.insert(prop, 'project_uuid')
        uuid = prop.get_uuid()

        self.assertEqual('uuid', uuid)

        self.assertEqual(
            self.dummy_propagation_params.get_description(),
            passed_data[0]['description'])

        passed_prop_params = passed_data[0]['initialPropagationParameters']
        self.assertEqual(
            self.dummy_propagation_params.get_start_time(),
            passed_prop_params['start_time'])
        self.assertEqual(
            self.dummy_propagation_params.get_end_time(),
            passed_prop_params['end_time'])
        self.assertEqual(
            self.dummy_propagation_params.get_propagator_uuid(),
            passed_prop_params['propagator_uuid'])
        self.assertEqual(
            self.dummy_propagation_params.get_step_size(),
            passed_prop_params['step_duration_sec'])

        self.assertEqual(
            TargetedPropagationsTest.remove_non_static_fields(
                self.dummy_opm_params.generate_opm()),
            TargetedPropagationsTest.remove_non_static_fields(
                passed_prop_params['opmFromString']))

        passed_targeting_params = passed_data[0]['targetingParameters']
        self.assertEqual(self.dummy_targeting_params.get_target_distance_from_earth(),
                         passed_targeting_params['targetDistanceFromEarth'])
        self.assertEqual(self.dummy_targeting_params.get_tolerance(),
                         passed_targeting_params['tolerance'])
        self.assertEqual(self.dummy_targeting_params.get_run_nominal_only(),
                         passed_targeting_params['runNominalOnly'])

        self.assertEqual('project_uuid', passed_data[0]['project'])

        AdamObjects._insert = tmp_insert

    def test_get_targeted_propagation(self):
        dummy_rest = {'not': 'used'}
        targeted_props = TargetedPropagations(dummy_rest)

        return_data = {
            "uuid": "uuid",
            "initialPropagationParameters": {
                "start_time": "AAA",
                "end_time": "BBB",
                "step_duration_sec": "0",
                "propagator_uuid": "00000000-0000-0000-0000-000000000001",
                "executor": "stk",
                "opm": {
                    "header": {
                        "originator": "ADAM_User",
                        "creation_date": "2018-06-21 19:28:47.304102"
                    },
                    "metadata": {
                        "comments": [
                            "Cartesian coordinate system"
                        ],
                        "object_name": "dummy",
                        "object_id": "001",
                        "center_name": "SUN",
                        "ref_frame": "ICRF",
                        "time_system": "UTC"
                    },
                    "spacecraft": {
                        "mass": 1000.0,
                        "solar_rad_area": 20.0,
                        "solar_rad_coeff": 1.0,
                        "drag_area": 20.0,
                        "drag_coeff": 2.2
                    },
                    "ccsds_opm_vers": "2.0",
                    "state_vector": {
                        "epoch": "DDD",
                        "x": 1.0,
                        "y": 2.0,
                        "z": 3.0,
                        "x_dot": 4.0,
                        "y_dot": 5.0,
                        "z_dot": 6.0
                    }
                }
            },
            "targetingParameters": {
                "targetDistanceFromEarth": 123.0,
                "tolerance": 1.0,
                "runNominalOnly": False
            },
            "description": "Created by test at 2018-06-21 19:28:47.303980Z",
            "maneuverX": 0.0,
            "maneuverY": 0.0,
            "maneuverZ": 0.0
        }

        def return_data(self, uuid, return_data=return_data):
            return return_data
        tmp_get_json = AdamObjects._get_json
        AdamObjects._get_json = return_data

        targeted_prop = targeted_props.get('uuid')

        self.assertEqual('uuid', targeted_prop.get_uuid())

        self.assertEqual(self.dummy_propagation_params.get_start_time(),
                         targeted_prop.get_propagation_params().get_start_time())
        self.assertEqual(self.dummy_propagation_params.get_end_time(),
                         targeted_prop.get_propagation_params().get_end_time())

        self.assertEqual(
            TargetedPropagationsTest.remove_non_static_fields(
                self.dummy_opm_params.generate_opm()),
            TargetedPropagationsTest.remove_non_static_fields(
                targeted_prop.get_opm_params().generate_opm()))

        self.assertEqual(self.dummy_targeting_params.get_target_distance_from_earth(),
                         targeted_prop.get_targeting_params().get_target_distance_from_earth())

        self.assertIsNone(targeted_prop.get_ephemeris())
        self.assertEqual([0, 0, 0], targeted_prop.get_maneuver())

        AdamObjects._get_json = tmp_get_json


if __name__ == '__main__':
    unittest.main()
