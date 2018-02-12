"""
    batch_runner.py
"""

import adam
from adam.timer import Timer
from adam.batch import Batches

import datetime
import threading
from multiprocessing.dummy import Pool as ThreadPool


class BatchRunner():
    # All batches are run in the given project.
    def __init__(self, batches, project):
        self.batches = batches
        self.project = project
        self.batch_runs = []
    
    def add_batch(self, batch_run):
        batch_run.set_project(self.project.get_uuid())
        self.batch_runs.append(batch_run)
    
    def get_batches_status(self):
        batch_runs_by_state = {
            'PENDING': [],
            'RUNNING': [],
            'COMPLETED': [],
            'FAILED': []}
        states = self.batches.get_batch_states(self.project.get_uuid())
        for batch in self.batch_runs:
            batch_runs_by_state[states[batch.get_uuid()]].append(batch.get_uuid())
        
        return batch_runs_by_state
    
    def _runs_in_states(self, batch_runs_by_state, states):
        total = 0
        for state in states:
            total = total + len(batch_runs_by_state[state])
        return total
    
    def _submit_batches(self, threads):
        step = 500
        def submit(i):
            self.batches.new_batches(self.batch_runs[i:i+step])
        
        pool = ThreadPool(threads)
        results = pool.map(submit, [i for i in range(0, len(self.batch_runs), step)])
        pool.close()
        pool.join()
    
    def _all_are_complete(self, batch_runs_by_state):
        return self._runs_in_states(batch_runs_by_state, ['COMPLETED', 'FAILED']) == len(self.batch_runs)
    
    def _all_are_pending(self, batch_runs_by_state):
        return self._runs_in_states(batch_runs_by_state, ['PENDING']) == len(self.batch_runs)
        
    def submit_batches(self, threads=1):
        timer = Timer()
        timer.start("Submitting " + str(len(self.batch_runs)) + " batches")
        self._submit_batches(threads)
        timer.stop()
    
    def wait_for_running(self):
        timer = Timer()
        timer.start("Waiting for running")
        batch_runs_by_state = self.get_batches_status()
        while self._all_are_pending(batch_runs_by_state):
            batch_runs_by_state = self.get_batches_status()
        timer.stop()
    
    def wait_for_finished(self):
        timer = Timer()
        timer.start("Running")
        batch_runs_by_state = self.get_batches_status()
        while not self._all_are_complete(batch_runs_by_state):
            batch_runs_by_state = self.get_batches_status()
        timer.stop()
    
    def run_batches(self, threads=1):
        self.submit_batches(threads)
        self.wait_for_running()
        self.wait_for_finished()
        