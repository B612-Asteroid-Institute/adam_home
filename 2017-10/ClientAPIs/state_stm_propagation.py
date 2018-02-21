"""
@author: vivek
@todo: change all printing to logging
"""

# General imports
import time
from datetime import datetime
from copy import deepcopy
import numpy as np

# Adam related imports
from adam import Batches
from adam import Batch
from adam import PropagationParams
from adam import OpmParams
from adam import BatchRunManager
from adam import RestRequests

# Constants
ISO8601Z = "%Y-%m-%dT%H:%M:%SZ"
DECIMAL_ISO8601 = "%Y-%m-%dT%H:%M:%S.%f"

def batch_time_string_from_datetime(dtobj):
    """Convert a datetime object into the format required  by ADAM batch
    
    Args:
        dtobj (datetime.datetime) - a datetime in UTC

    Returns:
        decimal_iso_Z (str) - e.g. 2017-10-04T00:00:00.123456Z
    """

    decimal_iso_Z = dtobj.strftime(DECIMAL_ISO8601) + 'Z'
    return decimal_iso_Z

def propagate_states(state_vectors, epoch_time, end_time):
    """Propagate states from one time to another

    Assume state epoch is the same as integration start time

    Args:
        sate_vectors (list of lists) - list of lists with 6 elements 
                                        [rx, ry, rz, vx, vy, vz]  [km, km/s]
        epoch_time (datetime.datetime) - epoch of state (UTC datetime)
        end_time (datetime.datetime) - time at which to end the simulation
                                        (UTC datetime)

    Returns:
        end_state_vectors (list of lists) - states at end of integration
                                            [rx, ry, rz, vx, vy, vz]  [km, km/s]
    """
    
    # Convert times to strings    
    epoch_time_str = batch_time_string_from_datetime(epoch_time)
    start_time_str = epoch_time_str
    end_time_str = batch_time_string_from_datetime(end_time)
    print("Propagating %i states to propagate from %s to %s" %
          (len(state_vectors), start_time_str, end_time_str))
          
    url = "https://pro-equinox-162418.appspot.com/_ah/api/adam/v1"
    rest = RestRequests(url)
    batches_module = Batches(rest)
    
    # Create batches from statevectors
    batches = []
    propagation_params = PropagationParams({
        'start_time': start_time_str,
        'end_time': end_time_str,
        'project_uuid': 'ffffffff-ffff-ffff-ffff-ffffffffffff'
    })
    for state_vector in state_vectors:
        opm_params = OpmParams({
            'epoch': start_time_str,
            'state_vector': state_vector
        })
        batches.append(Batch(propagation_params, opm_params))

    # submit batches and wait till they finish running   
    BatchRunManager(batches_module, batches).run()

    # Get final states
    end_state_vectors = []
    for batch in batches:
        end_state_vectors.append(batch.get_results().get_end_state_vector())

    return end_state_vectors

def evaluate_func_with_derivative(xk, func, *args):
    """Evaluate a function and do central differencing for the derivative

    The function has to take a list of input values and provide a list out outs
    e.g. it has to be able to propagate more than 1 state

    Args:
        xk (list) - list of floats. value where we have to evaluate
        func (callable) - function to evaluate
        *args (args, optional) - any other arguments to be passed to func

    Returns:
        yk (list) - output of func(xk)
        dy_dx_matrix (numpy.matrix) - matrix of dy/dx
    """

    epsilon = 1.0e-6  # normalized step size. TODO use as input
    min_abs_x = 1.0e-3  # only used if x is really small
    x_dim = len(xk)  # dimension of problem
    hs = []  # store deltas
    xs = []  # put in to function
    # [xk, xi+h, xi-h, xj+h, xj-h,...]
    xs.append(xk)
    # we are using central differencing
    for i in range(0, x_dim):
        x_i = xk[i]
        h_i = max(abs(x_i), min_abs_x) * epsilon
        hs.append(h_i)
        x_copy_plus = deepcopy(xk)
        x_copy_plus[i] = x_i + h_i
        x_copy_minus = deepcopy(xk)
        x_copy_minus[i] = x_i - h_i
        xs.append(x_copy_plus)
        xs.append(x_copy_minus)

    # call the function with additional inputs
    ys = func(xs, *args)

    # This is the output
    yk = ys[0]
    y_dim = len(yk)

    # All the delta ys
    y_h = ys[1:]

    # make matrix of zeros
    dy_dx = np.zeros((y_dim, x_dim))

    for i in range(0, x_dim):
        h_i = hs[i]
        dy_dxi = (np.array(y_h[2*i]) - np.array(y_h[2*i+1])) / (2.0 * h_i)
        dy_dx[:, i] = dy_dxi

    dy_dx_matrix = np.matrix(dy_dx)

    return (yk, dy_dx_matrix)

def test_derivative_func(xyzs):
    """Function to test differntiation
    ref: https://www.mathworks.com/help/symbolic/jacobian.html
    TODO: convert this into a unit test
    """
    outs = []
    for xyz in xyzs:
        x = xyz[0]
        y = xyz[1]
        z = xyz[2]
        out = []
        out.append(x*y*z)
        out.append(y*y)
        out.append(x+z)
        outs.append(out)
    return outs

def main():

    state_vec = [130347560.13690618,
                 -74407287.6018632,
                 -35247598.541470632,
                 23.935241263310683,
                 27.146279819258538,
                 10.346605942591514]
    
    start_time = datetime(2017, 10, 4, 0, 0, 0 , 123456)
    end_time = datetime(2018, 10, 4, 0, 0, 0 , 123456)

    end_state, stm = evaluate_func_with_derivative(
        state_vec, propagate_states, start_time, end_time
    )

    print("State: ")
    print(end_state)
    print("STM: ")
    print(stm)

    return 0

if __name__ == "__main__":
    main()