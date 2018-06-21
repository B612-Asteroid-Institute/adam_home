from adam import Batch
from adam import PropagationParams
from adam import OpmParams
from adam.batch import StateSummary
from adam.batch import PropagationResults

from datetime import datetime
import numpy.testing as npt
import unittest


class OpmParamsTest(unittest.TestCase):
    """Unit tests for OpmParams object

    """

    def remove_non_static_fields(self, opm_string):
        # Remove the CREATION_DATE stamp since that varies.
        return "\n".join([line for line in opm_string.splitlines()
                         if not line.startswith('CREATION_DATE')])

    def test_generate_opm(self):
        o = OpmParams({
            'epoch': 'foo',
            'state_vector': [1, 2, 3, 4, 5, 6],
            'keplerian_elements': {
                'semi_major_axis_km': 1,
                'eccentricity': 2,
                'inclination_deg': 3,
                'ra_of_asc_node_deg': 4,
                'arg_of_pericenter_deg': 5,
                'true_anomaly_deg': 6,
                'gm': 7
            },

            'originator': 'a',
            'object_name': 'b',
            'object_id': 'c',

            'center_name': 'EARTH',
            'ref_frame': 'EMEME2000',

            'mass': 1,
            'solar_rad_area': 2,
            'solar_rad_coeff': 3,
            'drag_area': 4,
            'drag_coeff': 5,

            'covariance': [0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11,
                           12, 13, 14, 15, 16, 17, 18, 19, 20],
            'perturbation': 7,
            'hypercube': 'CORNERS',
        })
        expected_opm = """CCSDS_OPM_VERS = 2.0
ORIGINATOR = a
COMMENT Cartesian coordinate system
OBJECT_NAME = b
OBJECT_ID = c
CENTER_NAME = EARTH
REF_FRAME = EMEME2000
TIME_SYSTEM = UTC
EPOCH = foo
X = 1
Y = 2
Z = 3
X_DOT = 4
Y_DOT = 5
Z_DOT = 6
SEMI_MAJOR_AXIS = 1
ECCENTRICITY = 2
INCLINATION = 3
RA_OF_ASC_NODE = 4
ARG_OF_PERICENTER = 5
TRUE_ANOMALY = 6
GM = 7
MASS = 1
SOLAR_RAD_AREA = 2
SOLAR_RAD_COEFF = 3
DRAG_AREA = 4
DRAG_COEFF = 5
CX_X = 0
CY_X = 1
CY_Y = 2
CZ_X = 3
CZ_Y = 4
CZ_Z = 5
CX_DOT_X = 6
CX_DOT_Y = 7
CX_DOT_Z = 8
CX_DOT_X_DOT = 9
CY_DOT_X = 10
CY_DOT_Y = 11
CY_DOT_Z = 12
CY_DOT_X_DOT = 13
CY_DOT_Y_DOT = 14
CZ_DOT_X = 15
CZ_DOT_Y = 16
CZ_DOT_Z = 17
CZ_DOT_X_DOT = 18
CZ_DOT_Y_DOT = 19
CZ_DOT_Z_DOT = 20
USER_DEFINED_ADAM_INITIAL_PERTURBATION = 7 [sigma]
USER_DEFINED_ADAM_HYPERCUBE = CORNERS"""
        opm = self.remove_non_static_fields(o.generate_opm())
        self.maxDiff = None  # Otherwise if the next line fails, we can't see the diff
        self.assertEqual(expected_opm, opm)

    def test_generate_opm_with_defaults(self):
        o = OpmParams({'epoch': 'foo', 'state_vector': [1, 2, 3, 4, 5, 6]})
        expected_opm = """CCSDS_OPM_VERS = 2.0
ORIGINATOR = ADAM_User
COMMENT Cartesian coordinate system
OBJECT_NAME = dummy
OBJECT_ID = 001
CENTER_NAME = SUN
REF_FRAME = ICRF
TIME_SYSTEM = UTC
EPOCH = foo
X = 1
Y = 2
Z = 3
X_DOT = 4
Y_DOT = 5
Z_DOT = 6
MASS = 1000
SOLAR_RAD_AREA = 20
SOLAR_RAD_COEFF = 1
DRAG_AREA = 20
DRAG_COEFF = 2.2"""
        opm = self.remove_non_static_fields(o.generate_opm())
        self.maxDiff = None  # Otherwise if the next line fails, we can't see the diff
        self.assertEqual(expected_opm, opm)

    def test_access_state_vector(self):
        o = OpmParams({'epoch': 'foo', 'state_vector': [1, 2, 3, 4, 5, 6]})
        self.assertEqual([1, 2, 3, 4, 5, 6], o.get_state_vector())
        o.set_state_vector([6, 5, 4, 3, 2, 1])
        self.assertEqual([6, 5, 4, 3, 2, 1], o.get_state_vector())

    def test_required_keys(self):
        with self.assertRaises(KeyError):
            OpmParams({'epoch': 'foo'})

        with self.assertRaises(KeyError):
            OpmParams({'state_vector': []})

        with self.assertRaises(KeyError):
            OpmParams({
                'keplerian_elements': {
                    'semi_major_axis_km': 1,
                    'eccentricity': 2,
                    'inclination_deg': 3,
                    'ra_of_asc_node_deg': 4,
                    'arg_of_pericenter_deg': 5,
                    'true_anomaly_deg': 6,
                    'gm': 7
                }})

        with self.assertRaises(KeyError):
            OpmParams({
                'epoch': 'foo',
                'keplerian_elements': {
                    'semi_major_axis_km': 1,
                    'eccentricity': 2,
                    'inclination_deg': 3,
                    'ra_of_asc_node_deg': 4,
                    'arg_of_pericenter_deg': 5,
                    'true_anomaly_deg': 6,
                    # Missing gm.
                }})

        with self.assertRaises(KeyError):
            OpmParams({
                'epoch': 'foo',
                'keplerian_elements': {
                    'semi_major_axis_km': 1,
                    'eccentricity': 2,
                    'inclination_deg': 3,
                    'ra_of_asc_node_deg': 4,
                    'arg_of_pericenter_deg': 5,
                    'true_anomaly_deg': 6,
                    'gm': 7,
                    'extra what is this': 8
                }})

        # No KeyError with no state vector.
        OpmParams({
            'epoch': 'foo',
            'keplerian_elements': {
                'semi_major_axis_km': 1,
                'eccentricity': 2,
                'inclination_deg': 3,
                'ra_of_asc_node_deg': 4,
                'arg_of_pericenter_deg': 5,
                'true_anomaly_deg': 6,
                'gm': 7
            }})

    def test_invalid_keys(self):
        with self.assertRaises(KeyError):
            OpmParams({'unrecognized': 0})
    
    def test_from_json(self):
        self.maxDiff = 1000
        json1 = {
            "header": {
                "originator": "Test",
                "creation_date": "2018-06-21 16:22:20.550672"
            },
            "metadata": {
                "comments": [
                    "Cartesian coordinate system"
                ],
                "object_name": "TestObj",
                "object_id": "TestObjId",
                "center_name": "SUN",
                "ref_frame": "ICRF",
                "time_system": "UTC"
            },
            "spacecraft": {
                "mass": 500.5,
                "solar_rad_area": 25.2,
                "solar_rad_coeff": 1.2,
                "drag_area": 33.3,
                "drag_coeff": 2.5
            },
            "ccsds_opm_vers": "2.0",
            "state_vector": {
                "epoch": "2018-06-21T16:22:20.550561Z",
                "x": 130347560.13690618,
                "y": -74407287.6018632,
                "z": -35247598.54147063,
                "x_dot": 23.935241263310683,
                "y_dot": 27.146279819258538,
                "z_dot": 10.346605942591514
            }
        }

        expected_opm1 = """CCSDS_OPM_VERS = 2.0
CREATION_DATE = 2018-06-21 16:25:33.374936
ORIGINATOR = Test
COMMENT Cartesian coordinate system
OBJECT_NAME = TestObj
OBJECT_ID = TestObjId
CENTER_NAME = SUN
REF_FRAME = ICRF
TIME_SYSTEM = UTC
EPOCH = 2018-06-21T16:22:20.550561Z
X = 130347560.13690618
Y = -74407287.6018632
Z = -35247598.54147063
X_DOT = 23.935241263310683
Y_DOT = 27.146279819258538
Z_DOT = 10.346605942591514
MASS = 500.5
SOLAR_RAD_AREA = 25.2
SOLAR_RAD_COEFF = 1.2
DRAG_AREA = 33.3
DRAG_COEFF = 2.5"""

        expected_opm1 = self.remove_non_static_fields(expected_opm1)
        opm_params1 = OpmParams.fromJsonResponse(json1)
        actual_opm1 = self.remove_non_static_fields(opm_params1.generate_opm())

        self.assertEqual(expected_opm1, actual_opm1)

        json2 = {
            "header": {
                "originator": "Test",
                "creation_date": "2018-06-21 17:43:20.984533"
            },
            "metadata": {
                "comments": [
                "Cartesian coordinate system"
                ],
                "object_name": "TestObj",
                "object_id": "TestObjId",
                "center_name": "SUN",
                "ref_frame": "ICRF",
                "time_system": "UTC"
            },
            "spacecraft": {
                "mass": 500.5,
                "solar_rad_area": 25.2,
                "solar_rad_coeff": 1.2,
                "drag_area": 33.3,
                "drag_coeff": 2.5
            },
            "covariance": {
                "cx_x": 0.0003331349476038534,
                "cy_x": 0.0004618927349220216,
                "cy_y": 0.0006782421679971363,
                "cz_x": -0.0003070007847730449,
                "cz_y": -0.0004221234189514228,
                "cz_z": 0.0003231931992380369,
                "cx_dot_x": -3.34936503392263e-07,
                "cx_dot_y": -4.686084221046758e-07,
                "cx_dot_z": 2.484949578400095e-07,
                "cx_dot_x_dot": 4.29602280558729e-10,
                "cy_dot_x": -2.211832501084875e-07,
                "cy_dot_y": -2.864186892102733e-07,
                "cy_dot_z": 1.798098699846038e-07,
                "cy_dot_x_dot": 2.608899201686016e-10,
                "cy_dot_y_dot": 1.767514756338532e-10,
                "cz_dot_x": -3.041346050686871e-07,
                "cz_dot_y": -4.989496988610662e-07,
                "cz_dot_z": 3.540310904497689e-07,
                "cz_dot_x_dot": 1.86926319295459e-10,
                "cz_dot_y_dot": 1.008862586240695e-10,
                "cz_dot_z_dot": 6.2244443386355e-10
            },
            "adam_fields": [
                {
                "key": "INITIAL_PERTURBATION",
                "value": "3"
                },
                {
                "key": "HYPERCUBE",
                "value": "FACES"
                }
            ],
            "ccsds_opm_vers": "2.0",
            "state_vector": {
                "epoch": "2018-06-21T17:43:20.984304Z",
                "x": 130347560.13690618,
                "y": -74407287.6018632,
                "z": -35247598.54147063,
                "x_dot": 23.935241263310683,
                "y_dot": 27.146279819258538,
                "z_dot": 10.346605942591514
            }
        }

        expected_opm2 = """CCSDS_OPM_VERS = 2.0
CREATION_DATE = 2018-06-21 17:43:20.984372
ORIGINATOR = Test
COMMENT Cartesian coordinate system
OBJECT_NAME = TestObj
OBJECT_ID = TestObjId
CENTER_NAME = SUN
REF_FRAME = ICRF
TIME_SYSTEM = UTC
EPOCH = 2018-06-21T17:43:20.984304Z
X = 130347560.13690618
Y = -74407287.6018632
Z = -35247598.54147063
X_DOT = 23.935241263310683
Y_DOT = 27.146279819258538
Z_DOT = 10.346605942591514
MASS = 500.5
SOLAR_RAD_AREA = 25.2
SOLAR_RAD_COEFF = 1.2
DRAG_AREA = 33.3
DRAG_COEFF = 2.5
CX_X = 0.0003331349476038534
CY_X = 0.0004618927349220216
CY_Y = 0.0006782421679971363
CZ_X = -0.0003070007847730449
CZ_Y = -0.0004221234189514228
CZ_Z = 0.0003231931992380369
CX_DOT_X = -3.34936503392263e-07
CX_DOT_Y = -4.686084221046758e-07
CX_DOT_Z = 2.484949578400095e-07
CX_DOT_X_DOT = 4.29602280558729e-10
CY_DOT_X = -2.211832501084875e-07
CY_DOT_Y = -2.864186892102733e-07
CY_DOT_Z = 1.798098699846038e-07
CY_DOT_X_DOT = 2.608899201686016e-10
CY_DOT_Y_DOT = 1.767514756338532e-10
CZ_DOT_X = -3.041346050686871e-07
CZ_DOT_Y = -4.989496988610662e-07
CZ_DOT_Z = 3.540310904497689e-07
CZ_DOT_X_DOT = 1.86926319295459e-10
CZ_DOT_Y_DOT = 1.008862586240695e-10
CZ_DOT_Z_DOT = 6.2244443386355e-10
USER_DEFINED_ADAM_INITIAL_PERTURBATION = 3 [sigma]
USER_DEFINED_ADAM_HYPERCUBE = FACES"""

        expected_opm2 = self.remove_non_static_fields(expected_opm2)
        opm_params2 = OpmParams.fromJsonResponse(json2)
        actual_opm2 = self.remove_non_static_fields(opm_params2.generate_opm())

        self.assertEqual(expected_opm2, actual_opm2)

        json3 = {
            "header": {
                "originator": "Test",
                "creation_date": "2018-06-21 17:56:58.406867"
            },
            "metadata": {
                "comments": [
                "Cartesian coordinate system"
                ],
                "object_name": "TestObj",
                "object_id": "TestObjId",
                "center_name": "SUN",
                "ref_frame": "ICRF",
                "time_system": "UTC"
            },
            "keplerian": {
                "eccentricity": 0.5355029800000188,
                "inclination": 23.439676743246295,
                "gm": 132712440041.9394,
                "semi_major_axis": 313072891.38037175,
                "mean_motion": 0.0,
                "ra_of_asc_node": 359.9942693176405,
                "arg_of_pericenter": 328.5584374618295,
                "true_anomaly": -127.01778914927144,
                "mean_anomaly": 0.0
            },
            "spacecraft": {
                "mass": 500.5,
                "solar_rad_area": 25.2,
                "solar_rad_coeff": 1.2,
                "drag_area": 33.3,
                "drag_coeff": 2.5
            },
            "ccsds_opm_vers": "2.0",
            "state_vector": {
                "epoch": "2018-06-21T17:56:58.406556Z",
                "x": 0.0,
                "y": 0.0,
                "z": 0.0,
                "x_dot": 0.0,
                "y_dot": 0.0,
                "z_dot": 0.0
            }
        }

        expected_opm3 = """CCSDS_OPM_VERS = 2.0
CREATION_DATE = 2018-06-21 17:56:58.406717
ORIGINATOR = Test
COMMENT Cartesian coordinate system
OBJECT_NAME = TestObj
OBJECT_ID = TestObjId
CENTER_NAME = SUN
REF_FRAME = ICRF
TIME_SYSTEM = UTC
EPOCH = 2018-06-21T17:56:58.406556Z
X = 0.0
Y = 0.0
Z = 0.0
X_DOT = 0.0
Y_DOT = 0.0
Z_DOT = 0.0
SEMI_MAJOR_AXIS = 313072891.38037175
ECCENTRICITY = 0.5355029800000188
INCLINATION = 23.439676743246295
RA_OF_ASC_NODE = 359.9942693176405
ARG_OF_PERICENTER = 328.5584374618295
TRUE_ANOMALY = -127.01778914927144
GM = 132712440041.9394
MASS = 500.5
SOLAR_RAD_AREA = 25.2
SOLAR_RAD_COEFF = 1.2
DRAG_AREA = 33.3
DRAG_COEFF = 2.5"""

        expected_opm3 = self.remove_non_static_fields(expected_opm3)
        opm_params3 = OpmParams.fromJsonResponse(json3)
        actual_opm3 = self.remove_non_static_fields(opm_params3.generate_opm())

        self.assertEqual(expected_opm3, actual_opm3)


if __name__ == '__main__':
    unittest.main()
