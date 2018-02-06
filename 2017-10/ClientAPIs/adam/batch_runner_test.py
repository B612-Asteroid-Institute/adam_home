from adam.batch_runner import BatchRunner
from adam.batch import Batch
from adam.project import Project

import unittest
    
class MockBatches:
    def __init__(self):
        self.expected_get_batch_states = []
        self.expected_new_batch = []
        
    def expect_get_batch_states(self, project, response):
        self.expected_get_batch_states.append([project, response])
    
    def expect_new_batch(self, batch):
        self.expected_new_batch.append(batch)
    
    def get_batch_states(self, project):
        if len(self.expected_get_batch_states) == 0:
            raise AssertionError("Did not expect any calls")
            
        expectation = self.expected_get_batch_states.pop(0)
        if not expectation[0].get_uuid() == project:
            raise AssertionError("Expected call to get_batch_states with " + expectation[0].get_uuid() + ", got " + project)
        
        return expectation[1]
        
    
    def new_batch(self, batch):
        expectation = self.expected_new_batch.pop(0)
        if not expectation == batch:
            raise AssertionError("Expected call to new_batch with " + expectation + ", got " + batch.get_uuid())
    
    def clear_expectations(self):
        if not len(self.expected_new_batch) == 0:
            raise AssertionError("Still expecting call to new_batch")
        if not len(self.expected_get_batch_states) == 0:
            raise AssertionError("Still expecting call to get_batch_states")

class MockBatch:
    def __init__(self, uuid):
        self.uuid = uuid
    
    def set_project(self, project):
        pass
        
    def get_uuid(self):
        return self.uuid

class BatchRunnerTest(unittest.TestCase):
    """Unit tests for batch runner.

    """

    def test_flow(self):
        batches = MockBatches()
        project = Project("p1", None, None, None)
        
        batch_runner = BatchRunner(batches, project)
        
        b1 = MockBatch("b1")
        batch_runner.add_batch(b1)
        
        batches.expect_new_batch(b1)
        batches.expect_get_batch_states(project, {"b1": "COMPLETED"})
        
        batch_runner.run_batches()
        
        batches.clear_expectations()
        
        batches.expect_new_batch(b1)
        batches.expect_get_batch_states(project, {"b1": "PENDING"})
        batches.expect_get_batch_states(project, {"b1": "RUNNING"})
        batches.expect_get_batch_states(project, {"b1": "RUNNING"})
        batches.expect_get_batch_states(project, {"b1": "COMPLETED"})
        
        batch_runner.run_batches()
        
        batches.clear_expectations()
        
        batches.expect_new_batch(b1)
        batches.expect_get_batch_states(project, {"b1": "PENDING"})
        batches.expect_get_batch_states(project, {"b1": "FAILED"})
        
        batch_runner.run_batches()
        
        batches.clear_expectations()

if __name__ == '__main__':
    unittest.main()
