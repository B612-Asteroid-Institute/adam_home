from adam import BatchRunner
import unittest

class BatchRunnerTest(unittest.TestCase):
    """Unit tests for batch runner.

    """
    
    class MockBatches:
        def __init__(self):
            self.expected_get_batch_states = []
            self.expected_new_batch = []
            
        def expect_get_batch_states(self, project, response):
            self.expected_get_batch_states.append([project, response])
        
        def get_batch_states(self, project):
            if len(self.expected_get_batch_states) == 0:
                raise AssertionError("Did not expect any calls")
                
            expectation = self.expected_get_batch_states.pop()
            
        
        def new_batch(self, batch):
            pass

    def test_flow(self):