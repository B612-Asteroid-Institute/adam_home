"""
    batch.py
"""

from datetime import datetime, timedelta


class Batch(object):
    def __init__(self, propagation_params, opm_params):
        self._propagation_params = propagation_params
        self._opm_params = opm_params
        self._state_summary = None
        self._results = None

    def __repr__(self):
        return "Batch %s, %s" % (self.get_uuid(), self.get_calc_state())

    def get_propagation_params(self):
        return self._propagation_params

    def get_opm_params(self):
        return self._opm_params

    def get_state_summary(self):
        return self._state_summary

    def set_state_summary(self, state_summary):
        self._state_summary = state_summary

    def get_results(self):
        return self._results

    def set_results(self, results):
        self._results = results

    # Convenience method to get batch uuid.
    def get_uuid(self):
        if self._state_summary is None:
            return None
        return self._state_summary.get_uuid()

    # Convenience method to get batch calculation state.
    def get_calc_state(self):
        if self._state_summary is None:
            return None
        return self._state_summary.get_calc_state()


class PropagationParams(object):

    DEFAULT_CONFIG_ID = "00000000-0000-0000-0000-000000000001"

    def __init__(self, params):
        """
        Param options are:

            --- start_time and end_time are required! ---
            start_time (str): start time of the run
            end_time (str): end time of the run

            step_size (int): step size in seconds. Defaults to 86400, or one day.
            propagator_uuid (str): propagator settings to use (default is the Sun,
                all planets, and the Moon as point masses [no asteroids])
            description (str): human-readable description of the run

        Raises:
            KeyError if the given object does not include 'start_time' and 'end_time',
            or if unsupported parameters are provided
        """
        # Make this a bit easier to get right by checking for parameters by unexpected
        # names.
        supported_params = {'start_time', 'end_time', 'step_size',
                            'propagator_uuid', 'project_uuid', 'description'}
        extra_params = params.keys() - supported_params
        if len(extra_params) > 0:
            raise KeyError("Unexpected parameters provided: %s" %
                           (extra_params))

        self._start_time = params['start_time']  # Required.
        self._end_time = params['end_time']  # Required.
        # Check explicitly for None, since 0 is a valid value.
        self._step_size = params.get('step_size') if params.get('step_size') is not None else 86400
        self._propagator_uuid = params.get('propagator_uuid') or self.DEFAULT_CONFIG_ID
        self._project_uuid = params.get('project_uuid')
        self._description = params.get('description')

    def __repr__(self):
        return "Batch params [%s, %s, %s, %s, %s, %s]" % (
            self._start_time, self._end_time, self._step_size,
            self._propagator_uuid, self._project_uuid, self._description)

    def get_start_time(self):
        return self._start_time

    def get_end_time(self):
        return self._end_time

    def get_step_size(self):
        return self._step_size

    def get_propagator_uuid(self):
        return self._propagator_uuid

    def get_project_uuid(self):
        return self._project_uuid

    def get_description(self):
        return self._description


class OpmParams(object):
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

        Raises:
            KeyError if the given object does not include 'epoch' and 'state_vector',
            or if unsupported parameters are provided

        """
        # Make this a bit easier to get right by checking for parameters by unexpected
        # names.
        supported_params = {'epoch', 'state_vector', 'keplerian_elements', 'originator',
                            'object_name', 'object_id', 'center_name', 'ref_frame', 'mass', 'solar_rad_area',
                            'solar_rad_coeff', 'drag_area', 'drag_coeff', 'covariance',
                            'perturbation', 'hypercube'}
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

        self._mass = params.get('mass') or 1000
        self._solar_rad_area = params.get('solar_rad_area') or 20
        self._solar_rad_coeff = params.get('solar_rad_coeff') or 1
        self._drag_area = params.get('drag_area') or 20
        self._drag_coeff = params.get('drag_coeff') or 2.2

        self._covariance = params.get('covariance')
        self._perturbation = params.get('perturbation')
        self._hypercube = params.get('hypercube')

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
        state_vector = self._state_vector or [0, 0, 0, 0, 0, 0]
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

        return base_opm + keplerian_elements + spacecraft_params + covariance


class StateSummary(object):
    def __init__(self, json):
        """ Requires a json response as returned from the server representing a batch
            state summary (e.g. from /batch/uuid or in bulk from batch/project_id)

            Raises:
                KeyError if the given object does not include 'uuid' and 'calc_state'
        """
        self._uuid = json['uuid']
        self._calc_state = json['calc_state']
        self._step_size = json.get('step_duration_sec')
        self._create_time = json.get('create_time')
        self._execute_time = json.get('execute_time')
        self._complete_time = json.get('complete_time')
        self._project_uuid = json.get('project')
        self._parts_count = json.get('parts_count')

    def __repr__(self):
        return "State summary for %s: %s" % (self._uuid, self._calc_state)

    def get_uuid(self):
        return self._uuid

    def get_step_size(self):
        return self._step_size

    def get_create_time(self):
        return self._create_time

    def get_execute_time(self):
        return self._execute_time

    def get_complete_time(self):
        return self._complete_time

    def get_project_uuid(self):
        return self._project_uuid

    def get_parts_count(self):
        return self._parts_count

    def get_calc_state(self):
        return self._calc_state


class PropagationResults(object):

    class Part(object):
        def __init__(self, part):
            """ Requires a json response as returned from the server representing a batch
                part state (e.g. from /batch/batch_uuid/part_index)

                Raises:
                    KeyError if the given object does not include 'part_index' and
                    'calc_state'
            """
            self._part_index = part['part_index']
            self._calc_state = part['calc_state']
            self._ephemeris = part.get('stk_ephemeris')
            self._error = part.get('error')

        def __repr__(self):
            return "PropagationPart [%s]" % (self._calc_state)

        def get_part_index(self):
            return self._part_index

        def get_calc_state(self):
            return self._calc_state

        def get_ephemeris(self):
            return self._ephemeris

        def get_error(self):
            return self._error

    M2KM = 1E-3  # meters to kilometers

    def __init__(self, parts):
        """ Should be called with a list of json responses from the server representing
            the parts_count parts of a batch propagation result.
        """
        if (len(parts) < 1):
            raise RuntimeError("Must provide at least one part.")

        # Fill in None responses (which may happen e.g. in case of 404s, or if the part
        # isn't ready yet) with Nones
        self._parts = [self.Part(p) if p is not None else None for p in parts]

    def __repr__(self):
        return "Propagation results with %s parts" % (len(self._parts))

    def get_parts(self):
        return self._parts

    def get_final_ephemeris(self):
        part = self._parts[-1]
        if part is None:
            print("Final part is not available")
            return None
        state = part.get_calc_state()
        if (state != 'COMPLETED'):
            print(
                "Final part is in state %s, not COMPLETED, so no ephemeris is available" % (state))
            return None
        return part.get_ephemeris()

    def _parse_date(self, date):
        parts = date.split(".")
        micros = float("0." + parts[1])

        parsed = datetime.strptime(parts[0], "%d %b %Y %H:%M:%S")
        parsed = parsed + timedelta(microseconds=micros * 1000000)
        return parsed

    def get_state_vector_at_time(self, target_epoch):
        """Get the state vector at the given time as a 6d list in [km, km/s]

        This function grabs the STK ephemeris from the final part. It parses the epoch given in
        the ephemeris in order to determine the times of all the state vectors given in the file.

        If a time is requested that does not have an explicit state vector, None will be returned.
        This will not interpolate.

        Args:
            target_epoch (datetime) - time at which a state vector is desired

        Returns:
            state_vector (list) - an array with 6 elements [rx, ry, rz, vx, vy, vz]
                                  [km, km/s]
        """
        stk_ephemeris = self.get_final_ephemeris()
        if stk_ephemeris is None:
            return None

        split_ephem = stk_ephemeris.splitlines()

        file_epoch = None
        for line in split_ephem:
            if line.startswith("ScenarioEpoch"):
                epoch_str = line.split('\t')[1]
                try:
                    file_epoch = self._parse_date(epoch_str)
                except ValueError as e:
                    print("Caught error, ignoring: " + str(e))
                    pass
        if file_epoch is None:
            print("No file epoch could be parsed")
            return None

        for line in split_ephem:
            split_line = line.split()
            # It's a state if it has more than 7 elements
            if len(split_line) >= 7:
                epoch = file_epoch + timedelta(seconds=float(split_line[0]))
                if abs((epoch - target_epoch).total_seconds()) <= 1e-6:
                    state_vector = [(float(i) * self.M2KM)
                                    for i in split_line][1:7]
                    return state_vector

        print("No state vector found at time " + str(target_epoch))
        return None

    def get_end_state_vector(self):
        """Get the end state vector as a 6d list in [km, km/s]

        This function first grabs the STK ephemeris from the final part
        The final state entry is returned as an array

        Args:

        Returns:
            state_vector (list) - an array with 6 elements [rx, ry, rz, vx, vy, vz]
                                  [km, km/s]
        """
        stk_ephemeris = self.get_final_ephemeris()
        if stk_ephemeris is None:
            return None

        split_ephem = stk_ephemeris.splitlines()
        state_vectors = []
        for line in split_ephem:
            split_line = line.split()
            # It's a state if it has more than 7 elements
            if len(split_line) >= 7:
                state_vector = [(float(i) * self.M2KM) for i in split_line]
                # Ignore time
                state_vectors.append(state_vector[1:7])

        # We want the last element
        return state_vectors[-1]
