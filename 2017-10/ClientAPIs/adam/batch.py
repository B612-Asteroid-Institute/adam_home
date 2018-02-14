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
    
    def _build_batch_creation_data(self, batch_params, opm_params):
        data = {'start_time': batch_params.get_start_time(),
                'end_time': batch_params.get_end_time(),
                'step_duration_sec': batch_params.get_step_size(),
                'propagator_uuid': batch_params.get_propagator_uuid(),
                'project': batch_params.get_project_uuid(),
                'opm_string': opm_params.generate_opm()}

        if batch_params.get_description() is not None:
            data['description'] = batch_params.get_description()
        
        return data
    
    def new_batch(self, propagation_params, opm_params):
        data = self._build_batch_creation_data(propagation_params, opm_params)
        
        code, response = self._rest.post('/batch/', data)
        
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
        
        code, response = self._rest.post('/batches/', {'requests': batch_dicts})

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

        return PropagationPart(part_json)
        
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

class PropagationPart(object):
    def __init__(self, part):
        self._calc_state = part['calc_state']
        if self._calc_state in ['COMPLETED', 'FAILED']:
            self._ephemeris = part['stk_ephemeris']
        else:
            self._ephemeris = None
        self._error = part.get('error') or ''
    
    def __repr__(self):
        return "PropagationPart [%s]" % (self._calc_state)
    
    def get_calc_state(self):
        return self._calc_state
    
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
    
    def get_ephemerides(self):
        # Fills in None ephemerides for None parts
        return [p.get_ephemeris() if p is not None else None for p in self._parts]
    
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
        self._step_size = json.get('step_duration_sec')
        self._create_time = json.get('create_time')
        self._execute_time = json.get('execute_time')
        self._complete_time = json.get('complete_time')
        self._project = json.get('project')
        self._parts_count = json.get('parts_count')
        self._calc_state = json.get('calc_state')

    def __repr__(self):
        return "Batch %s" % (self._uuid)
    
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
        
    def get_project(self):
        return self._project
        
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
    
class Batch(object):
    def __init__(self, propagation_params, opm_params):
        self.propagation_params = propagation_params
        self.opm_params = opm_params
        self.state_summary = None
        self.results = None
    
    def get_propagation_params(self):
        return self.propagation_params
    
    def get_opm_params(self):
        return self.opm_params
    
    def get_state_summary(self):
        return self.state_summary
    
    def set_state_summary(self, state_summary):
        self.state_summary = state_summary
    
    def get_results(self):
        return self.results
    
    def set_results(self, results):
        self.results = results
    
    # Convenience method to get batch uuid.
    def get_uuid(self):
        if self.state_summary is None: return None
        return self.state_summary.get_uuid()
        
    # Convenience method to get batch calculation state.
    def get_calc_state(self):
        if self.state_summary is None: return None
        return self.state_summary.get_calc_state()

class BatchOld(object):
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