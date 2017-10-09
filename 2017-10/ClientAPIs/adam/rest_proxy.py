import json
import requests

class RestProxy(object):
    """
    Interface for accessing server.
    """
    def post(self, url, data_dict):
        """
        Sends POST request to the server.
        :param url: string
        :param data_dict: dictionary to be sent in the body
        :return: pair of code and json data
        """
        raise NotImplementedError("Got interface, need implementation")

    def get(self, url):
        """
        Sends GET request to the URL
        :param url: string
        :return: pair of code and json data
        """
        raise NotImplementedError("Got interface, need implementation")

class RestRequests(RestProxy):
    """
    Implementation using requests package.
    """

    def post(self, url, data_dict):
        req = requests.post(url, data=json.dumps(data_dict))
        return req.status_code, req.json()

    def get(self, url):
        req = requests.get(url)
        return req.status_code, req.json()

class _RestProxyForTest(RestProxy):
    def __init__(self):
        # Expectations as tuples (method, input_url, input_data, return_code, return_data)
        self._expectations = []

    def expect_post(self, url, data_func, code, resp_data):
        self._expectations.append(('POST', url, data_func, code, resp_data))

    def expect_get(self, url, code, resp_data):
        self._expectations.append(('GET', url, None, code, resp_data))

    def post(self, url, data_dict):
        if len(self._expectations) == 0:
            # TODO more specific error
            raise AssertionError("Did not expect any calls, get POST")
        exp = self._expectations[0]
        self._expectations.pop(0)
        if exp[0] != 'POST':
            raise AssertionError("Expected %s, got POST" % exp[0])
        if url != exp[1]:
            raise AssertionError("Expected POST request to %s, got %s" % (exp[1], url))
        if not exp[2](data_dict):
            raise AssertionError("POST data didn't pass check: %s" % data_dict)
        return exp[3], exp[4]

    def get(self, url):
        if len(self._expectations) == 0:
            # TODO more specific error
            raise AssertionError("Did not expect any calls, get GET")
        exp = self._expectations[0]
        self._expectations.pop(0)
        if exp[0] != 'GET':
            raise AssertionError("Expected %s, got GET" % exp[0])
        if url != exp[1]:
            raise AssertionError("Expected GET request to %s, got %s" % (exp[1], url))
        return exp[3], exp[4]
