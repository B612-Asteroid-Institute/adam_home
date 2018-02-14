"""
    batch.py
"""

from adam.batch2 import Batch2
from adam.batch2 import Batches
from adam.batch2 import PropagationParams
from adam.batch2 import OpmParams
from adam.batch2 import StateSummary
from adam.rest_proxy import RestRequests
from datetime import datetime
from tabulate import tabulate

M2KM = 1E-3  # meters to kilometers

class Batch(object):
    """Module for a batch request

    This class is used for creating batch runs on the cloud

    """
    def __init__(self, rest):
        """Initializes attributes

        """
        propagation_params = PropagationParams({
            # Bit of a hack so that we can deal with start_time and end_time being
            # set separately later (before use).
            'start_time': None,
            'end_time': None
        })
        opm_params = OpmParams({
            'epoch': None,
            'state_vector': None
        })
        self._batch = Batch2(propagation_params, opm_params)
        self._batch_module = Batches(rest)

    def __repr__(self):
        """Printable representation of returned values from job run

        This function returns the printed uuid and calc state

        Args:
            None

        Returns:
            Printable representation of uuid and calc state (str)
        """
        return repr(self._batch)
        
    def set_description(self, description):
        """Sets the description of the run
        This function sets the description of the propagated run
        Args:
            description (str): description of the run
        Returns:
            None
        """
        self._batch.get_propagation_params()._description = description
    
    def set_project(self, project):
        self._batch.get_propagation_params()._project_uuid = project

    def set_originator(self, originator):
        """Sets the originator of the run
        This function sets the originator of the propagated run
        Args:
            originator (str): responsible entity for run
        Returns:
            None
        """
        self._batch.get_opm_params()._originator = originator

    def set_object_name(self, object_name):
        """Sets the object name
        This function sets the object's name for the propagation
        Args:
            object_name (str): name of object
        Returns:
            None
        """
        self._batch.get_opm_params()._object_name = object_name

    def set_object_id(self, object_id):
        """Sets the object ID
        This function sets the object's ID for the propagation
        Args:
            object_id (str): identification of object
        Returns:
            None
        """
        self._batch.get_opm_params()._object_id = object_id

    def set_state_vector(self, epoch, state_vector):
        """Set epoch and state vector
        This function sets the epoch and cartesian state vector (position and velocity)
        Args:
            epoch (str): the epoch associated with the state vector (IS0-8601 format)
            state_vector (list): an array with 6 elements [rx, ry, rz, vx, vy, vz]
        Returns:
            None
        """
        self._batch.get_opm_params()._epoch = epoch
        self._batch.get_opm_params()._state_vector = state_vector

    def set_start_time(self, start_time):
        """Set start time
        This function sets the start time for the propagation run
        Args:
            start_time (str): start time in ISO-8601 format (yyyy-MM-ddTHH:mm:ssZ)
        Returns:
            None
        """
        self._batch.get_propagation_params()._start_time = start_time

    def set_end_time(self, end_time):
        """Set end time
        This function sets the end time for the propagation run
        Args:
            end_time (str): end time in ISO-8601 format (yyyy-MM-ddTHH:mm:ssZ)
        Returns:
            None
        """
        self._batch.get_propagation_params()._end_time = end_time

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
        self._batch.get_propagation_params()._step_size = step_size

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
        self._batch.get_opm_params()._covariance = covariance
        self._batch.get_opm_params()._hypercube = hypercube
        self._batch.get_opm_params()._perturbation = perturbation

    def set_mass(self, mass):
        """Set object mass
        This function sets the object's mass for propagation
        Args:
            mass (float): object mass in kilograms
        Returns:
            None
        """
        self._batch.get_opm_params()._mass = mass

    def set_solar_rad_area(self, solar_rad_area):
        """Set object solar radiation area
        This function sets the object's solar radiation area for propagation
        Args:
            solar_rad_area (float): object solar radiation area in squared meters
        Returns:
            None
        """
        self._batch.get_opm_params()._solar_rad_area = solar_rad_area

    def set_solar_rad_coeff(self, solar_rad_coeff):
        """Set object solar radiation coefficient
        This function sets the object's solar radiation coefficient for propagation
        Args:
            solar_rad_coeff (float): object solar radiation coefficient
        Returns:
            None
        """
        self._batch.get_opm_params()._solar_rad_coeff = solar_rad_coeff

    def set_drag_area(self, drag_area):
        """Set object drag area
        This function sets the object's drag area for propagation
        Args:
            drag_area (float): object drag area in squared meters
        Returns:
            None
        """
        self._batch.get_opm_params()._drag_area = drag_area

    def set_drag_coeff(self, drag_coeff):
        """Set object drag coefficient
        This function sets the object's drag coefficient for propagation
        Args:
            drag_coeff (float): object drag coefficient
        Returns:
            None
        """
        self._batch.get_opm_params()._drag_coeff = drag_coeff

    def set_propagator_uuid(self, propagator_uuid):
        """Set propagator uuid
        This functions sets the propagator uuid for the desired force model
        See https://pro-equinox-162418.appspot.com/_ah/api/adam/v1/config for configurations
        Args:
            propagator_uuid (str): configuration uuid to set for the propagator
        Returns:
            None
        """
        self._batch.get_propagation_params()._propagator_uuid = propagator_uuid
    
    def set_uuid_for_testing(self, uuid):
        if self._batch.get_state_summary() is None:
            # Hack for testing. Don't imitate this.
            self._batch.set_state_summary(StateSummary({
                'uuid': None,
                'calc_state': None
            }))
        self._batch.get_state_summary()._uuid = uuid
        
    def set_calc_state_for_testing(self, calc_state):
        if self._batch.get_state_summary() is None:
            # Hack for testing. Don't imitate this.
            self._batch.set_state_summary(StateSummary({
                'uuid': None,
                'calc_state': None
            }))
        self._batch.get_state_summary()._calc_state = calc_state
    
    def set_parts_count_for_testing(self, parts_count):
        if self._batch.get_state_summary() is None:
            # Hack for testing. Don't imitate this.
            self._batch.set_state_summary(StateSummary({
                'uuid': None,
                'calc_state': None
            }))
        self._batch.get_state_summary()._parts_count = parts_count
        
    def set_epoch_for_testing(self, epoch):
        self._batch.get_opm_params()._epoch = epoch
    
    def set_state_vector_for_testing(self, state_vector):
        self._batch.get_opm_params()._state_vector = state_vector
    
    def generate_opm(self):
        """Generate an OPM string
        This function generates a single OPM string from defined parameters (CCSDS format)
        Args:
            None
        Returns:
            OPM (str)
        """
        return self._batch.get_opm_params().generate_opm()

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
        if self._batch.get_propagation_params()._start_time is None:
            raise KeyError('Need start_time!')
        if self._batch.get_propagation_params()._end_time is None:
            raise KeyError('Need end_time!')
        if self._batch.get_opm_params()._epoch is None:
            raise KeyError('Need epoch!')
        if self._batch.get_opm_params()._state_vector is None:
            raise KeyError('Need state_vector!')
            
        state_summary = self._batch_module.new_batch(
            self._batch.get_propagation_params(), self._batch.get_opm_params())
        
        self._batch.set_state_summary(state_summary)

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
        if self._batch.get_uuid() is None:
            raise KeyError("Need uuid!")
            
        self._batch.set_state_summary(
            self._batch_module.get_summary(self._batch.get_uuid()))

        return self._batch.get_calc_state()

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
        return self._batch.get_calc_state()

    def get_parts_count(self):
        """Get parts count
        This function just returns the parts count
        Args:
            None
        Returns:
            parts_count (int)
        """
        return self._batch.get_state_summary()._parts_count

    def get_uuid(self):
        """Grab the UUID
        This function just returns the UUID of the run
        Args:
            None
        Returns:
            uuid (str)
        """
        return self._batch.get_uuid()

    def _load_results(self):
        if self._batch.get_results() is not None:
            # Already loaded the results. They won't change.
            return

        results = self._batch_module.get_propagation_results(
            self._batch.get_state_summary())
        for i in range(len(results.get_parts())):
            if results.get_parts()[i] is None:
                raise RuntimeError("Could not retrieve result part %s" % (i + 1))
        self._batch.set_results(results)
    
    def _load_part(self, index):
        """Load part
        This function attempts to load the part and store it in the loaded parts. It will first try to check if the run
        has completed and if the index value is valid. It will then check if the part already exists and return it
        if it does. Otherwise, it will attempt to grab the part from the run on the server and return 'None' if the job
        has not returned a successful code error.
        Args:
            index (int): part index of job (1 for regular job, > 1 for jobs with covariance)
        Returns:
            part (PropagationResultPart): specific part run
        Raises:
            KeyError: if part is 'None'
            IndexError: if provided index is out of bounds
        """
        if index < 1 or index > self._batch.get_state_summary()._parts_count:
            raise IndexError
        
        self._load_results()
        return self._batch.get_results().get_parts()[index - 1]
        
    def get_part_error(self, index):
        """Get error from specified part
        This function loads the part (json response) that is stored and grabs its code error
        Args:
            index (int): part index of job (1 for regular job, > 1 for jobs with covariance)
        Returns:
            Either the part error (str) or None
        """

        # Load the part from the given index
        return self._load_part(index).get_error()

    def get_part_state(self, index):
        """Get calc state from specified part
        This function loads the part (json response) that is stored and grabs its calc state
        Args:
            index (int): part index of job (1 for regular job, > 1 for jobs with covariance)
        Returns:
            Either the calc state (str) or None
        """

        # Load the part from the given index
        return self._load_part(index).get_calc_state()

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
        return self._load_part(index).get_ephemeris()

    def get_end_state_vector(self):
        """Get the end state vector as a 6d list in [km, km/s]
        This function first grabs the STK ephemeris from the final part
        The final state entry is returned as an array
        Args:
        Returns:
            state_vector (list) - an array with 6 elements [rx, ry, rz, vx, vy, vz]
                                  [km, km/s]
        """
        self._load_results()
        return self._batch.get_results().get_end_state_vector()