from adam import Auth
from adam import Batch
from adam import Projects
from adam import RestRequests
from adam import AuthorizingRestProxy
from adam import LoggingRestProxy
import time
import os

rest = RestRequests("http://localhost:8080/_ah/api/adam/v1")
auth = Auth(rest)
tokenFile = os.getcwd() + '/token.txt'
# Opening with "a+" instead of "r" creates the file if it doesn't exist.
with open(tokenFile, "a+") as f:
    f.seek(0)
    token = f.read()

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
auth_rest = AuthorizingRestProxy(LoggingRestProxy(rest), auth.get_token())

projects = Projects(auth_rest)
projects.print_projects()
project = projects.new_project('ffffffff-ffff-ffff-ffff-ffffffffffff', None, "parent")
projects.print_projects()
child = projects.new_project(project.get_uuid(), None, "child")
projects.print_projects()
projects.delete_project(child.get_uuid())
projects.print_projects()
projects.delete_project(project.get_uuid())
projects.print_projects()

state_vec = [130347560.13690618,
             -74407287.6018632,
             -35247598.541470632,
             23.935241263310683,
             27.146279819258538,
             10.346605942591514]

batch_run = Batch()
batch_run.set_start_time('2017-10-04T00:00:00Z')
batch_run.set_end_time('2067-10-04T00:00:00Z')
batch_run.set_state_vector('2017-10-04T00:00:00.000Z', state_vec)

# Optional parameters (uncomment to use)
batch_run.set_propagator_uuid("00000000-0000-0000-0000-000000000002")    # Only Sun as point mass, nothing else
batch_run.set_step_size(3600, 'min')
batch_run.set_mass(500.5)
batch_run.set_solar_rad_area(25.2)
batch_run.set_solar_rad_coeff(1.2)
batch_run.set_drag_area(33.3)
batch_run.set_drag_coeff(2.5)
batch_run.set_originator('Robot')
batch_run.set_object_name('TestObj')
batch_run.set_object_id('test1234')
batch_run.set_description('some description')
#Total GET response size [https://pro-equinox-162418.appspot.com/_ah/api/adam/v1/batch/df246aca-f861-4d4b-8f45-1dd86725fb01/1]: 1764
print("Initial state %s" % batch_run)
print
print(batch_run.generate_opm())
batch_run.submit()
print
print("Final state %s" % batch_run)

while not batch_run.is_ready():
    print("State %s" % batch_run)
    time.sleep(1)

part_count = batch_run.get_parts_count()
print("Final state %s, part count %s" % (batch_run.get_calc_state(), part_count))
eph = batch_run.get_part_ephemeris(1)
print("Ephemeris")
print(eph[:1000])
