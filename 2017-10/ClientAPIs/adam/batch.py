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
    
    def _build_batch_creation_data(self, propagation_params, opm_params):
        data = {'start_time': propagation_params.get_start_time(),
                'end_time': propagation_params.get_end_time(),
                'step_duration_sec': propagation_params.get_step_size(),
                'propagator_uuid': propagation_params.get_propagator_uuid(),
                'project': propagation_params.get_project_uuid(),
                'opm_string': opm_params.generate_opm()}

        if propagation_params.get_description() is not None:
            data['description'] = propagation_params.get_description()
        
        return data
    
    def new_batch(self, propagation_params, opm_params):
        data = self._build_batch_creation_data(propagation_params, opm_params)
        
        code, response = self._rest.post('/batch', data)
        
        if code != 200:
            raise RuntimeError("Server status code: %s; Response: %s" % (code, response))
        
        return StateSummary(response)
    
    def new_batches(self, param_pairs):
        """ Expects a list of pairs of [propagation_params, opm_params].
            Returns a list of batch summaries for the submitted batches in the same order.
        """
        batch_dicts = []
        for pair in param_pairs:
            batch_dicts.append(self._build_batch_creation_data(pair[0], pair[1]))
        
        code, response = self._rest.post('/batches', {'requests': batch_dicts})

        # Check error code
        if code != 200:
            raise RuntimeError("Server status code: %s; Response: %s" % (code, response))

        if len(param_pairs) != len(response['requests']):
            raise RuntimeError("Expected %s results, only got %s" % (len(param_pairs), len(response['requests'])))
        
        # Store response values
        summaries = []
        for i in range(len(response['requests'])):
            summaries.append(StateSummary(response['requests'][i]))
        
        return summaries
        
    def delete_batch(self, uuid):
        code = self._rest.delete('/batch/' + uuid)
        
        if code != 204:
            raise RuntimeError("Server status code: %s" % (code))
    
    def get_summary(self, uuid):
        code, response = self._rest.get('/batch/' + uuid)
        
        if code == 404:
            return None
        elif code != 200:
            raise RuntimeError("Server status code: %s; Response: %s" % (code, response))
        
        return StateSummary(response)
    
    def _get_summaries(self, project):
        code, response = self._rest.get('/batch?project_uuid=' + project)
            
        if code != 200:
            raise RuntimeError("Server status code: %s; Response: %s" % (code, response))
        
        return response['items']
    
    def get_summaries(self, project):
        summaries = {} 
        for s in self._get_summaries(project):
            summaries[s['uuid']] = StateSummary(s)
        return summaries
    
    def print_summaries(self, project, keys="batch_uuid,calc_state"):
        batches = self._get_summaries(project)
        
        print(tabulate(batches, headers=keys, tablefmt="fancy_grid"))

    def _get_part(self, state_summary, index):
        # Parts IDs are 1-indexed, not 0-indexed.
        url = '/batch/' + state_summary.get_uuid() + '/' + str(index + 1)
        code, part_json = self._rest.get(url)

        if code == 404:    # Not found
            return None
        if code != 200:
            raise RuntimeError("Server status code: %s" % (code))

        return PropagationResultPart(part_json)
        
    def get_propagation_results(self, state_summary):
        """ Returns a PropagationResults object with as many PropagationPart objects as 
            the state summary  claims to have parts, or raises an error. Note that if 
            state of given summary is not 'COMPLETED' or 'FAILED', not all parts are 
            guaranteed to exist or to have an ephemeris.
        """
        if state_summary.get_parts_count() < 1:
            ###### Is there a better way to communicate errors?
            print("Unable to retrieve results for batch with no parts")
            return None
            
        parts = [self._get_part(state_summary, i) 
            for i in range(state_summary.get_parts_count())]
        return PropagationResults(parts)

class PropagationResultPart(object):
    def __init__(self, part):
        self._calc_state = part['calc_state']
        self._part_index = part['part_index']
        self._ephemeris = part.get('stk_ephemeris')
        self._error = part.get('error')
    
    def __repr__(self):
        return "PropagationPart [%s]" % (self._calc_state)
    
    def get_calc_state(self):
        return self._calc_state
    
    def get_part_index(self):
        return self._part_index
    
    def get_error(self):
        return self._error
    
    def get_ephemeris(self):
        return self._ephemeris
        
class PropagationResults(object):

    M2KM = 1E-3  # meters to kilometers

    def __init__(self, parts):
        if (len(parts) < 1):
            print("Must provide at least one part.")
            return
            
        self._parts = parts
    
    def __repr__(self):
        return "Propagation results with %s parts" % (len(self._parts))
    
    def get_parts(self):
        return self._parts
    
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
        part = self._parts[-1]
        if part is None:
            print("Cannot compute final state vector from nonexistent final part")
            return None
        state = part.get_calc_state()
        if (state != 'COMPLETED'):
            print("Cannot compute final state vector from part in state %s" % (state))
            return None
        
        stk_ephemeris = part.get_ephemeris()  # Guaranteed to exist if state == COMPLETED
    
        split_ephem = stk_ephemeris.splitlines()
        state_vectors = []
        for line in split_ephem:
            split_line  = line.split()
            # It's a state if it has more than 7 elements
            if len(split_line) >= 7:
                state_vector = [(float(i) * self.M2KM) for i in split_line]
                # Ignore time
                state_vectors.append(state_vector[1:7])     
        
        # We want the last element
        return state_vectors[-1]
        
class StateSummary(object):
    def __init__(self, json):
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
        """
        self._start_time = params['start_time']  # Required.
        self._end_time = params['end_time']  # Required.
        self._step_size = params.get('step_size') or 86400
        self._propagator_uuid = params.get('propagator_uuid') or self.DEFAULT_CONFIG_ID
        self._project_uuid = params.get('project_uuid')
        self._description = params.get('description')
    
    def __repr__(self):
        return "Batch params [%s, %s, %s, %s, %s, %s]" % (self._start_time, self._end_time, self._step_size, self._propagator_uuid, self._project_uuid, self._description)
    
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
            
            --- epoch and state_vector are required! ---
            epoch (str): the epoch associated with the state vector (IS0-8601 format)
            state_vector (list): an array with 6 elements [rx, ry, rz, vx, vy, vz] 
                representing the position and velocity vector of the object.
        
            originator (str): responsible entity for run (default: 'ADAM_User')
            object_name (str): name of object (default: 'dummy')
            object_id (str): identification of object (default: '001')
            
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

        """
        self._epoch = params['epoch']  # Required.
        self._state_vector = params['state_vector']  # Required.
        
        self._originator = params.get('originator') or 'ADAM_User'
        self._object_name = params.get('object_name') or 'dummy'
        self._object_id = params.get('object_id') or '001'
        
        self._mass = params.get('mass') or 1000
        self._solar_rad_area = params.get('solar_rad_area') or 20
        self._solar_rad_coeff = params.get('solar_rad_coeff') or 1
        self._drag_area = params.get('drag_area') or 20
        self._drag_coeff = params.get('drag_coeff') or 2.2
        
        self._covariance = params.get('covariance')
        self._perturbation = params.get('perturbation')
        self._hypercube = params.get('hypercube')
    
    def __repr__(self):
        return "Opm %s" % self.generate_opm()
    
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
    
class Batch2(object):
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
        if self._state_summary is None: return None
        return self._state_summary.get_uuid()
        
    # Convenience method to get batch calculation state.
    def get_calc_state(self):
        if self._state_summary is None: return None
        return self._state_summary.get_calc_state()


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