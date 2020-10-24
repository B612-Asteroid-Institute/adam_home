"""
    batch_run_manager.py
"""

from adam.timer import Timer

from enum import Enum
import copy
import threading
from multiprocessing.dummy import Pool as ThreadPool


class State(Enum):
    INITIALIZED = 1
    SUBMITTED = 2
    COMPLETED = 3


class BatchRunManager(object):
    """
    Class for managing the state and propagation of a set of batch propagations.
    Responsible for submitting them, tracking and exposing their status during
    propagation, and retrieving their results.

    WARNING: this module is not thread-safe. The only supported simultaneous operation
    is calling get_latest_statuses() while a call to run() is ongoing.
    """

    def __init__(self, batches_module, batch_runs, do_timing=True, multi_threaded=True):
        """Sets up object that can manage the running and lifetime of the given batches.

        Args:
            batches_module (Batches): Object to use to communicate with server.
            batch_runs (list<Batch2>): Batches to be run/managed.
            do_timing (boolean): If true, timing information will be printed for various
                parts of batch lifetime (submission, running, results retrieval).
            multi_threaded (boolean): If true, operations that would benefit from
                multithreading such as submission or results retrieval will be
                multithreaded. Should generally be left true, but can be set to false if
                a guaranteed particular ordering is necessary (e.g. for tests).
        """
        self.batches_module = batches_module

        # Store the batch runs and check that they all belong to the same project.
        self.batch_runs = batch_runs
        projects = set([b.get_propagation_params().get_project_uuid() for b in batch_runs])
        if len(projects) != 1:
            print("All batches must belong to the same project to use the batch run manager")
            return
        self.project = projects.pop()

        self.state = State.INITIALIZED

        self.do_timing = do_timing
        if self.do_timing:
            self.timer = Timer()

        self.multi_threaded = multi_threaded

        # Cache the overall status here. Lock access so that state can be retrieved while
        # waiting for completion.
        self.cached_status = self._get_empty_cached_status()
        self.status_lock = threading.Lock()

    def __repr__(self):
        return "Batch run manager [%s: %s batches]" % (self.state, len(self.batch_runs))

    def get_batch_runs(self):
        """ Retrieves the batch runs managed by this object. Not safe to call while
            any other call is ongoing.
        """
        return self.batch_runs

    def get_latest_statuses(self):
        """ Retrieves the latest state of all batches managed by this object.
            Safe to call while a call to update_state(), wait_for_completion()
            or run() is ongoing.
        """
        self.status_lock.acquire()
        status = copy.deepcopy(self.cached_status)
        self.status_lock.release()
        return status

    def _get_empty_cached_status(self):
        return {
            'PENDING': [],
            'RUNNING': [],
            'COMPLETED': [],
            'FAILED': []}

    def _update_cached_status(self):
        status = self._get_empty_cached_status()
        for b in self.batch_runs:
            status[b.get_calc_state()].append(b.get_uuid())

        self.status_lock.acquire()
        self.cached_status = status
        self.status_lock.release()

    def _submit(self):
        if self.do_timing:
            self.timer.start("Submitting %s runs." % (len(self.batch_runs)))

        if not self.state == State.INITIALIZED:
            print("Error: runs already submitted, cannot resubmit.")
            self.timer.stop()
            return

        # Batch runs are most efficient when submitted in a single call because of the
        # overhead of authorization, connecting to the database, etc. The server takes
        # ~20 seconds to submit 500 batch runs. We don't want to take more time than that
        # because calls time out around 60 seconds.
        submission_batch_size = 500

        # Use as many threads as we have batches to submit, up to an arbitrary maximum
        # of 10, which allows us to submit 5000 batches in parallel.
        if self.multi_threaded:
            num_batches = round(len(self.batch_runs) / submission_batch_size) + 1
            threads = min(num_batches, 10)
        else:
            threads = 1

        def _submit_batches(i):
            # Grab all the creation parameters from the batch objects.
            runs = self.batch_runs[i:i+submission_batch_size]
            params = [[b.get_propagation_params(), b.get_opm_params()] for b in runs]

            # Call to the server to create the batches.
            summaries = self.batches_module.new_batches(params)

            # Update the batches with the resulting state summaries.
            for summary_i in range(len(summaries)):
                self.batch_runs[i + summary_i].set_state_summary(summaries[summary_i])

        pool = ThreadPool(threads)
        # Break up the batches into chunks and submit them in chunks. For fewer than
        # <submission_batch_size> runs, this just submits them all in one request on one
        # thread.
        pool.map(_submit_batches,
                 [i for i in range(0, len(self.batch_runs), submission_batch_size)])
        pool.close()
        pool.join()

        self._update_cached_status()

        if self.do_timing:
            self.timer.stop()

        self.state = State.SUBMITTED

    def _update_state(self):
        """ Updates the state of all batch runs managed by this object. When finished
            updating batch run state, sets the state of this object to COMPLETED if all
            managed runs are in a final state (COMPLETED or FAILED).
        """
        if self.state == State.INITIALIZED:
            print("Error: runs not yet submitted, no state to retrieve")
            return
        elif self.state == State.COMPLETED:
            # No update is necessary, since nothing changes once the state is COMPLETED.
            return

        # First, update the status of all batches.
        summaries_by_uuid = self.batches_module.get_summaries(self.project)

        for batch in self.batch_runs:
            batch.set_state_summary(summaries_by_uuid[batch.get_uuid()])

        # Then, if the state of this whole batch should be updated, do that.
        complete = True
        for b in self.batch_runs:
            if not b.get_calc_state() in ['COMPLETED', 'FAILED']:
                complete = False
                break
        if complete:
            self.state = State.COMPLETED

        self._update_cached_status()

    def _wait_for_completion(self):
        """ Waits for the completion of all the batches managed by this object. When this
            returns, all managed batches are guaranteed to be in a final state
            (COMPLETED or FAILED).
        """
        if self.do_timing:
            self.timer.start("Running.")

        while self.state != State.COMPLETED:
            self._update_state()

        if self.do_timing:
            self.timer.stop()

    def _get_results(self):
        if self.do_timing:
            self.timer.start("Retrieving propagation results.")

        def _get_results(i):
            b = self.batch_runs[i]
            results = self.batches_module.get_propagation_results(b.get_state_summary())
            b.set_results(results)

        if self.multi_threaded:
            threads = 5
        else:
            threads = 1
        pool = ThreadPool(threads)
        pool.map(_get_results, [i for i in range(len(self.batch_runs))])
        pool.close()
        pool.join()

        if self.do_timing:
            self.timer.stop()

    def run(self):
        self._submit()
        self._wait_for_completion()
        self._get_results()
        print("Run status: complete")
