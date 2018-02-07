"""
    batch.py
"""

from adam.rest_proxy import RestRequests
from datetime import datetime
from tabulate import tabulate

class Batches(object):
    def __init__(self, rest):
        self._rest = rest
    
    def __repr__(self):
        return "Batches module"
    
    def new_batch(self, batch):
        batch.submit()
        
    def delete_batch(self, uuid):
        code = self._rest.delete('/batch/' + uuid)
        
        if code != 204:
            raise RuntimeError("Server status code: %s" % (code))
    
    def _get_batches(self, project):
        code, response = self._rest.get('/batch?project_uuid=' + project)
            
        if code != 200:
            raise RuntimeError("Server status code: %s; Response: %s" % (code, response))
        
        return response['items']
    
    def get_batch_states(self, project):
        batches = {} 
        for b in self._get_batches(project):
            batches[b['uuid']] = b['calc_state']
        
        return batches
    
    def print_batches(self, project):
        batches = self._get_batches(project)
        
        print(tabulate(batches, headers="keys", tablefmt="fancy_grid"))
        

M2KM = 1E-3  # meters to kilometers

class Batch(object):
    """Module for a batch request

    This class is used for creating batch runs on the cloud

    """
    def __init__(self, rest):
        """Initializes attributes

        """
        self._state_vector = None     # position and velocity state vector
        self._epoch = None            # epoch associated with state vector
        self._start_time = None       # start time of run
        self._end_time = None         # end time of run
        self._step_size = 86400       # step size in seconds (defaulted to 1 day)
        self._covariance = None       # covariance
        self._hypercube = None        # hypercube type (e.g. FACES, CORNERS)
        self._perturbation = None     # perturbation sigma on state vector
        self._calc_state = None       # status on run (e.g. RUNNING, COMPLETED)
        self._uuid = None             # uuid associated with run
        self._parts_count = 0         # number of parts count
        self._loaded_parts = {}       # parts that have already been loaded
        self._rest = rest

        # Object properties
        self._mass = 1000             # mass, kg
        self._solar_rad_area = 20     # solar radiation area, m^2
        self._solar_rad_coeff = 1     # solar radiation coefficient
        self._drag_area = 20          # drag area, m^2
        self._drag_coeff = 2.2        # drag coefficient

        # Propagator settings (default is the Sun, all planets, and the Moon as point masses [no asteroids])
        self._propagator_uuid = "00000000-0000-0000-0000-000000000001"

        # Header and metadata information
        self._originator = 'ADAM_User'
        self._object_name = 'dummy'
        self._object_id = '001'
        self._description = None
        self._project = None

    def __repr__(self):
        """Printable representation of returned values from job run

        This function returns the printed uuid and calc state

        Args:
            None

        Returns:
            Printable representation of uuid and calc state (str)
        """
        return "Batch %s, %s" % (self._uuid, self._calc_state)

    def set_description(self, description):
        """Sets the description of the run

        This function sets the description of the propagated run

        Args:
            description (str): description of the run

        Returns:
            None
        """
        self._description = description
    
    def set_project(self, project):
        self._project = project

    def set_originator(self, originator):
        """Sets the originator of the run

        This function sets the originator of the propagated run

        Args:
            originator (str): responsible entity for run

        Returns:
            None
        """
        self._originator = originator

    def set_object_name(self, object_name):
        """Sets the object name

        This function sets the object's name for the propagation

        Args:
            object_name (str): name of object

        Returns:
            None
        """
        self._object_name = object_name

    def set_object_id(self, object_id):
        """Sets the object ID

        This function sets the object's ID for the propagation

        Args:
            object_id (str): identification of object

        Returns:
            None
        """
        self._object_id = object_id

    def set_state_vector(self, epoch, state_vector):
        """Set epoch and state vector

        This function sets the epoch and cartesian state vector (position and velocity)

        Args:
            epoch (str): the epoch associated with the state vector (IS0-8601 format)
            state_vector (list): an array with 6 elements [rx, ry, rz, vx, vy, vz]

        Returns:
            None
        """
        self._epoch = epoch
        self._state_vector = state_vector

    def set_start_time(self, start_time):
        """Set start time

        This function sets the start time for the propagation run

        Args:
            start_time (str): start time in ISO-8601 format (yyyy-MM-ddTHH:mm:ssZ)

        Returns:
            None
        """
        self._start_time = start_time

    def set_end_time(self, end_time):
        """Set end time

        This function sets the end time for the propagation run

        Args:
            end_time (str): end time in ISO-8601 format (yyyy-MM-ddTHH:mm:ssZ)

        Returns:
            None
        """
        self._end_time = end_time

    def set_step_size(self, step_size, step_size_unit):
        """Set step size

        This function sets the step size for the propagator run; can be positive or negative
        It first converts the step size to seconds given the step size unit
        Valid units for step size are: "sec", "min", "hour", or "day"

        Args:
            step_size (int): step size in seconds
            step_size_unit (str): units of time for step size

        Returns:
            None
        """

        # Multiplier dictionary to convert to seconds
        multiplier = {"sec": 1, "min": 60, "hour": 3600, "day": 86400}

        # Get step size; raise KeyError if unit not in dictionary
        try:
            step_size = round(step_size * multiplier[step_size_unit])
        except:
            raise KeyError('Invalid units. Options: "sec", "min", "hour", or "day"')

        # Set step size
        self._step_size = step_size

    def set_covariance(self, covariance, hypercube, perturbation):
        """Set covariance

        This function sets the state vector error covariance (6x6 lower triangular form)
        None or all of the parameters must be given

        Args:
            covariance (list): an array with 21 elements corresponding to a 6x6 lower triangle
            hypercube (str): hypercube propagation type (e.g. 'FACES' or 'CORNERS')
            perturbation (int): sigma perturbation

        Returns:
            None
        """
        self._covariance = covariance
        self._hypercube = hypercube
        self._perturbation = perturbation

    def set_mass(self, mass):
        """Set object mass

        This function sets the object's mass for propagation

        Args:
            mass (float): object mass in kilograms

        Returns:
            None
        """
        self._mass = mass

    def set_solar_rad_area(self, solar_rad_area):
        """Set object solar radiation area

        This function sets the object's solar radiation area for propagation

        Args:
            solar_rad_area (float): object solar radiation area in squared meters

        Returns:
            None
        """
        self._solar_rad_area = solar_rad_area

    def set_solar_rad_coeff(self, solar_rad_coeff):
        """Set object solar radiation coefficient

        This function sets the object's solar radiation coefficient for propagation

        Args:
            solar_rad_coeff (float): object solar radiation coefficient

        Returns:
            None
        """
        self._solar_rad_coeff = solar_rad_coeff

    def set_drag_area(self, drag_area):
        """Set object drag area

        This function sets the object's drag area for propagation

        Args:
            drag_area (float): object drag area in squared meters

        Returns:
            None
        """
        self._drag_area = drag_area

    def set_drag_coeff(self, drag_coeff):
        """Set object drag coefficient

        This function sets the object's drag coefficient for propagation

        Args:
            drag_coeff (float): object drag coefficient

        Returns:
            None
        """
        self._drag_coeff = drag_coeff

    def set_propagator_uuid(self, propagator_uuid):
        """Set propagator uuid

        This functions sets the propagator uuid for the desired force model
        See https://pro-equinox-162418.appspot.com/_ah/api/adam/v1/config for configurations

        Args:
            propagator_uuid (str): configuration uuid to set for the propagator

        Returns:
            None
        """
        self._propagator_uuid = propagator_uuid
    
    def set_project(self, project_uuid):
        self._project = project_uuid

    def generate_opm(self):
        """Generate an OPM string

        This function generates a single OPM string from defined parameters (CCSDS format)

        Args:
            None

        Returns:
            OPM (str)
        """
        base_opm =  "CCSDS_OPM_VERS = 2.0\n" + \
                    ("CREATION_DATE = %s\n" % datetime.utcnow()) + \
                    ("ORIGINATOR = %s\n" % self._originator) + \
                    "COMMENT Cartesian coordinate system\n" + \
                    ("OBJECT_NAME = %s\n" % self._object_name) + \
                    ("OBJECT_ID = %s\n" % self._object_id) + \
                    "CENTER_NAME = SUN\n" + \
                    "REF_FRAME = ITRF-97\n" + \
                    "TIME_SYSTEM = UTC\n" + \
                    ("EPOCH = %s\n" % self._epoch) + \
                    ("X = %s\n" % (self._state_vector[0])) + \
                    ("Y = %s\n" % (self._state_vector[1])) + \
                    ("Z = %s\n" % (self._state_vector[2])) + \
                    ("X_DOT = %s\n" % (self._state_vector[3])) + \
                    ("Y_DOT = %s\n" % (self._state_vector[4])) + \
                    ("Z_DOT = %s\n" % (self._state_vector[5])) + \
                    ("MASS = %s\n" % self._mass) + \
                    ("SOLAR_RAD_AREA = %s\n" % self._solar_rad_area) + \
                    ("SOLAR_RAD_COEFF = %s\n" % self._solar_rad_coeff) + \
                    ("DRAG_AREA = %s\n" % self._drag_area) + \
                    ("DRAG_COEFF = %s" % self._drag_coeff)

        if self._covariance is None:
            return base_opm
        else:
            covariance = ("\nCX_X = %s\n" % (self._covariance[0])) + \
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
                         ("USER_DEFINED_ADAM_INITIAL_PERTURBATION = %s [sigma]\n" % self._perturbation) + \
                         ("USER_DEFINED_ADAM_HYPERCUBE = %s\n" % self._hypercube)
            return base_opm + covariance

    def submit(self):
        """Submit a job to the cloud

        This function submits a job to the cloud. If the submission was successful, it stores the uuid and calc_state.
        If parameters are missing, it will raise a key error associated with that parameter. If the submission failed
        on the server side, it will return the server status code and associated response.

        Raises:
            KeyErrors: if any of the following are not provided:
                       start_time, end_time, epoch, or state_vector
        """

        # Raise KeyErrors for missing parameters
        if self._start_time is None:
            raise KeyError('Need start_time!')
        if self._end_time is None:
            raise KeyError('Need end_time!')
        if self._epoch is None:
            raise KeyError('Need epoch!')
        if self._state_vector is None:
            raise KeyError('Need state_vector!')

        # Create metadata dictionary
        data = {'start_time': self._start_time,
                'step_duration_sec': self._step_size,
                'end_time': self._end_time,
                'opm_string': self.generate_opm(),
                'propagator_uuid': self._propagator_uuid,
                'project': self._project}

        if self._description is not None:
            data['description'] = self._description

        # Post request on cloud server
        code, response = self._rest.post('/batch', data)

        # Check error code
        if code != 200:
            raise RuntimeError("Server status code: %s; Response: %s" % (code, response))

        # Store UUID and calc state
        self._uuid = response['uuid']
        self._calc_state = response['calc_state']

    def _load_state(self):
        """Load job state from UUID

        This function loads the code and response from a UUID.
        If the response was successful, it will store the calc state and parts count.

        Args:
            None

        Returns:
            calc_state (str)

        Raises:
            KeyError: if uuid is missing
            RuntimeError: if run failed
        """

        # Raise error if UUID is missing
        if self._uuid is None:
            raise KeyError("Need uuid!")

        # Get code and response from UUID
        code, response = self._rest.get('/batch/' + self._uuid)

        # Check for failed error codes and raise error if job failed
        if code == 404:    # Not found
            return False
        elif code != 200:
            raise RuntimeError("Server status code: %s; Response: %s" % (code, response))

        # Store/return calc state and store parts count
        self._calc_state = response['calc_state']
        self._parts_count = response['parts_count']
        return self._calc_state

    def is_ready(self):
        """Determine if job is ready

        This function determines if the job has either completed or failed (i.e., not waiting).

        Args:
            None

        Returns:
            Boolean
        """
        current_state = self._load_state()
        return current_state in ["COMPLETED", "FAILED"]

    def get_calc_state(self):
        """Get calc state

        This function just returns the calc state (job status)

        Args:
            None

        Returns:
            calc_state (str)
        """
        return self._calc_state

    def get_parts_count(self):
        """Get parts count

        This function just returns the parts count

        Args:
            None

        Returns:
            parts_count (int)
        """
        return self._parts_count

    def get_uuid(self):
        """Grab the UUID

        This function just returns the UUID of the run

        Args:
            None

        Returns:
            uuid (str)
        """
        return self._uuid

    def _load_part(self, index):
        """Load part

        This function attempts to load the part and store it in the loaded parts. It will first try to check if the run
        has completed and if the index value is valid. It will then check if the part already exists and return it
        if it does. Otherwise, it will attempt to grab the part from the run on the server and return 'None' if the job
        has not returned a successful code error.

        Args:
            index (int): part index of job (1 for regular job, > 1 for jobs with covariance)

        Returns:
            part (dict): json response structure of specific part run

        Raises:
            KeyError: if calc_state of overall run is not 'COMPLETED' or if part is 'None'
            IndexError: if provided index is out of bounds
        """

        # Check to see if index is out of bounds
        if index < 1 or index > self._parts_count:
            raise IndexError

        # Check if part exists and get it if it does
        try:
            part = self._loaded_parts[index]
        except KeyError:
            part = None

        # If no part exists, grab part from server
        if part is None:
            code, part = self._rest.get('/batch/' + self._uuid + '/' + str(index))

            # Raise error if specific part submission was not successful
            if code != 200:
                raise RuntimeError("Server status code: %s" % (code))

            # Get the status of the submitted job and grab the part if it is either 'COMPLETED' or 'FAILED'
            status = part['calc_state']
            if status == 'COMPLETED' or status == 'FAILED':
                self._loaded_parts[index] = part

        # If still no part, raise KeyError
        if part is None:
            raise KeyError

        # Return the part (json dict response for each specific part)
        return part

    def get_part_error(self, index):
        """Get error from specified part

        This function loads the part (json response) that is stored and grabs its code error

        Args:
            index (int): part index of job (1 for regular job, > 1 for jobs with covariance)

        Returns:
            Either the part error (str) or None
        """

        # Load the part from the given index
        part = self._load_part(index)

        # Try to return the error for that part; return None otherwise
        try:
            return part['error']
        except KeyError:
            return None

    def get_part_state(self, index):
        """Get calc state from specified part

        This function loads the part (json response) that is stored and grabs its calc state

        Args:
            index (int): part index of job (1 for regular job, > 1 for jobs with covariance)

        Returns:
            Either the calc state (str) or None
        """

        # Load the part from the given index
        part = self._load_part(index)

        # Try to return the calc state for that part; return None otherwise
        try:
            return part['calc_state']
        except KeyError:
            return None

    def is_ready_part(self, index):
        """Determine if a part is ready

        This function determines if the job for a specified part has either completed or failed (i.e., not waiting).

        Args:
            index (int): part index of job (1 for regular job, > 1 for jobs with covariance)

        Returns:
            Boolean
        """

        # Load the part from the given index
        part_state = self.get_part_state(index)

        return part_state in ["COMPLETED", "FAILED"]

    def get_part_ephemeris(self, index):
        """Get ephemeris from specified part

        This function loads the part (json response) that is stored and grabs its STK ephemeris

        Args:
            index (int): part index of job (1 for regular job, > 1 for jobs with covariance)

        Returns:
            Either the STK ephemeris (str) or None
        """

        # Load the part from the given index
        part = self._load_part(index)

        # Try to return the ephemeris for that part; return None otherwise
        try:
            return part['stk_ephemeris']
        except KeyError:
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

        # get final ephemeris part
        stk_ephemeris = self.get_part_ephemeris(self._parts_count)
        if stk_ephemeris is None:
            return None
    
        split_ephem = stk_ephemeris.splitlines()
        state_vectors = []
        for line in split_ephem:
            split_line  = line.split()
            # It's a state if it has more than 7 elements
            if len(split_line) >= 7:
                state_vector = [(float(i) * M2KM) for i in split_line]
                # Ignore time
                state_vectors.append(state_vector[1:7])     
        
        # We want the last element
        return state_vectors[-1]