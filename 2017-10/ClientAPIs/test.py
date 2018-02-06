from adam import Auth
from adam import RestRequests
from adam import Batch
import time
import os

url = "https://adam-dev-193118.appspot.com/_ah/api/adam/v1"
rest = RestRequests(url)
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
    
# If non-empty, auth.get_token() can now be used to authorize calls to other API methods.

state_vec = [130347560.13690618,
             -74407287.6018632,
             -35247598.541470632,
             23.935241263310683,
             27.146279819258538,
             10.346605942591514]

covariance = [3.331349476038534e-04, + \
              4.618927349220216e-04, 6.782421679971363e-04, + \
             -3.070007847730449e-04, -4.221234189514228e-04, 3.231931992380369e-04, + \
             -3.349365033922630e-07, -4.686084221046758e-07, 2.484949578400095e-07, 4.296022805587290e-10, + \
             -2.211832501084875e-07, -2.864186892102733e-07, 1.798098699846038e-07, 2.608899201686016e-10, 1.767514756338532e-10, + \
             -3.041346050686871e-07, -4.989496988610662e-07, 3.540310904497689e-07, 1.869263192954590e-10, 1.008862586240695e-10, 6.224444338635500e-10]

batch_run = Batch()
batch_run.set_start_time('2017-10-04T00:00:00Z')
batch_run.set_end_time('2017-10-11T00:00:00Z')
batch_run.set_state_vector('2017-10-04T00:00:00.000Z', state_vec)

# Optional parameters (uncomment to use)
# batch_run.set_propagator_uuid("00000000-0000-0000-0000-000000000002")    # Only Sun as point mass, nothing else
# batch_run.set_step_size(3600, 'min')
# batch_run.set_covariance(covariance, 'FACES', 3)
# batch_run.set_mass(500.5)
# batch_run.set_solar_rad_area(25.2)
# batch_run.set_solar_rad_coeff(1.2)
# batch_run.set_drag_area(33.3)
# batch_run.set_drag_coeff(2.5)
# batch_run.set_originator('Robot')
# batch_run.set_object_name('TestObj')
# batch_run.set_object_id('test1234')
# batch_run.set_description('some description')

print("Initial state %s" % batch_run)
print
print(batch_run.generate_opm())
batch_run.submit()
print
print("Final state %s" % batch_run)

while not batch_run.is_ready():
    time.sleep(5)

part_count = batch_run.get_parts_count()
print("Final state %s, part count %s" % (batch_run.get_calc_state(), part_count))
eph = batch_run.get_part_ephemeris(1)
print("Ephemeris")
print(eph)
# end_state_vector = batch_run.get_end_state_vector()
# print("State vector at the end of propagation")
# print(end_state_vector)
