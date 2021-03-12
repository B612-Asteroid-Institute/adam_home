"""
    job.py
"""


class Job(object):
    """Job class.

    An ADAM Project is like captures a computational run in our services.
    """

    def __init__(self, uuid, project_id=None, object_id=None, user_defined_id=None, description=None, job_type=None,
                 input_json=None, submission_time=None, execution_start=None, completion_time=None, status=None):
        self._uuid = uuid
        self._project_id = project_id
        self._object_id = object_id
        self._user_defined_id = user_defined_id,
        self._description = description
        self._job_type = job_type
        self._input_json = input_json
        self._submission_time = submission_time
        self._execution_start = execution_start
        self._completion_time = completion_time
        self._status = status


    def __repr__(self):
        return (
            f"Job(uuid={self._uuid}, project_id={self._project_id}, "
            f"object_id={self._object_id}, user_defined_id={self._user_defined_id}, "
            f"description={self._description}, job_type={self._job_type},"
            f"status={self._status}, submission_time={self._submission_time},"
            f"execution_start={self._execution_start}, completion_time={self._completion_time},"
            f"input_json={self._input_json})")

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
        return self._input_json

    def get_submission_time(self):
        return self._submission_time

    def get_execution_start(self):
        return self._execution_start

    def get_completion_time(self):
        return self._completion_time

    def get_status(self):
        return self._status

