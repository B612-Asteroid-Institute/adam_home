"""
    batch.py
"""

from adam.rest_proxy import RestRequests
from datetime import datetime

_URL = 'https://pro-equinox-162418.appspot.com/_ah/api/adam/v1'

def _set_url_base(url):
    global _URL
    old_value = _URL
    _URL = url
    return old_value

class Batch(object):
    """
    Module for a batch request
    """
    def __init__(self):
        self._state_vector = None    # position and velocity state vector
        self._epoch = None
        self._start_time = None
        self._end_time = None
        self._step_size = 86400      # defaulted to 1 day
        self._calc_state = None
        self._uuid = None
        self._parts_count = 0
        self._loaded_parts = {}
        self._rest = RestRequests()

    def __repr__(self):
        return "Batch %s, %s" % (self._uuid, self._calc_state)

    def set_rest_accessor(self, proxy):
        """
        Overrides network access methods
        :param proxy: RestProxy
        """
        self._rest = proxy

    def set_state_vector(self, epoch, state_vector):
        """
        Sets the cartesian state vector (position and velocity)
        :param state_vector: array with 6 elements
        """
        self._epoch = epoch
        self._state_vector = state_vector

    def set_start_time(self, start_time):
        """
        Sets the start time for the propagation run
        :param start_time: string in ISO-8601 format (yyyy-MM-ddTHH:mm:ssZ)
        """
        self._start_time = start_time

    def set_end_time(self, end_time):
        """
        Sets the end time for the propagation run
        :param end_time: string in ISO-8601 format (yyyy-MM-ddTHH:mm:ssZ)
        """
        self._end_time = end_time

    def generate_opm(self):
        """
        Generates an OPM string from defined parameters
        :return: OPM string
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
        """
        Submits a job to the cloud
        Raises error if run was not a success
        Stores UUID and calc state otherwise
        """
        if self._start_time is None:
            raise KeyError('Need start_time!')
        if self._end_time is None:
            raise KeyError('Need end_time!')
        if self._epoch is None:
            raise KeyError('Need epoch!')
        if self._state_vector is None:
            raise KeyError('Need state_vector!')

        data = {'start_time': self._start_time,
                'step_duration_sec': self._step_size,
                'end_time': self._end_time,
                'opm_string': self.generate_opm()}

        code, response = self._rest.post(_URL + '/batch', data)

        # Check error code
        if code != 200:
            raise RuntimeError("Server status code: %s; Response: %s" % (code, response))

        # Store UUID and calc state
        self._uuid = response['uuid']
        self._calc_state = response['calc_state']

    def _load_state(self):
        """
        Loads job state from UUID
        Stores calc state and parts count
        :return: calc state
        """
        if self._uuid is None:
            raise KeyError("Need uuid!")

        code, response = self._rest.get(_URL + '/batch/' + self._uuid)

        # Check error code
        if code == 404:
            return False
        elif code != 200:
            raise RuntimeError("Server status code: %s; Response: %s" % (code, response))

        self._calc_state = response['calc_state']
        self._parts_count = response['parts_count']
        return self._calc_state

    def is_ready(self):
        """
        Determines if job has either completed or failed
        :return: boolean (True if completed or failed)
        """
        current_state = self._load_state()
        return current_state in ["COMPLETED", "FAILED"]

    def get_calc_state(self):
        """
        Gets calc state
        :return: calc state
        """
        return self._calc_state

    def get_parts_count(self):
        """
        Gets parts count
        :return: parts count
        """
        return self._parts_count

    def get_uuid(self):
        """
        Grab the UUID of the run
        :return: UUID
        """
        return self._uuid

    def _load_part(self, index):
        if self._calc_state != "COMPLETED":
            raise KeyError
        if index < 1 or index > self._parts_count:
            raise IndexError
        try:
            part = self._loaded_parts[index]
        except KeyError:
            part = None
        if part is None:
            code, part = self._rest.get(_URL + '/batch/' + self._uuid + '/' + str(index))
            if code != 200:
                return None
            status = part['calc_state']
            if status == 'COMPLETED' or status == 'FAILED':
                self._loaded_parts[index] = part
        if part is None:
            raise KeyError
        return part

    def get_part_error(self, index):
        """
        Get error for individual part
        :param index: batch part number
        :return:
        """
        part = self._load_part(index)
        try:
            return part['error']
        except KeyError:
            return None

    def get_part_state(self, index):
        """
        Get state for each individual part
        :param index: batch part number
        :return:
        """
        part = self._load_part(index)
        try:
            return part['calc_state']
        except KeyError:
            return None

    def get_part_ephemeris(self, index):
        """
        Get ephemeris from specified part
        :param index:
        :return:
        """
        part = self._load_part(index)
        try:
            return part['stk_ephemeris']
        except KeyError:
            return None