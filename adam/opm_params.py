"""
    opm_params.py
"""

from datetime import datetime


class OpmParams(object):
    @classmethod
    def fromJsonResponse(cls, response_opm):
        # Values in [] are guaranteed to be present. Values in .get() may be missing.
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

            initial_maneuver (list): An array with 3 elements representing initial dx, dy, dz
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
                            'covariance', 'keplerian_covariance', 'perturbation', 'hypercube',
                            'initial_maneuver'}
        extra_params = self.__check_params(supported_params, params)
        if len(extra_params) > 0:
            raise KeyError("Unexpected parameters provided: %s" %
                           (extra_params))

        self._epoch = params['epoch']  # Required.

        if 'state_vector' not in params and 'keplerian_elements' not in params:
            raise KeyError(
                "Either state_vector or keplerian_elements must be provided.")

        keplerian_params = params.get('keplerian_elements', [])
        if keplerian_params:
            self._check_keplerian_params(keplerian_params)

        self._state_vector = params.get('state_vector')
        self._keplerian_elements = keplerian_params

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
        self._keplerian_covariance = params.get('keplerian_covariance')
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
        using_mean_anomaly = True
        if self._keplerian_elements is not None:
            if ('true_anomaly_deg') in self._keplerian_elements:
                using_mean_anomaly = False
                keplerian_elements = \
                    ("SEMI_MAJOR_AXIS = %s\n" %
                     (self._keplerian_elements['semi_major_axis_km'])) + \
                    ("ECCENTRICITY = %s\n" % (self._keplerian_elements['eccentricity'])) + \
                    ("INCLINATION = %s\n" % (self._keplerian_elements['inclination_deg'])) + \
                    ("RA_OF_ASC_NODE = %s\n" %
                     (self._keplerian_elements['ra_of_asc_node_deg'])) + \
                    ("ARG_OF_PERICENTER = %s\n" %
                     (self._keplerian_elements['arg_of_pericenter_deg'])) + \
                    ("TRUE_ANOMALY = %s\n" % (self._keplerian_elements['true_anomaly_deg'])) + \
                    ("GM = %s\n" % (self._keplerian_elements['gm']))
            if ('mean_anomaly_deg') in self._keplerian_elements:
                keplerian_elements = \
                    ("SEMI_MAJOR_AXIS = %s\n" %
                     (self._keplerian_elements['semi_major_axis_km'])) + \
                    ("ECCENTRICITY = %s\n" % (self._keplerian_elements['eccentricity'])) + \
                    ("INCLINATION = %s\n" % (self._keplerian_elements['inclination_deg'])) + \
                    ("RA_OF_ASC_NODE = %s\n" %
                     (self._keplerian_elements['ra_of_asc_node_deg'])) + \
                    ("ARG_OF_PERICENTER = %s\n" %
                     (self._keplerian_elements['arg_of_pericenter_deg'])) + \
                    ("MEAN_ANOMALY = %s\n" % (self._keplerian_elements['mean_anomaly_deg'])) + \
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

        keplerian_covariance = ""
        anomaly_angle_cov = ""
        if self._keplerian_covariance is not None:
            if using_mean_anomaly:
                anomaly_angle_cov = ("USER_DEFINED_CM_A = %s\n" % (
                    self._keplerian_covariance[15])) + \
                                    ("USER_DEFINED_CM_E = %s\n" % (
                                        self._keplerian_covariance[16])) + \
                                    ("USER_DEFINED_CM_I = %s\n" % (
                                        self._keplerian_covariance[17])) + \
                                    ("USER_DEFINED_CM_O = %s\n" % (
                                        self._keplerian_covariance[18])) + \
                                    ("USER_DEFINED_CM_W = %s\n" % (
                                        self._keplerian_covariance[19])) + \
                                    ("USER_DEFINED_CM_M = %s\n" % (self._keplerian_covariance[20]))
            else:
                anomaly_angle_cov = ("USER_DEFINED_CT_A = %s\n" % (
                    self._keplerian_covariance[15])) + \
                                    ("USER_DEFINED_CT_E = %s\n" % (
                                        self._keplerian_covariance[16])) + \
                                    ("USER_DEFINED_CT_I = %s\n" % (
                                        self._keplerian_covariance[17])) + \
                                    ("USER_DEFINED_CT_O = %s\n" % (
                                        self._keplerian_covariance[18])) + \
                                    ("USER_DEFINED_CT_W = %s\n" % (
                                        self._keplerian_covariance[19])) + \
                                    ("USER_DEFINED_CT_T = %s\n" % (self._keplerian_covariance[20]))

            covariance = ("USER_DEFINED_CA_A = %s\n" % (self._keplerian_covariance[0])) + \
                         ("USER_DEFINED_CE_A = %s\n" % (self._keplerian_covariance[1])) + \
                         ("USER_DEFINED_CE_E = %s\n" % (self._keplerian_covariance[2])) + \
                         ("USER_DEFINED_CI_A = %s\n" % (self._keplerian_covariance[3])) + \
                         ("USER_DEFINED_CI_E = %s\n" % (self._keplerian_covariance[4])) + \
                         ("USER_DEFINED_CI_I = %s\n" % (self._keplerian_covariance[5])) + \
                         ("USER_DEFINED_CO_A = %s\n" % (self._keplerian_covariance[6])) + \
                         ("USER_DEFINED_CO_E = %s\n" % (self._keplerian_covariance[7])) + \
                         ("USER_DEFINED_CO_I = %s\n" % (self._keplerian_covariance[8])) + \
                         ("USER_DEFINED_CO_O = %s\n" % (self._keplerian_covariance[9])) + \
                         ("USER_DEFINED_CW_A = %s\n" % (self._keplerian_covariance[10])) + \
                         ("USER_DEFINED_CW_E = %s\n" % (self._keplerian_covariance[11])) + \
                         ("USER_DEFINED_CW_I = %s\n" % (self._keplerian_covariance[12])) + \
                         ("USER_DEFINED_CW_O = %s\n" % (self._keplerian_covariance[13])) + \
                         ("USER_DEFINED_CW_W = %s\n" % (self._keplerian_covariance[14])) + \
                         anomaly_angle_cov

        return base_opm + keplerian_elements + spacecraft_params + covariance + maneuver + keplerian_covariance

    def __check_params(self, allowed, actual):
        extra_items = []
        for item in actual:
            if item not in allowed:
                extra_items.append(item)
        return extra_items

    def _check_keplerian_params(self, actual):
        actual_set = frozenset(actual)

        # These params must be a subset of actual
        always_required_params = frozenset(['semi_major_axis_km', 'eccentricity', 'inclination_deg',
                                            'ra_of_asc_node_deg', 'arg_of_pericenter_deg', 'gm'])

        if not always_required_params <= actual_set:
            raise KeyError(
                f'Keplerian params must include all parameters of {always_required_params}. '
                f'Provided params were {actual_set}')

        remaining_actual_set = actual_set - always_required_params

        # Either true anomaly or mean anomaly are provided, but not both
        oneof_required_params = frozenset(['true_anomaly_deg', 'mean_anomaly_deg'])
        satisfies_oneof_required_param = (
                (('true_anomaly_deg' in remaining_actual_set)
                 or ('mean_anomaly_deg' in remaining_actual_set))
                and not (oneof_required_params <= remaining_actual_set))

        if not satisfies_oneof_required_param:
            raise KeyError(
                f'Keplerian params must include either one of {oneof_required_params}. '
                f'Provided params were {actual_set}')

        extra_params = remaining_actual_set - oneof_required_params

        if extra_params:
            raise KeyError(f'Unrecognized Keplerian params were provided: {extra_params}')
