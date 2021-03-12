
class ApsRestServiceResultsProcessor:
    """AdamProcessingService REST service to check job status and results"""

    def __init__(self, rest, project):
        self._rest = rest
        self._project = project

    def __repr__(self):
        return "Adam Results Processing Class"

    def check_status(self, job_uuid):
        """Check the status of a job.

        Args:
            job_uuid (str): the job id.

        Returns:
            str: the job status.
        """

        code, response = self._rest.get(f'/projects/{self._project}/jobs/{job_uuid}/status')
        if code != 200:
            raise RuntimeError("Server status code: %s; Response: %s" % (code, response))

        return response

    def get_results(self, job_uuid):
        """Get the results of a job.

        Args:
            job_uuid (str): The job id.

        Returns:
            str: The job result, in JSON format::

                {
                    "uuid": id of the result record (string),
                    "jobUuid": job id (string),
                    "outputSummaryJson": the output summary e.g. counts (json),
                    "outputDetailsJson": the output details e.g. final positions (json)
                }
        """

        code, response = self._rest.get(f'/projects/{self._project}/jobs/{job_uuid}/result')
        if code != 200:
            raise RuntimeError("Server status code: %s; Response: %s" % (code, response))

        return response