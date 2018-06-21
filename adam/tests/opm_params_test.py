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
        # Remove the CREATION_DATE stamp since that varies.
        opm = "\n".join([line for line in o.generate_opm().splitlines()
                         if not line.startswith('CREATION_DATE')])
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
        # Remove the CREATION_DATE stamp since that varies.
        opm = "\n".join([line for line in o.generate_opm().splitlines()
                         if not line.startswith('CREATION_DATE')])
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


if __name__ == '__main__':
    unittest.main()
