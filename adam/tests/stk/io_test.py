import unittest
import numpy

from adam.stk.io import ephemeris_file_data_to_dataframe

STK_EPHEM_TEXT = '''
stk.v.11.0
BEGIN Ephemeris
ScenarioEpoch 30 Dec 2008 01:14:17.620000
CentralBody SUN
CoordinateSystem ICRF
InterpolationMethod HERMITE
InterpolationOrder 5
NumberOfEphemerisPoints 1097

EphemerisTimePosVel
0.000000000000e+00 9.361973576452e+10 -1.811359048452e+11 -8.103280027661e+10 1.766818009358e+04 1.391375015366e+04 5.222453970115e+03
8.640000000000e+04 9.514184241432e+10 -1.799252621642e+11 -8.057777871925e+10 1.756537425528e+04 1.411039477722e+04 5.310472158010e+03
1.727990000000e+05 9.665496366388e+10 -1.786976273177e+11 -8.011514735716e+10 1.746018049128e+04 1.430708487060e+04 5.398605983415e+03
2.591990000000e+05 9.815889209618e+10 -1.774529970188e+11 -7.964489642865e+10 1.735257327800e+04 1.450380549577e+04 5.486850102770e+03


END Ephemeris
'''  # noqa: E501



class StkIoTest(unittest.TestCase):

    def test_ephemeris_file_data_to_dataframe(self):
        ephemeris = ephemeris_file_data_to_dataframe(STK_EPHEM_TEXT.splitlines())
        self.assertEqual((4, 7), ephemeris.shape)
        self.assertEqual(numpy.datetime64('2008-12-30T01:14:17.62'), ephemeris.values[0][0])
        self.assertAlmostEqual(9.361973576452e+7, ephemeris.values[0][1], 5)
        self.assertAlmostEqual(-198421940.32336992, ephemeris.values[0][2], 5)
        self.assertAlmostEqual(-2294415.6265469044, ephemeris.values[0][3], 5)
        self.assertAlmostEqual(1.766818009358e+01, ephemeris.values[0][4], 11)
        self.assertAlmostEqual(14.842989069313047, ephemeris.values[0][5], 11)
        self.assertAlmostEqual(-0.7430641269076066, ephemeris.values[0][6], 11)
        self.assertEqual(numpy.datetime64('2009-01-02T01:14:16.62'), ephemeris.values[3][0])
