from adam.batch_run_manager import BatchRunManager
from adam.batch import Batch2
from adam.batch import PropagationParams
from adam.batch import OpmParams
from adam.batch import StateSummary
from adam.batch import PropagationResults

import unittest
    
class MockBatches:
    def __init__(self):
        self.expected_get_results = []
        self.expected_get_summaries = []
        self.expected_new_batch = []
    
    def expect_get_results(self, batch, response):
        self.expected_get_results.append([batch, response])
        
    def expect_get_summaries(self, project, response):
        self.expected_get_summaries.append([project, response])
    
    def expect_new_batch(self, batch, response):
        self.expected_new_batch.append([batch, response])
    
    def get_propagation_results(self, batch):
        if len(self.expected_get_results) == 0:
            raise AssertionError("Did not expect any calls")
            
        expectation = self.expected_get_results.pop(0)
        if not expectation[0] == batch:
            raise AssertionError("Expected call to get_propagation_results with %s, got %s" %
                (expectation[0], batch))
        
        return expectation[1]
        
    def get_summaries(self, project):
        if len(self.expected_get_summaries) == 0:
            raise AssertionError("Did not expect any calls")
            
        expectation = self.expected_get_summaries.pop(0)
        if not expectation[0] == project:
            raise AssertionError("Expected call to get_summaries with %s, got %s" %
                (expectation[0], project))
        
        return expectation[1]
        
    def new_batches(self, batch_params):
        return [self.new_batch(b[0], b[1]) for b in batch_params]
        
    def new_batch(self, propagation_params, opm_params):
        expectation = self.expected_new_batch.pop(0)
        if not expectation[0].get_propagation_params() == propagation_params and \
            expectations[0].get_opm_params() == opm_params:
            raise AssertionError("Expected call to new_batch with %, got %" %
                (expectation[0], batch.get_uuid()))
            
        return expectation[1]
    
    def clear_expectations(self):
        if not len(self.expected_new_batch) == 0:
            raise AssertionError("Still expecting call to new_batch")
        if not len(self.expected_get_summaries) == 0:
            raise AssertionError("Still expecting call to get_batch_states")

def get_dummy_batch(project):
    return Batch2(PropagationParams({
        'start_time': 'today',
        'end_time': 'tomorrow',
        'project_uuid': project
    }), OpmParams({
        'epoch': 'today',
        'state_vector': [1, 2, 3, 4, 5, 6]
    }))

class BatchRunnerTest(unittest.TestCase):
    """Unit tests for batch runner.

    """

    def test_flow(self):
        batches = MockBatches()
        
        b1 = get_dummy_batch("p1")
        pending_state = StateSummary({'uuid': 'b1', 'calc_state': 'PENDING'})
        running_state = StateSummary({'uuid': 'b1', 'calc_state': 'RUNNING'})
        completed_state = StateSummary({'uuid': 'b1', 'calc_state': 'COMPLETED'})
        failed_state = StateSummary({'uuid': 'b1', 'calc_state': 'FAILED'})
        results = PropagationResults([])
        
        batches.expect_new_batch(b1, pending_state)
        batches.expect_get_summaries("p1", {"b1": completed_state})
        batches.expect_get_results(completed_state, results)
        
        batch_runner = BatchRunManager(batches, [b1], "p1")
        batch_runner.run()
        self.assertEqual(b1.get_state_summary(), completed_state)
        self.assertEqual(b1.get_results(), results)
        
        batches.clear_expectations()
        
        batches.expect_new_batch(b1, pending_state)
        batches.expect_get_summaries("p1", {"b1": pending_state})
        batches.expect_get_summaries("p1", {"b1": running_state})
        batches.expect_get_summaries("p1", {"b1": running_state})
        batches.expect_get_summaries("p1", {"b1": completed_state})
        batches.expect_get_results(completed_state, results)
        
        batch_runner = BatchRunManager(batches, [b1])
        batch_runner.run()
        self.assertEqual(b1.get_state_summary(), completed_state)
        self.assertEqual(b1.get_results(), results)
        
        batches.clear_expectations()
        
        batches.expect_new_batch(b1, pending_state)
        batches.expect_get_summaries("p1", {"b1": pending_state})
        batches.expect_get_summaries("p1", {"b1": failed_state})
        batches.expect_get_results(failed_state, results)
        
        batch_runner = BatchRunManager(batches, [b1])
        batch_runner.run()
        self.assertEqual(b1.get_state_summary(), failed_state)
        self.assertEqual(b1.get_results(), results)
        
        batches.clear_expectations()

if __name__ == '__main__':
    unittest.main()
