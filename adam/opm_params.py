"""
    opm_params.py
"""

from datetime import datetime


class OpmParams(object):
    @classmethod
    def fromJsonResponse(cls, response_opm):
        header = response_opm['header']
        metadata = response_opm['metadata']
        spacecraft = response_opm['spacecraft']
        state_vector = response_opm['state_vector']
        keplerian_elements = response_opm.get('keplerian')
        covariance = response_opm.get('covariance')
        maneuvers = response_opm.get('maneuvers')
        adam_fields = {f['key']: f['value']
                       for f in response_opm.get('adam_fields') or []}
        opm_params = {
            'epoch': state_vector['epoch'],
            'state_vector': [
                state_vector['x'], state_vector['y'], state_vector['z'],
                state_vector['x_dot'], state_vector['y_dot'], state_vector['z_dot']
            ],

            'originator': header['originator'],
            'object_name': metadata['object_name'],
            'object_id': metadata['object_id'],

            'center_name': metadata['center_name'],
            'ref_frame': metadata['ref_frame'],

            'mass': spacecraft['mass'],
            'solar_rad_area': spacecraft['solar_rad_area'],
            'solar_rad_coeff': spacecraft['solar_rad_coeff'],
            'drag_area': spacecraft['drag_area'],
            'drag_coeff': spacecraft['drag_coeff'],
        }

        if covariance is not None:
            opm_params['hypercube'] = adam_fields['HYPERCUBE']
            opm_params['perturbation'] = int(
                adam_fields['INITIAL_PERTURBATION'])
            opm_params['covariance'] = [covariance['cx_x'],
                                        covariance['cy_x'],
                                        covariance['cy_y'],
                                        covariance['cz_x'],
                                        covariance['cz_y'],
                                        covariance['cz_z'],
                                        covariance['cx_dot_x'],
                                        covariance['cx_dot_y'],
                                        covariance['cx_dot_z'],
                                        covariance['cx_dot_x_dot'],
                                        covariance['cy_dot_x'],
                                        covariance['cy_dot_y'],
                                        covariance['cy_dot_z'],
                                        covariance['cy_dot_x_dot'],
                                        covariance['cy_dot_y_dot'],
                                        covariance['cz_dot_x'],
                                        covariance['cz_dot_y'],
                                        covariance['cz_dot_z'],
                                        covariance['cz_dot_x_dot'],
                                        covariance['cz_dot_y_dot'],
                                        covariance['cz_dot_z_dot']]

        if keplerian_elements is not None:
            opm_params['keplerian_elements'] = {
                'semi_major_axis_km': keplerian_elements['semi_major_axis'],
                'eccentricity': keplerian_elements['eccentricity'],
                'inclination_deg': keplerian_elements['inclination'],
                'ra_of_asc_node_deg': keplerian_elements['ra_of_asc_node'],
                'arg_of_pericenter_deg': keplerian_elements['arg_of_pericenter'],
                'true_anomaly_deg': keplerian_elements['true_anomaly'],
                'gm': keplerian_elements['gm'],
            }

        if maneuvers is not None and len(maneuvers) > 0:
            # Only the first one present will be parsed.
            opm_params['initial_maneuver'] = [
                maneuvers[0]['man_dv_1'],
                maneuvers[0]['man_dv_2'],
                maneuvers[0]['man_dv_3'],
            ]

        return OpmParams(opm_params)

    def __init__(self, params):
        """
        Param options are:

            --- epoch is required! ---
            epoch (str): the epoch associated with the state vector (IS0-8601 format)

            --- either state_vector or keplerian_elements is required! ---
            --- note that if keplerian_elements are provided, state_vector will be ignored
            --- by server side even if also provided. ---
            state_vector (list): an array with 6 elements [rx, ry, rz, vx, vy, vz]
                representing the cartesian coordinates (the position and velocity vector)
                of the object.
            keplerian_elements (dictionary): contains 7 elements representing the
                keplerian coordinates of the object. The elements are:
                    semi_major_axis_km (float): Semimajor axis (km)
                    eccentricity (float): Eccentricity of orbit
                    inclination_deg (float): Inclination of orbit (deg)
                    ra_of_asc_node_deg (float): Right ascension of ascending node (deg)
                    arg_of_pericenter_deg (float): Argument of pericenter (deg)
                    true_anomaly_deg (float): True anomaly (deg)
                    gm (float): Gravitational constant (km^3/s^2)

            originator (str): responsible entity for run (default: 'ADAM_User')
            object_name (str): name of object (default: 'dummy')
            object_id (str): identification of object (default: '001')

            center_name (str): center for propagation. 'SUN' or 'EARTH'. (default: 'SUN')
            ref_frame (str): reference frame for propagation. 'ICRF' (International Celestial
                             Reference Frame) or 'EMEME2000' (Earth Mean Ecliptic Mean
                             Equinox of J2000). (default: 'ICRF')

            mass (float): object mass in kilograms (default: 1000 kg)
            solar_rad_area (float): object solar radiation area in squared meters
                (default: 20 m^2)
            solar_rad_coeff (float): object solar radiation coefficient (default: 1)
            drag_area (float): object drag area in squared meters (default: 20 m^2)
            drag_coeff (float): object drag coefficient (default: 2.2)

            --- None or all of covariance, perturbation, and hypercube must be given ---
            --- No defaults if not given ---
            covariance (list): an array with 21 elements corresponding to a 6x6 lower triangle
            perturbation (int): sigma perturbation on state vector
            hypercube (str): hypercube propagation type (e.g. 'FACES' or 'CORNERS')

            initial_maneuver (list): An array with 3 elements representing intial dx, dy, dz
                in velocity-orbit-normal coordinates (dx is in direction of velocity,
                dy is orbit-normal, and dz is in direction of x cross y).
                Assumed to take place at state vector epoch.

        Raises:
            KeyError if the given object does not include 'epoch' and 'state_vector',
            or if unsupported parameters are provided

        """
        # Make this a bit easier to get right by checking for parameters by unexpected
        # names.
        supported_params = {'epoch', 'state_vector', 'keplerian_elements', 'originator',
                            'object_name', 'object_id', 'center_name', 'ref_frame', 'mass',
                            'solar_rad_area', 'solar_rad_coeff', 'drag_area', 'drag_coeff',
                            'covariance', 'perturbation', 'hypercube', 'initial_maneuver'}
        extra_params = params.keys() - supported_params
        if len(extra_params) > 0:
            raise KeyError("Unexpected parameters provided: %s" %
                           (extra_params))

        self._epoch = params['epoch']  # Required.

        if 'state_vector' not in params and 'keplerian_elements' not in params:
            raise KeyError(
                "Either state_vector or keplerian_elements must be provided.")

        supported_keplerian_elements = {'semi_major_axis_km', 'eccentricity', 'inclination_deg',
                                        'ra_of_asc_node_deg', 'arg_of_pericenter_deg',
                                        'true_anomaly_deg', 'gm'}
        if 'keplerian_elements' in params.keys():
            keplerian_params = params['keplerian_elements'].keys()
            if not supported_keplerian_elements == keplerian_params:
                raise KeyError("Unexpected keplerian elements provided. Values for exactly "
                               "the following must be given: %s" % (supported_keplerian_elements))

        self._state_vector = params.get('state_vector')
        self._keplerian_elements = params.get('keplerian_elements')

        self._originator = params.get('originator') or 'ADAM_User'
        self._object_name = params.get('object_name') or 'dummy'
        self._object_id = params.get('object_id') or '001'

        self._center_name = params.get('center_name') or 'SUN'
        self._ref_frame = params.get('ref_frame') or 'ICRF'

        self._mass = params.get('mass') or 1000.0
        self._solar_rad_area = params.get('solar_rad_area') or 20.0
        self._solar_rad_coeff = params.get('solar_rad_coeff') or 1.0
        self._drag_area = params.get('drag_area') or 20.0
        self._drag_coeff = params.get('drag_coeff') or 2.2

        self._covariance = params.get('covariance')
        self._perturbation = params.get('perturbation')
        self._hypercube = params.get('hypercube')

        self._initial_maneuver = params.get('initial_maneuver')

    def __repr__(self):
        return "OpmParams: %s" % self.generate_opm()

    def get_state_vector(self):
        return self._state_vector

    def set_state_vector(self, state_vector):
        self._state_vector = state_vector

    def generate_opm(self):
        """Generate an OPM string

        This function generates a single OPM string from defined parameters (CCSDS format)

        Args:
            None

        Returns:
            OPM (str)
        """

        # State vector is required in the OPM even if keplerian elements are also given. However,
        # in that case it will be ignored in favor of the keplerian elements so it is not required
        # from the user. If no state vector is specified, use dummy values.
        state_vector = self._state_vector or [0.0, 0.0, 0.0, 0.0, 0.0, 0.0]
        base_opm = "CCSDS_OPM_VERS = 2.0\n" + \
            ("CREATION_DATE = %s\n" % datetime.utcnow()) + \
            ("ORIGINATOR = %s\n" % self._originator) + \
            "COMMENT Cartesian coordinate system\n" + \
            ("OBJECT_NAME = %s\n" % self._object_name) + \
            ("OBJECT_ID = %s\n" % self._object_id) + \
            ("CENTER_NAME = %s\n" % self._center_name) + \
            ("REF_FRAME = %s\n" % self._ref_frame) + \
            "TIME_SYSTEM = UTC\n" + \
            ("EPOCH = %s\n" % self._epoch) + \
            ("X = %s\n" % (state_vector[0])) + \
            ("Y = %s\n" % (state_vector[1])) + \
            ("Z = %s\n" % (state_vector[2])) + \
            ("X_DOT = %s\n" % (state_vector[3])) + \
            ("Y_DOT = %s\n" % (state_vector[4])) + \
            ("Z_DOT = %s\n" % (state_vector[5]))

        keplerian_elements = ""
        if self._keplerian_elements is not None:
            keplerian_elements = \
                ("SEMI_MAJOR_AXIS = %s\n" % (self._keplerian_elements['semi_major_axis_km'])) + \
                ("ECCENTRICITY = %s\n" % (self._keplerian_elements['eccentricity'])) + \
                ("INCLINATION = %s\n" % (self._keplerian_elements['inclination_deg'])) + \
                ("RA_OF_ASC_NODE = %s\n" % (self._keplerian_elements['ra_of_asc_node_deg'])) + \
                ("ARG_OF_PERICENTER = %s\n" %
                    (self._keplerian_elements['arg_of_pericenter_deg'])) + \
                ("TRUE_ANOMALY = %s\n" % (self._keplerian_elements['true_anomaly_deg'])) + \
                ("GM = %s\n" % (self._keplerian_elements['gm']))

        spacecraft_params = \
            ("MASS = %s\n" % self._mass) + \
            ("SOLAR_RAD_AREA = %s\n" % self._solar_rad_area) + \
            ("SOLAR_RAD_COEFF = %s\n" % self._solar_rad_coeff) + \
            ("DRAG_AREA = %s\n" % self._drag_area) + \
            ("DRAG_COEFF = %s\n" % self._drag_coeff)

        covariance = ""
        if self._covariance is not None:
            covariance = ("CX_X = %s\n" % (self._covariance[0])) + \
                         ("CY_X = %s\n" % (self._covariance[1])) + \
                         ("CY_Y = %s\n" % (self._covariance[2])) + \
                         ("CZ_X = %s\n" % (self._covariance[3])) + \
                         ("CZ_Y = %s\n" % (self._covariance[4])) + \
                         ("CZ_Z = %s\n" % (self._covariance[5])) + \
                         ("CX_DOT_X = %s\n" % (self._covariance[6])) + \
                         ("CX_DOT_Y = %s\n" % (self._covariance[7])) + \
                         ("CX_DOT_Z = %s\n" % (self._covariance[8])) + \
                         ("CX_DOT_X_DOT = %s\n" % (self._covariance[9])) + \
                         ("CY_DOT_X = %s\n" % (self._covariance[10])) + \
                         ("CY_DOT_Y = %s\n" % (self._covariance[11])) + \
                         ("CY_DOT_Z = %s\n" % (self._covariance[12])) + \
                         ("CY_DOT_X_DOT = %s\n" % (self._covariance[13])) + \
                         ("CY_DOT_Y_DOT = %s\n" % (self._covariance[14])) + \
                         ("CZ_DOT_X = %s\n" % (self._covariance[15])) + \
                         ("CZ_DOT_Y = %s\n" % (self._covariance[16])) + \
                         ("CZ_DOT_Z = %s\n" % (self._covariance[17])) + \
                         ("CZ_DOT_X_DOT = %s\n" % (self._covariance[18])) + \
                         ("CZ_DOT_Y_DOT = %s\n" % (self._covariance[19])) + \
                         ("CZ_DOT_Z_DOT = %s\n" % (self._covariance[20])) + \
                         ("USER_DEFINED_ADAM_INITIAL_PERTURBATION = %s [sigma]\n" %
                          self._perturbation) + \
                         ("USER_DEFINED_ADAM_HYPERCUBE = %s\n" % self._hypercube)

        maneuver = ""
        if self._initial_maneuver is not None:
            maneuver = ("MAN_EPOCH_IGNITION = %s\n" % (self._epoch)) + \
                       ("MAN_DURATION = 0.0\n") + \
                       ("MAN_DELTA_MASS = 0.0\n") + \
                       ("MAN_REF_FRAME = TNW\n") + \
                       ("MAN_DV_1 = %s\n" % (self._initial_maneuver[0])) + \
                       ("MAN_DV_2 = %s\n" % (self._initial_maneuver[1])) + \
                       ("MAN_DV_3 = %s\n" % (self._initial_maneuver[2]))

        return base_opm + keplerian_elements + spacecraft_params + covariance + maneuver
