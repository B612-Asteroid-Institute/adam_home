"""
    rest_proxy.py

    Class for setting up a REST proxy (for testing purposes)
"""

import json
import requests

class RestProxy(object):
    """Interface for accessing the server

    """
    def post(self, url, data_dict):
        """Send POST request to the server

        This function is intended to be overriden by derived classes to POST a request to a real or proxy server

        Args:
            url (str): the URL to send the POST to
            data_dict (dict): dictionary to be sent in the body of the POST

        Returns:
            Pair of code and json data (when overriden)

        Raises:
            NotImplementedError: if this does not get overriden by the derived classes
        """
        raise NotImplementedError("Got interface, need implementation")

    def get(self, url):
        """Send GET request to the URL

        This function is intended to be overriden by derived classes to GET a request from a real or proxy URL

        Args:
            url (str): the URL to send the GET request to

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

    def post(self, url, data_dict):
        """Send POST request to the URL

        This function is used to POST a request to the actual server

        Args:
            url (str): the URL to send the POST to
            data_dict (dict): dictionary to be sent in the body of the POST

        Returns:
            Pair of code and json data (actual from server)
        """
        req = requests.post(url, data=json.dumps(data_dict))
        return req.status_code, req.json()

    def get(self, url):
        """Send GET request to the server

        This function is used to GET a request from the server's URL

        Args:
            url (str): the URL to send the GET request to

        Returns:
            Pair of code and json data
        """
        req = requests.get(url)
        return req.status_code, req.json()

class _RestProxyForTest(RestProxy):
    """Implementation using REST proxy

    This class is used to send requests to a proxy server for testing purposes.

    """
    def __init__(self):
        """Initializes attributes

        Expectations as tuples (method, input_url, input_data, return_code, return_data)

        """
        self._expectations = []

    def expect_post(self, url, data_func, code, resp_data):
        """Expectations for POST method

        This function defines the expectations for a POST method.

        Args:
            url (str): the URL to send the POST to
            data_func (func): function to validate the input data to send to the POST
            code (int): return code from POST
            resp_data (dict): response data returned from POST
        """
        self._expectations.append(('POST', url, data_func, code, resp_data))

    def expect_get(self, url, code, resp_data):
        """Expectations for GET method

        This function defines the expectations for a GET method.

        Args:
            url (str): the URL to send the GET request to
            code (int): return code from GET
            resp_data (dict): response data returned from GET
        """
        self._expectations.append(('GET', url, None, code, resp_data))

    def post(self, url, data_dict):
        """Send POST request to the proxy URL

        This function is used to POST a request to a proxy server for testing purposes.

        Args:
            url (str): the URL to send the POST to
            data_dict (dict): the input data to send to the POST

        Returns:
            Pair of code and json data

        Raises:
            AssertionError: expectations are empty list
            AssertionError: wrong method called
            AssertionError: mismatched URLs for POST request
            AssertionError: POST data not valid

        TODO:
            Substitute with more specific errors
        """

        # Check for empty expectations list - TODO more specific error
        if len(self._expectations) == 0:
            raise AssertionError("Did not expect any calls, get POST")

        # Get first expectations list
        exp = self._expectations[0]

        # Remove list from expectations
        self._expectations.pop(0)

        # Go through expectations list and raise errors for non-expected items
        if exp[0] != 'POST':
            # Method is not 'POST'
            raise AssertionError("Expected %s, got POST" % exp[0])

        if url != exp[1]:
            # URL does not match expected one
            raise AssertionError("Expected POST request to %s, got %s" % (exp[1], url))

        if not exp[2](data_dict):
            # POST data not valid
            raise AssertionError("POST data didn't pass check: %s" % data_dict)

        # Return code and response data
        return exp[3], exp[4]

    def get(self, url):
        """Send GET request to proxy server URL

        This function is used to GET a request from the proxy server's URL for testing purposes.

        Args:
            url (str): the URL to send the GET request to

        Returns:
            Pair of code and json data

        Raises:
            AssertionError: expectations are empty list
            AssertionError: wrong method called
            AssertionError: mismatched URLs for GET request

        TODO:
            Substitute with more specific errors
        """

        # Check for empty expectations list - TODO more specific error
        if len(self._expectations) == 0:
            raise AssertionError("Did not expect any calls, get GET")

        # Get first expectations list
        exp = self._expectations[0]

        # Remove list from expectations
        self._expectations.pop(0)

        # Go through expectations list and raise errors for non-expected items
        if exp[0] != 'GET':
            # Method is not 'GET'
            raise AssertionError("Expected %s, got GET" % exp[0])

        if url != exp[1]:
            # URL does not match expected one
            raise AssertionError("Expected GET request to %s, got %s" % (exp[1], url))

        # Return code and response data
        return exp[3], exp[4]
