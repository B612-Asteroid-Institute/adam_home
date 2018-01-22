"""
    rest_proxy.py

    Class for setting up a REST proxy (for testing purposes)
"""

import json
import requests

class RestProxy(object):
    """Interface for accessing the server

    """
    def post(self, path, data_dict):
        """Send POST request to the server

        This function is intended to be overriden by derived classes to POST a request to a real or proxy server

        Args:
            path (str): the path to send the POST to
            data_dict (dict): dictionary to be sent in the body of the POST

        Returns:
            Pair of code and json data (when overriden)

        Raises:
            NotImplementedError: if this does not get overriden by the derived classes
        """
        raise NotImplementedError("Got interface, need implementation")

    def get(self, path):
        """Send GET request to the server

        This function is intended to be overriden by derived classes to GET a request from a real or proxy server

        Args:
            path (str): the path to send the GET request to

        Returns:
            Pair of code and json data (when overriden)

        Raises:
            NotImplementedError: if this does not get overriden by the derived classes
        """
        raise NotImplementedError("Got interface, need implementation")

class RestRequests(RestProxy):
    """Implementation using requests package

    This class is used to send actual requests to the server.

    """

    # Default base URL corresponding to ADAM project.
    DEFAULT_BASE_URL = 'https://pro-equinox-162418.appspot.com/_ah/api/adam/v1'
    
    def __init__(self, base_url=DEFAULT_BASE_URL):
        """Initialize with the give base URL. All paths for requests will be appended
        to this URL.
        
        """
        self._base_url = base_url

    def post(self, path, data_dict):
        """Send POST request to the server

        This function is used to POST a request to the actual server

        Args:
            path (str): the path to send the POST to
            data_dict (dict): dictionary to be sent in the body of the POST

        Returns:
            Pair of code and json data (actual from server)
        """
        req = requests.post(self._base_url + path, data=json.dumps(data_dict))
        req_json = {}
        try:
            req_json = req.json()
        except ValueError:
            # TODO(laura): make the rest server return json responses, always
            print("Received non-JSON response from API: " + str(req.status_code) + ", " + req.content)
        return req.status_code, req_json

    def get(self, path):
        """Send GET request to the server

        This function is used to GET a request from the server

        Args:
            path (str): the path to send the GET request to

        Returns:
            Pair of code and json data
        """
        req = requests.get(self._base_url + path)
        req_json = {}
        try:
            req_json = req.json()
        except ValueError:
            # TODO(laura): make the rest server return json responses, always
            print("Received non-JSON response from API: " + str(req.status_code) + ", " +  req.content)
        return req.status_code, req_json

class _RestProxyForTest(RestProxy):
    """Implementation using REST proxy

    This class is used to send requests to a proxy server for testing purposes.

    """
    def __init__(self):
        """Initializes attributes

        Expectations as tuples (method, input_path, input_data, return_code, return_data)

        """
        self._expectations = []

    def expect_post(self, path, data_func, code, resp_data):
        """Expectations for POST method

        This function defines the expectations for a POST method.

        Args:
            path (str): the path to send the POST to
            data_func (func): function to validate the input data to send to the POST
            code (int): return code from POST
            resp_data (dict): response data returned from POST
        """
        self._expectations.append(('POST', path, data_func, code, resp_data))

    def expect_get(self, path, code, resp_data):
        """Expectations for GET method

        This function defines the expectations for a GET method.

        Args:
            path (str): the path to send the GET request to
            code (int): return code from GET
            resp_data (dict): response data returned from GET
        """
        self._expectations.append(('GET', path, None, code, resp_data))

    def post(self, path, data_dict):
        """Imitate sending POST request to server.

        This function is used to imitate POSTing a request to a server for testing
        purposes.

        Args:
            path (str): the path to send the POST to
            data_dict (dict): the input data to send to the POST

        Returns:
            Pair of code and json data

        Raises:
            AssertionError: expectations are empty list
            AssertionError: wrong method called
            AssertionError: mismatched paths for POST request
            AssertionError: POST data not valid

        TODO:
            Substitute with more specific errors
        """

        # Check for empty expectations list - TODO more specific error
        if len(self._expectations) == 0:
            raise AssertionError("Did not expect any calls, got POST")

        # Get first expectations list
        exp = self._expectations[0]

        # Remove list from expectations
        self._expectations.pop(0)

        # Go through expectations list and raise errors for non-expected items
        if exp[0] != 'POST':
            # Method is not 'POST'
            raise AssertionError("Expected %s, got POST" % exp[0])

        if path != exp[1]:
            # path does not match expected one
            raise AssertionError("Expected POST request to %s, got %s" % (exp[1], path))

        if not exp[2](data_dict):
            # POST data not valid
            raise AssertionError("POST data didn't pass check: %s" % data_dict)

        # Return code and response data
        return exp[3], exp[4]

    def get(self, path):
        """Imitate sending GET request to server

        This function is used to imitate GETting a request from the server for testing 
        purposes.

        Args:
            path (str): the path to send the GET request to

        Returns:
            Pair of code and json data

        Raises:
            AssertionError: expectations are empty list
            AssertionError: wrong method called
            AssertionError: mismatched paths for GET request

        TODO:
            Substitute with more specific errors
        """

        # Check for empty expectations list - TODO more specific error
        if len(self._expectations) == 0:
            raise AssertionError("Did not expect any calls, got GET")

        # Get first expectations list
        exp = self._expectations[0]

        # Remove list from expectations
        self._expectations.pop(0)

        # Go through expectations list and raise errors for non-expected items
        if exp[0] != 'GET':
            # Method is not 'GET'
            raise AssertionError("Expected %s, got GET" % exp[0])

        if path != exp[1]:
            # path does not match expected one
            raise AssertionError("Expected GET request to %s, got %s" % (exp[1], path))

        # Return code and response data
        return exp[3], exp[4]
