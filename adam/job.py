"""
    job.py
"""
import json
import urllib
import datetime
from dateutil import parser as dateparser
from adam import Project, AuthenticatingRestProxy, RestRequests


class Job(object):
    """Job class.

    An ADAM Project is like captures a computational run in our services.
    """

    def __init__(self, uuid, project_id=None, object_id=None, user_defined_id=None, description=None, job_type=None,
                 input_json=None, submission_time=None, execution_start=None, completion_time=None, status=None):
        self._uuid = uuid
        self._project_id = project_id
        self._object_id = object_id
        self._user_defined_id = user_defined_id
        self._description = description
        self._job_type = job_type
        self._input_json = input_json
        self._submission_time = submission_time
        self._execution_start = execution_start
        self._completion_time = completion_time
        self._status = status

    def __repr__(self):
        return (
            f"Job(object_id={self._object_id}, user_defined_id={self._user_defined_id}, "
            f"description={self._description}, job_type={self._job_type},"
            f"status={self._status}, submission_time={self._submission_time},"
            f"execution_start={self._execution_start}, completion_time={self._completion_time},"
            f"input_json={self._input_json},uuid={self._uuid}, project_id={self._project_id}, )")

    def get_uuid(self):
        return self._uuid

    def get_project_id(self):
        return self._project_id

    def get_object_id(self):
        return self._object_id

    def get_user_defined_id(self):
        return self._user_defined_id

    def get_description(self):
        return self._description

    def get_job_type(self):
        return self._job_type

    def get_input_json(self):
        return json.loads(self._input_json)

    def get_input_json_string(self):
        return self._input_json

    def get_submission_time(self):
        return self._submission_time

    def get_execution_start(self):
        return self._execution_start

    def get_completion_time(self):
        return self._completion_time

    def get_status(self):
        return self._status

class JobsClient(object):
    """Module for managing jobs.

    """

    def __init__(self, rest=AuthenticatingRestProxy(RestRequests())):
        """Initialize the Jobs API client.

        Args:
            rest (RestProxy): a RestProxy that makes calls to the ADAM API.
        """
        self._rest = rest

    def get_jobs(self, project, status=None, object_id=None, user_defined_id=None, description=None,
                  earliest_submission_datetime=None, latest_submission_datetime=None):
        """Finds jobs based on one or more of the specified fields

        Args:
            project (str | Project): (Required) The workspace (project) id or a Project object
            status (str): (Optional) The status field looking for (can have wildcards)
            object_id (str): (Optional) The object ID field looking for (can have wildcards)
            user_defined_id (str): (Optional) The user ID field looking for (can have wildcards)
            description (str): (Optional) The description field looking for (can have wildcards)
            earliest_submission_datetime (datetime): (Optional) Earlist submission date/time interested in
            latest_submission_datetime (datetime): (Optional) Earlist submission date/time interested in

        Returns:
            list: a list of jobs for the project that match that criteria.
        """

        project_id = project.get_uuid() if type(project) is Project else project
        query_parameters = []

        if (status is not None):
            query_parameters.append(f"status={urllib.parse.quote_plus(status)}")

        if (object_id is not None):
            query_parameters.append(f"objectId={urllib.parse.quote_plus(object_id)}")

        if (user_defined_id is not None):
            query_parameters.append(f"userDefinedId={urllib.parse.quote_plus(user_defined_id)}")

        if (description is not None):
            query_parameters.append(f"description={urllib.parse.quote_plus(description)}")

        if (earliest_submission_datetime is not None):
            if type(earliest_submission_datetime) is not datetime.datetime:
                raise TypeError("Earliest submission date time needs to be a datetime object")
            query_parameters.append(f"earliestSubmissionDateTime={earliest_submission_datetime.isoformat()}")

        if (latest_submission_datetime is not None):
            if type(latest_submission_datetime) is not datetime.datetime:
                raise TypeError("Earliest submission date time needs to be a datetime object")
            query_parameters.append(f"latestSubmissionDateTime={latest_submission_datetime.isoformat()}")

        query_string = "&".join(query_parameters)
        request_path = f'/projects/{project_id}/jobs?{query_string}'
        project_id = project.get_uuid() if type(project) is Project else project
        code, response = self._rest.get(request_path)

        if (code == 200):
            jobs = list(map(self._jobObjectFromHashMap, response['items']))
            return jobs
        else:
            raise RuntimeError("Server status code: %s; Response: %s" % (code, response))

    def filter_by_inputs(self, jobs, keys, comparison, comparison_value):
        """Initialize the Jobs API client.

        filter_by_inputs(jobs, ['monteCarloDraws'], Comparison.GreaterThan, 50000)
        filter_by_inputs(jobs, ['opm','keplerian','inclination'], Comparison.GreaterThan, 23)

        Args:
            jobs (List[Job]): the jobs list to filter
            keys (List[str]): one or more keys of the JSON hierarchy
            comparison (Comparison): The type of comparison desired
            comparison_value : the value of the specific key of interest that is being tested for equality
        """
        results = []

        if len(keys) < 1:
            raise ValueError(f"Must provide at least one string key, comparison type, and one value: {keys}")

        for job in jobs:
            inputs = job.get_input_json()
            value = inputs[keys[0]]
            try:
                for ki in range(1, len(keys)):
                    key = keys[ki]
                    value = value[key]
            except TypeError:
                # The key they are searching for doesn't exist so by definition this won't pass filter criteria
                continue
            if comparison.compare(comparison_value, value):
                results.append(job)

        return results

    def _jobObjectFromHashMap(self, j):
        try:
            submission_time = dateparser.parse(j['submissionTime'])
        except:
            submission_time = None

        try:
            execution_start = dateparser.parse(j['executionStart'])
        except:
            execution_start = None

        try:
            completion_time = dateparser.parse(j['completionTime'])
        except:
            completion_time = None

        return Job(
            uuid=j.get('uuid'),
            project_id=j.get('referenceUuid'),
            description=j.get('description'),
            object_id=j.get('objectId'),
            user_defined_id=j.get('userDefinedId'),
            job_type=j.get('jobType'),
            input_json=j.get('inputParametersJson'),
            submission_time=submission_time,
            execution_start=execution_start,
            completion_time=completion_time,
            status=j.get('status')
        )
