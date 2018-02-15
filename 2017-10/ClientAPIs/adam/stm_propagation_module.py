"""
@author: vivek
@todo: change all printing to logging
"""

# General imports
from copy import deepcopy
import numdifftools as nd
import numpy as np

# Adam related imports
from adam import Batch2
from adam import BatchRunManager

class StmPropagationModule(object):
    def __init__(self, batches_module):
        self.batches_module = batches_module
    
    def __repr__(self):
        return "StmPropagationModule"

    def _propagate_states(self, state_vectors, propagation_params, opm_params_templ):
        """Propagate states using many initial state vectors.

        Args:
            state_vectors (list of lists):
                list of lists with 6 elements [rx, ry, rz, vx, vy, vz]  [km, km/s]
            propagation_params (PropagationParams):
                propagation-related parameters to be used for all propagations
            opm_params_templ (OpmParams):
                opm-related parameters to be used for all propagations, once with each
                of the given state vectors.

        Returns:
            end_state_vectors (list of lists):
                states at end of integration [rx, ry, rz, vx, vy, vz]  [km, km/s]
        """

        # Create batches from state vectors
        batches = []
        for state_vector in state_vectors:
            opm_params = deepcopy(opm_params_templ)
            opm_params.set_state_vector(state_vector)
            batches.append(Batch2(propagation_params, opm_params))

        # submit batches and wait till they finish running  
        runner = BatchRunManager(self.batches_module, batches)
        runner.run()

        # Get final states
        end_state_vectors = []
        for batch in batches:
            end_state_vectors.append(batch.get_results().get_end_state_vector())

        return end_state_vectors

    def _evaluate_func_with_derivative(self, xk, func, *args):
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
    
    def run_stm_propagation(self, propagation_params, opm_params):
        """ Generates a state transition matrix for the propagation described by the
            given parameters. Does so by nudging the state vector given in opm_params
            in several different directions and combining the results of propagating
            with the slightly different state vectors.
            
            Args:
                propagation_params (PropagationParams):
                    Propagation-related parameters for the STM propagations
                opm_params (OpmParams):
                    OPM-related parameters for the propagations, including the nominal
                    state vector that will be varied.
            
            Returns:
                end_state (list):
                    Final state vector of nominal propagation [rx, ry, rz, vx, vy, vz] 
                    [km, km/s]
                stm (matrix):
                    STM describing effect of changes to initial state on final state
        """
        end_state, stm = self._evaluate_func_with_derivative(
            opm_params.get_state_vector(),
            self._propagate_states,
            propagation_params,
            opm_params
        )
        
        return end_state, stm
    