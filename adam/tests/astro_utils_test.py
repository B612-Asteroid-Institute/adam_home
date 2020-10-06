import unittest
import astro_utils

JPL_ECLIPTIC_X = -3.027985514061421E+08
JPL_ECLIPTIC_Y = 2.855686074583623E+08
JPL_ECLIPTIC_Z = 1.678012767460957E+07
JPL_ECLIPTIC_VX = -1.238827604421024E+01
JPL_ECLIPTIC_VY = -1.047525790511110E+01
JPL_ECLIPTIC_VZ = -1.218174336421540E+00

ICRF_X = -3.027985514061421E+08
ICRF_Y = 2.553293233705423E+08
ICRF_Z = 1.289881346389093E+08
ICRF_VX = -1.238827604421024E+01
ICRF_VY = -9.126299300516822E+00
ICRF_VZ = -5.284471399288181E+00


class AstroUtilsTest(unittest.TestCase):

    def test_icrf_to_ecliptic(self):
        ecliptic_pos_vel = astro_utils.icrf_to_jpl_ecliptic(ICRF_X, ICRF_Y, ICRF_Z, ICRF_VX, ICRF_VY, ICRF_VZ)
        self.assertAlmostEqual(JPL_ECLIPTIC_X, ecliptic_pos_vel[0],8)
        self.assertAlmostEqual(JPL_ECLIPTIC_Y, ecliptic_pos_vel[1],6)
        self.assertAlmostEqual(JPL_ECLIPTIC_Z, ecliptic_pos_vel[2],6)

        self.assertAlmostEqual(JPL_ECLIPTIC_VX, ecliptic_pos_vel[3],15)
        self.assertAlmostEqual(JPL_ECLIPTIC_VY, ecliptic_pos_vel[4],14)
        self.assertAlmostEqual(JPL_ECLIPTIC_VZ, ecliptic_pos_vel[5],14)

    def test_ecliptic_to_icrf(self):
        icrf_pos_vel = astro_utils.jpl_ecliptic_to_icrf(JPL_ECLIPTIC_X, JPL_ECLIPTIC_Y, JPL_ECLIPTIC_Z, JPL_ECLIPTIC_VX, JPL_ECLIPTIC_VY, JPL_ECLIPTIC_VZ)
        self.assertAlmostEqual(ICRF_X, icrf_pos_vel[0],8)
        self.assertAlmostEqual(ICRF_Y, icrf_pos_vel[1],6)
        self.assertAlmostEqual(ICRF_Z, icrf_pos_vel[2],6)

        self.assertAlmostEqual(ICRF_VX, icrf_pos_vel[3],15)
        self.assertAlmostEqual(ICRF_VY, icrf_pos_vel[4],14)
        self.assertAlmostEqual(ICRF_VZ, icrf_pos_vel[5],14)
