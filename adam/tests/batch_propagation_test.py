from adam import BatchPropagation
from adam import BatchPropagations
from adam import PropagationParams
from adam import OpmParams
from adam.adam_objects import AdamObjects

import unittest


class BatchPropagationTest(unittest.TestCase):
    """Unit tests for BatchPropagation object

    """

    def test_get_methods(self):
        opm_params = {'any': 'object1'}
        prop_params = {'any': 'object2'}
        batch_prop = BatchPropagation(prop_params, opm_params)
        self.assertEqual(opm_params, batch_prop.get_opm_params())
        self.assertEqual(prop_params, batch_prop.get_propagation_params())
        self.assertIsNone(batch_prop.get_summary())
        self.assertEqual([], batch_prop.get_final_state_vectors())

        batch_prop.set_summary(
            '1000 2000 3000 4000 5000 6000 7000\n7000 6000 5000 4000 3000 2000 1000')
        # Summary is in meters. State vectors are in km (to match OPM).
        self.assertEqual(
            '1000 2000 3000 4000 5000 6000 7000\n7000 6000 5000 4000 3000 2000 1000',
            batch_prop.get_summary())
        self.assertEqual([[1, 2, 3, 4, 5, 6, 7], [7, 6, 5, 4, 3, 2, 1]],
                         batch_prop.get_final_state_vectors())


class BatchPropagationsTest(unittest.TestCase):
    """Unit tests for BatchPropagations module

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

    def test_create_batch_propagation(self):
        dummy_rest = {'not': 'used'}
        batch_props = BatchPropagations(dummy_rest)

        # Override AdamObjects._insert to just dump out a copy of the data passed.
        passed_data = []

        def store_data(self, data, passed_data=passed_data):
            passed_data.append(data)
            return 'uuid'
        tmp_insert = AdamObjects._insert
        AdamObjects._insert = store_data

        batch_prop = BatchPropagation(
            self.dummy_propagation_params, self.dummy_opm_params)
        batch_props.insert(batch_prop, 'project_uuid')
        uuid = batch_prop.get_uuid()

        self.assertEqual('uuid', uuid)

        self.assertEqual(
            self.dummy_propagation_params.get_description(),
            passed_data[0]['description'])

        passed_prop_params = passed_data[0]['templatePropagationParameters']
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
            BatchPropagationsTest.remove_non_static_fields(
                self.dummy_opm_params.generate_opm()),
            BatchPropagationsTest.remove_non_static_fields(
                passed_prop_params['opmFromString']))

        self.assertEqual('project_uuid', passed_data[0]['project'])

        AdamObjects._insert = tmp_insert

    def test_get_batch_propagation(self):
        dummy_rest = {'not': 'used'}
        batch_props = BatchPropagations(dummy_rest)

        return_data = {
            "uuid": "uuid",
            "templatePropagationParameters": {
                "start_time": "AAA",
                "end_time": "BBB",
                "step_duration_sec": "0",
                "propagator_uuid": "00000000-0000-0000-0000-000000000001",
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
            "summary": "1000 2000 3000 4000 5000 6000 7000\n7000 6000 5000 4000 3000 2000 1000"
        }

        def return_data(self, uuid, return_data=return_data):
            return return_data
        tmp_get_json = AdamObjects._get_json
        AdamObjects._get_json = return_data

        batch_prop = batch_props.get('uuid')

        self.assertEqual('uuid', batch_prop.get_uuid())

        self.assertEqual(self.dummy_propagation_params.get_start_time(),
                         batch_prop.get_propagation_params().get_start_time())
        self.assertEqual(self.dummy_propagation_params.get_end_time(),
                         batch_prop.get_propagation_params().get_end_time())

        self.assertEqual(
            BatchPropagationsTest.remove_non_static_fields(
                self.dummy_opm_params.generate_opm()),
            BatchPropagationsTest.remove_non_static_fields(
                batch_prop.get_opm_params().generate_opm()))

        self.assertEqual('1000 2000 3000 4000 5000 6000 7000\n7000 6000 5000 4000 3000 2000 1000',
                         batch_prop.get_summary())
        self.assertEqual([[1, 2, 3, 4, 5, 6, 7], [7, 6, 5, 4, 3, 2, 1]],
                         batch_prop.get_final_state_vectors())

        AdamObjects._get_json = tmp_get_json


if __name__ == '__main__':
    unittest.main()
