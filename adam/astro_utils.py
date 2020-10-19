import numpy as np


JPL_OBLIQUITY = np.deg2rad(84381.448 / 3600.0)

def icrf_to_jpl_ecliptic(x, y, z, vx, vy, vz):
    return _apply_x_rotation(JPL_OBLIQUITY, x, y, z, vx, vy, vz)


def jpl_ecliptic_to_icrf(x, y, z, vx, vy, vz):
    return _apply_x_rotation(-JPL_OBLIQUITY, x, y, z, vx, vy, vz)


def _apply_x_rotation(phi, x0, y0, z0, vx0, vy0, vz0):
    x = x0
    y = y0 * np.cos(phi) + z0 * np.sin(phi)
    z = -y0 * np.sin(phi) + z0 * np.cos(phi)
    vx = vx0
    vy = vy0 * np.cos(phi) + vz0 * np.sin(phi)
    vz = -vy0 * np.sin(phi) + vz0 * np.cos(phi)
    return [x, y, z, vx, vy, vz]
