from adam import Batch
from adam import Batches
from adam import BatchRunManager
from adam import PropagationParams
from adam import OpmParams
from adam import Projects
from adam import RestRequests
from adam import AuthorizingRestProxy
import time
import os

url = "https://pro-equinox-162418.appspot.com/_ah/api/adam/v1"
 # Reads your token from a file in current directory. For instructions on getting a token, see auth_demo notebook.
token = open(os.getcwd() + '/token.txt').read()
auth_rest = AuthorizingRestProxy(RestRequests(url), token)

# Example inputs

# 6x1 state vector (position [km], velocity [km/s])
state_vec = [130347560.13690618,
             -74407287.6018632,
             -35247598.541470632,
             23.935241263310683,
             27.146279819258538,
             10.346605942591514]

# Lower triangular covariance matrix (21 elements in a list)
covariance = [3.331349476038534e-04, + \
              4.618927349220216e-04, 6.782421679971363e-04, + \
             -3.070007847730449e-04, -4.221234189514228e-04, 3.231931992380369e-04, + \
             -3.349365033922630e-07, -4.686084221046758e-07, 2.484949578400095e-07, 4.296022805587290e-10, + \
             -2.211832501084875e-07, -2.864186892102733e-07, 1.798098699846038e-07, 2.608899201686016e-10, 1.767514756338532e-10, + \
             -3.041346050686871e-07, -4.989496988610662e-07, 3.540310904497689e-07, 1.869263192954590e-10, 1.008862586240695e-10, 6.224444338635500e-10]

# Create batch parameters. Uncomment to use.

propagation_params = PropagationParams({
    'start_time': '2017-10-04T00:00:00Z',   # propagation start time in ISO format
    'end_time': '2017-10-11T00:00:00Z',     # propagation end time in ISO format

    'project_uuid': 'ffffffff-ffff-ffff-ffff-ffffffffffff',

#     'step_size': 60 * 60,  # step size (seconds)
#     'propagator_uuid': '00000000-0000-0000-0000-000000000002',  # force model
#     'description': 'some description'       # description of run
})
opm_params = OpmParams({
    'epoch': '2017-10-04T00:00:00Z',
    'state_vector': state_vec,
            
#     'mass': 500.5,              # object mass
#     'solar_rad_area': 25.2,     # object solar radiation area (m^2)
#     'solar_rad_coeff': 1.2,     # object solar radiation coefficient
#     'drag_area': 33.3,          # object drag area (m^2)
#     'drag_coeff': 2.5,          # object drag coefficient
    
#     'covariance': covariance,   # object covariance
#     'perturbation': 3,          # sigma perturbation on state vector
#     'hypercube': 'FACES',       # hypercube propagation type
    
#     'originator': 'Robot',      # originator of run
#     'object_name': 'TestObj',   # object name
#     'object_id': 'test1234',    # object ID
})
batch = Batch(propagation_params, opm_params)
print("Submitting OPM:")
print(batch.get_opm_params().generate_opm())

# Submit and wait until batch run is ready
batches_module = Batches(auth_rest)
BatchRunManager(batches_module, [batch]).run()

# Get final parts count
parts_count = batch.get_state_summary().get_parts_count()
print("Final state: %s, part count %s\n" % (batch.get_calc_state(), parts_count))

# Get ephemeris of specified part
part_to_get = 0
eph = batch.get_results().get_parts()[part_to_get].get_ephemeris()
print("Ephemeris:")
print(eph)

# Get the end state vector (uncomment to use)
# end_state_vector = batch.get_results().get_end_state_vector()
# print("State vector at the end of propagation:")
# print(end_state_vector)
# print("\n")
