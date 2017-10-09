from adam import Batch
import time

state_vec = [130347560.13690618,
             -74407287.6018632,
             -35247598.541470632,
             23.935241263310683,
             27.146279819258538,
             10.346605942591514]

batch_run = Batch()
batch_run.set_start_time('2017-10-04T00:00:00Z')
batch_run.set_end_time('2017-10-11T00:00:00Z')
batch_run.set_state_vector('2017-10-04T00:00:00.000Z', state_vec)

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
