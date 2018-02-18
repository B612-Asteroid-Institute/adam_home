from adam import Auth
from adam import Batch
from adam import Projects
from adam import RestRequests
from adam import AuthorizingRestProxy
import time
import os

# Authorize user TODO: move this somewhere else
# This should really be done under the hood and not exposed to the client
url = "https://pro-equinox-162418.appspot.com/_ah/api/adam/v1"
rest = RestRequests(url)
auth = Auth(rest)
tokenFile = os.getcwd() + '/token.txt'
# Opening with "a+" instead of "r" creates the file if it doesn't exist.
with open(tokenFile, "a+") as f:
    f.seek(0)
    token = f.readline().replace('\n', '')

try:
    if not auth.authorize(token):
        if auth.initial_authorization():
            with open(tokenFile, "w") as f:
                f.write(auth.get_token())
except RuntimeError as e:
    print('Encountered server error while attempting to authorize: ' + str(e))

if auth.get_token() == "":
    print('Could not authorize user.')
else:
    print('Welcome, ' + auth.get_user())
    
# auth.get_token() can now be used to authorize calls to other API methods.
auth_rest = AuthorizingRestProxy(rest, auth.get_token())

# Get projects TODO: move this somewhere else
projects = Projects(auth_rest)
project = projects.new_project('ffffffff-ffff-ffff-ffff-ffffffffffff', None, "parent")
child = projects.new_project(project.get_uuid(), None, "child")
print('Current projects, including newly-created parent and child:')
projects.print_projects()
projects.delete_project(child.get_uuid())
projects.delete_project(project.get_uuid())

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

# Create batch class
batch_run = Batch(rest)                                                 # initialize
batch_run.set_start_time('2017-10-04T00:00:00Z')                        # set propagation start time in ISO format
batch_run.set_end_time('2017-10-11T00:00:00Z')                          # set propagation end time in ISO format
batch_run.set_state_vector('2017-10-04T00:00:00.000Z', state_vec)       # set epoch (in ISO format) and state vector

# Optional parameters (uncomment to use)
# batch_run.set_propagator_uuid("00000000-0000-0000-0000-000000000002")    # set force model from config
# batch_run.set_step_size(3600, 'min')                                     # set step size and units
# batch_run.set_covariance(covariance, 'FACES', 3)                         # set covariance, type, and sigma
# batch_run.set_mass(500.5)                                                # set object mass
# batch_run.set_solar_rad_area(25.2)                                       # set object solar radiation area (m^2)
# batch_run.set_solar_rad_coeff(1.2)                                       # set object solar radiation coefficient
# batch_run.set_drag_area(33.3)                                            # set object drag area (m^2)
# batch_run.set_drag_coeff(2.5)                                            # set object drag coefficient
# batch_run.set_originator('Robot')                                        # set originator of run
# batch_run.set_object_name('TestObj')                                     # set object name
# batch_run.set_object_id('test1234')                                      # set object ID
# batch_run.set_description('some description')                            # set description of run

# Generate OPM and submit batch
print("\n")
print("Initial state: %s\n" % batch_run)
print
print("Submitted OPM:")
print(batch_run.generate_opm())
batch_run.submit()
print("\n")
print("Final state: %s" % batch_run)

# Wait until batch run is ready
while not batch_run.is_ready():
    print("Waiting...")
    time.sleep(5)

# Get final parts count
part_count = batch_run.get_parts_count()
print("Final state %s, part count %s\n" % (batch_run.get_calc_state(), part_count))

# Get ephemeris of specified part
part_to_get = 1
eph = batch_run.get_part_ephemeris(part_to_get)
print("Ephemeris:")
print(eph)

# Get the end state vector (uncomment to use)
#end_state_vector = batch_run.get_end_state_vector()
#print("State vector at the end of propagation:")
#print(end_state_vector)
#print("\n")
