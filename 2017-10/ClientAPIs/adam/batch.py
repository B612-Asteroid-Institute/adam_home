"""
    batch.py
"""

from adam.rest_proxy import RestRequests
from datetime import datetime

# Base URL
_URL = 'https://pro-equinox-162418.appspot.com/_ah/api/adam/v1'

def _set_url_base(url):
    """Set the base URL

    This function sets the global _URL to the inputted url and returns the old global _URL.

    Args:
        url (str): the URL to set as global

    Returns:
        the old _URL (str)
    """
    global _URL
    old_value = _URL
    _URL = url
    return old_value

class Batch(object):
    """Module for a batch request

    This class is used for creating batch runs on the cloud

    """
    def __init__(self):
        """Initializes attributes

        """
        self._state_vector = None    # position and velocity state vector
        self._epoch = None           # epoch associated with state vector
        self._start_time = None      # start time of run
        self._end_time = None        # end time of run
        self._step_size = 86400      # defaulted to 1 day
        self._calc_state = None      # status on run (e.g. RUNNING, COMPLETED)
        self._uuid = None            # uuid associated with run
        self._parts_count = 0        # number of parts count
        self._loaded_parts = {}      # parts that have already been loaded
        self._rest = RestRequests()  # rest request option (requests package or proxy)

    def __repr__(self):
        """Printable representation of returned values from job run

        This function returns the printed uuid and calc state

        Args:
            None

        Returns:
            Printable representation of uuid and calc state (str)
        """
        return "Batch %s, %s" % (self._uuid, self._calc_state)

    def set_rest_accessor(self, proxy):
        """Override network access methods

        This function overrides network access and sets the rest request to a proxy

        Args:
            proxy (class)

        Returns:
            None
        """
        self._rest = proxy

    def set_state_vector(self, epoch, state_vector):
        """Set epoch and state vector

        This function sets the epoch and cartesian state vector (position and velocity)

        Args:
            epoch (str) - the epoch associated with the state vector (IS0-8601 format)
            state_vector (list) - an array with 6 elements [rx, ry, rz, vx, vy, vz]

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

    def generate_opm(self):
        """Generate an OPM string

        This function generates a single OPM string from defined parameters (CCSDS format)

        Args:
            None

        Returns:
            OPM (str)
        """
        return "CCSDS_OPM_VERS = 2.0\n" + \
               ("CREATION_DATE = %s\n" % datetime.utcnow()) + \
               "ORIGINATOR = Tatiana\n" + \
               "COMMENT Cartesian coordinate system\n" + \
               "OBJECT_NAME = dummy\n" + \
               "OBJECT_ID = 001\n" + \
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
               "MASS = 1000\n" + \
               "SOLAR_RAD_AREA = 20\n" + \
               "SOLAR_RAD_COEFF = 1\n" + \
               "DRAG_AREA = 20\n" + \
               "DRAG_COEFF = 2.2"

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
                'opm_string': self.generate_opm()}

        # Post request on cloud server
        code, response = self._rest.post(_URL + '/batch', data)

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
        code, response = self._rest.get(_URL + '/batch/' + self._uuid)

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

        # Raise error if job has not completed
        if self._calc_state != "COMPLETED":
            raise KeyError

        # Check to see if index is out of bounds
        if index < 1 or index > self._parts_count:
            raise IndexError

        # Check if part exists and get it if it does
        try:
            part = self._loaded_parts[index]
        except KeyError:
            part = None

        # If no part exists, grab part from URL
        if part is None:
            code, part = self._rest.get(_URL + '/batch/' + self._uuid + '/' + str(index))

            # Return 'None' if specific part submission was not successful
            if code != 200:
                return None

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