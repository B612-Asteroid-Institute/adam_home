"""
    runnable_manager.py
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


class RunnableManager(object):
    """
    Class for managing the state of a set of runnables.
    Responsible for submitting them, tracking and exposing their status during
    propagation, and retrieving their results.

    WARNING: this module is not thread-safe. The only supported simultaneous operation
    is calling get_latest_statuses() while a call to run() is ongoing.
    """

    def __init__(self, runnables_module, runnables, project_uuid,
                 do_timing=True, multi_threaded=True):
        """Sets up object that can manage the running and lifetime of the given batches.

        Args:
            runnables_module: Object to use to communicate with server. Should be subclass of
                AdamObjects and should implement create, get, and update_with_results.
            runnables (list<object>): Runnable objects to be run/managed. Should implement get_uuid.
            project_uuid (string): The uuid of the project in which these runnables should be run.
            do_timing (boolean): If true, timing information will be printed for various
                parts of batch lifetime (submission, running, results retrieval).
            multi_threaded (boolean): If true, operations that would benefit from
                multithreading such as submission or results retrieval will be
                multithreaded. Should generally be left true, but can be set to false if
                a guaranteed particular ordering is necessary (e.g. for tests).
        """
        self.runnables_module = runnables_module
        self.runnables = runnables
        self.project_uuid = project_uuid

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
        return "Runnable manager [%s: %s runnables]" % (self.state, len(self.runnables))

    def get_runnables(self):
        """ Retrieves the runnables managed by this object. Not safe to call while
            any other call is ongoing.
        """
        return self.runnables

    def get_latest_statuses(self):
        """ Retrieves the latest state of all runnables managed by this object.
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
        for r in self.runnables:
            status[r.get_runnable_state().get_calc_state()
                   ].append(r.get_uuid())

        self.status_lock.acquire()
        self.cached_status = status
        self.status_lock.release()

    def _submit(self):
        if self.do_timing:
            self.timer.start("Submitting %s runnables." %
                             (len(self.runnables)))

        if not self.state == State.INITIALIZED:
            print("Error: runnables already submitted, cannot resubmit.")
            self.timer.stop()
            return

        # Insert all the runnables server-side.
        import time
        count = 0
        for r in self.runnables:
            self.runnables_module.insert(r, self.project_uuid)
            count = count + 1
            if count % 10 == 0:
                print('Inserted ' + str(count) + ' runnables')
            time.sleep(.5)

        # TODO: support batched submission.

        # # Batch runs are most efficient when submitted in a single call because of the
        # # overhead of authorization, connecting to the database, etc. The server takes
        # # ~20 seconds to submit 500 batch runs. We don't want to take more time than that
        # # because calls time out around 60 seconds.
        # submission_batch_size = 500

        # # Use as many threads as we have batches to submit, up to an arbitrary maximum
        # # of 10, which allows us to submit 5000 batches in parallel.
        # if self.multi_threaded:
        #     num_batches = round(len(self.batch_runs) / submission_batch_size) + 1
        #     threads = min(num_batches, 10)
        # else:
        #     threads = 1

        # def _submit_batches(i):
        #     # Grab all the creation parameters from the batch objects.
        #     runs = self.batch_runs[i:i+submission_batch_size]
        #     params = [[b.get_propagation_params(), b.get_opm_params()] for b in runs]

        #     # Call to the server to create the batches.
        #     summaries = self.batches_module.new_batches(params)

        #     # Update the batches with the resulting state summaries.
        #     for summary_i in range(len(summaries)):
        #         self.batch_runs[i + summary_i].set_state_summary(summaries[summary_i])

        # pool = ThreadPool(threads)
        # # Break up the batches into chunks and submit them in chunks. For fewer than
        # # <submission_batch_size> runs, this just submits them all in one request on one
        # # thread.
        # pool.map(_submit_batches,
        #          [i for i in range(0, len(self.batch_runs), submission_batch_size)])
        # pool.close()
        # pool.join()

        # self._update_cached_status()

        if self.do_timing:
            self.timer.stop()

        self.state = State.SUBMITTED

    def _update_state(self):
        """ Updates the state of all runnables managed by this object. When finished
            updating runnable state, sets the state of this object to COMPLETED if all
            managed runnables are in a final state (COMPLETED or FAILED).
        """
        if self.state == State.INITIALIZED:
            print("Error: runnables not yet submitted, no state to retrieve")
            return
        elif self.state == State.COMPLETED:
            # No update is necessary, since nothing changes once the state is COMPLETED.
            return

        # First, update the status of all runnables.
        runnable_states = self.runnables_module.get_runnable_states(
            self.project_uuid)
        runnable_states_by_uuid = {}
        for runnable_state in runnable_states:
            runnable_states_by_uuid[runnable_state.get_uuid()] = runnable_state

        for runnable in self.runnables:
            runnable.set_runnable_state(
                runnable_states_by_uuid[runnable.get_uuid()])

        # Then, if the state of this whole batch should be updated, do that.
        complete = True
        for runnable in self.runnables:
            if not runnable.get_runnable_state().get_calc_state() in ['COMPLETED', 'FAILED']:
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

    def _get_results(self, get_child_results):
        if self.do_timing:
            self.timer.start("Retrieving runnable results.")

        def _get_results(i):
            r = self.runnables[i]
            self.runnables_module.update_with_results(r)
            if get_child_results:
                r.set_children(self.runnables_module.get_children(r.get_uuid()))

        if self.multi_threaded:
            threads = 5
        else:
            threads = 1
        pool = ThreadPool(threads)
        pool.map(_get_results, [i for i in range(len(self.runnables))])
        pool.close()
        pool.join()

        if self.do_timing:
            self.timer.stop()

    def run(self, get_child_results=True):
        self._submit()
        self._wait_for_completion()
        self._get_results(get_child_results)
