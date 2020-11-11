"""
    rest_proxy.py

    Exposes an interface for making calls to the REST API.

    Implementations:
        - RestRequests: makes simple calls to REST API.
        - AuthenticatingRestProxy: wraps a RestProxy and adds the auth token to all calls.
        - _RestProxyForTest: mocks methods and exposes extra functionality to add expectations.
"""

import datetime
import functools
import json

import requests
import yaml

from adam import ConfigManager


class AccessTokenRefresher(object):
    """Performs token refresh if the user's access token has expired."""

    @staticmethod
    def refresh_access_token(func):
        """Decorator for methods that should attempt to refresh the access token.

        This mainly applies to REST calls made with authentication information. Firebase
        automatically expires the access token (aka the Firebase ID token) after an hour. The ADAM
        server and client will leave the token verification up to Firebase. When an access token
        expires, ADAM will request a new one from Firebase, given the user's refresh token.

        After an access token is refreshed, it will be saved to the user's ADAM configuration for
        the current configuration profile. The configuration profile corresponds to the environments
        saved by adamctl.
        """
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            # Attempt to execute the initial request.
            response_code, response_body = func(*args, **kwargs)
            # Responses that don't result in 401 (unauthorized) should pass through.
            if response_code != 401:
                return response_code, response_body

            # 401 responses that aren't due to an expired token should pass through. This means
            # there's an issue with the user's account and they should reach out to B612 team for
            # help.
            if response_body.get('error') != 'expired-token':
                return response_code, response_body

            # Otherwise, received a 401 due to an expired token, so request a token refresh.
            cm = ConfigManager()
            default_env = cm.get_default_env()
            config = cm.get_config(environment=default_env)

            # If access token expired, refresh the access token.
            refresh_token_url = f"{config.get('url')}/users/{config.get('user_id', '-')}/idToken"
            request_body = {
                'refreshToken': config.get('refresh_token')
            }
            response = requests.post(refresh_token_url, json=request_body)
            response.raise_for_status()
            refresh_response_body = response.json()

            # Update the access and refresh token in the ADAM config, then write out the file.
            config['access_token'] = yaml.safe_load(refresh_response_body.get('idToken'))
            config['refresh_token'] = yaml.safe_load(refresh_response_body.get('refreshToken'))
            cm.set_config(default_env, config)
            cm.to_file()

            # The original function should reload the ADAM configuration to pick up the new
            # access_token.
            kwargs['force_reload_config'] = True

            # Then re-execute the method again.
            return func(*args, **kwargs)

        return wrapper


class RestProxy(object):
    """Interface for accessing the server

    """

    def post(self, path, data_dict, **kwargs):
        """Send POST request to the server

        This function is intended to be overridden by derived classes to POST a
        resource to a real or proxy server

        Args:
            path (str): the path to send the POST to
            data_dict (dict): dictionary to be sent in the body of the POST
            kwargs (dict): Additional arguments to configure requests method calls

        Returns:
            Pair of code and json data (when overridden)

        Raises:
            NotImplementedError: if this does not get overridden by the derived classes
        """
        raise NotImplementedError("Got interface, need implementation")

    def get(self, path, **kwargs):
        """Send GET request to the server

        This function is intended to be overridden by derived classes to GET a
        resource from a real or proxy server

        Args:
            path (str): the path to send the GET request to
            kwargs (dict): Additional arguments to configure requests method calls

        Returns:
            Pair of code and json data (when overridden)

        Raises:
            NotImplementedError: if this does not get overridden by the derived classes
        """
        raise NotImplementedError("Got interface, need implementation")

    def delete(self, path, **kwargs):
        """Send DELETE request to the server

        This function is intended to be overridden by derived classes to DELETE a
        resource from a real or proxy server

        Args:
            path (str): the path to send the DELETE request to
            kwargs (dict): Additional arguments to configure requests method calls

        Returns:
            Http code

        Raises:
            NotImplementedError: if this does not get overriden by the derived classes
        """
        raise NotImplementedError("Got interface, need implementation")


class AuthenticatingRestProxy(RestProxy):
    """ Rest proxy implementation that wraps another rest proxy and adds the authentication
    token to every method call.

    """

    def __init__(self, rest_proxy):
        self._rest_proxy = rest_proxy

    @AccessTokenRefresher.refresh_access_token
    def post(self, path, data_dict, **kwargs):
        kwargs['use_credentials'] = True
        return self._rest_proxy.post(path, data_dict, **kwargs)

    @AccessTokenRefresher.refresh_access_token
    def get(self, path, **kwargs):
        kwargs['use_credentials'] = True
        return self._rest_proxy.get(path, **kwargs)

    @AccessTokenRefresher.refresh_access_token
    def delete(self, path, **kwargs):
        kwargs['use_credentials'] = True
        return self._rest_proxy.delete(path, **kwargs)


class LoggingRestProxy(RestProxy):
    """ Rest proxy implementation that wraps another rest proxy and adds logging of
    interesting information such as timing and request size to each call.

    """

    def __init__(self, rest_proxy):
        self._rest_proxy = rest_proxy

    # From https://stackoverflow.com/questions/1094841/reusable-library-to-get-human-readable-version-of-file-size # NOQA
    def _sizeof_fmt(self, num, suffix='B'):
        for unit in ['', 'Ki', 'Mi', 'Gi', 'Ti', 'Pi', 'Ei', 'Zi']:
            if abs(num) < 1024.0:
                return "%3.1f%s%s" % (num, unit, suffix)
            num /= 1024.0
        return "%.1f%s%s" % (num, 'Yi', suffix)

    def post(self, path, data_dict, **kwargs):
        print("--------------------------------------------------------")
        print("| Post to " + path)
        start = datetime.datetime.now()
        code, response = self._rest_proxy.post(path, data_dict, **kwargs)
        end = datetime.datetime.now()
        print("|    Request size: " + self._sizeof_fmt(len(json.dumps(data_dict))))
        print("|    Response size: " + self._sizeof_fmt(len(str(response))))
        print("|    Call duration: " + str(end - start))
        print("--------------------------------------------------------")
        return code, response

    def get(self, path, **kwargs):
        print("--------------------------------------------------------")
        print("| Get to " + path)
        start = datetime.datetime.now()
        code, response = self._rest_proxy.get(path, **kwargs)
        end = datetime.datetime.now()
        print("|    Response size: " + self._sizeof_fmt(len(str(response))))
        print("|    Call duration: " + str(end - start))
        print("--------------------------------------------------------")
        return code, response

    def delete(self, path, **kwargs):
        print("--------------------------------------------------------")
        print("| Delete to " + path)
        start = datetime.datetime.now()
        code = self._rest_proxy.delete(path, **kwargs)
        end = datetime.datetime.now()
        print("|    Call duration: " + str(end - start))
        print("--------------------------------------------------------")
        return code, None


class RetryingRestProxy(RestProxy):
    """Rest proxy implementation that wraps another rest proxy and retries calls for some
    errors known to be retryable.
    """

    def __init__(self, rest_proxy, num_tries=5):
        self._rest_proxy = rest_proxy
        self._retry_codes = [
            403,  # ExpiredSessionExceptions can manifest as 403s.
            502,  # These happen periodically and are transient.
            503,  # Usually due to ExpiredSessionExceptions. They go away on retry.
        ]
        self._num_tries = num_tries

    def post(self, path, data_dict, **kwargs):
        for i in range(self._num_tries):
            code, response = self._rest_proxy.post(path, data_dict, **kwargs)
            if code not in self._retry_codes or i == self._num_tries - 1:
                break
            print("Encountered error %s calling post to %s: %s \nRetrying (attempt %s)" %
                  (code, path, response, i + 2))
        return code, response

    def get(self, path, **kwargs):
        for i in range(self._num_tries):
            code, response = self._rest_proxy.get(path, **kwargs)
            if code not in self._retry_codes or i == self._num_tries - 1:
                break
            print("Encountered error %s calling get on %s: %s \nRetrying (attempt %s)" %
                  (code, path, response, i + 2))
        return code, response

    def delete(self, path, **kwargs):
        for i in range(self._num_tries):
            code, response = self._rest_proxy.delete(path, **kwargs)
            if code not in self._retry_codes or i == self._num_tries - 1:
                break
            print("Encountered error %s calling delete on %s. Retrying (attempt %s)" %
                  (code, path, i + 2))
        return code, response


class RestRequests(RestProxy):
    """Implementation using requests package

    This class is used to send requests to the server.
    """

    def __init__(self):
        """Initialize client with some ADAM configuration."""

        self._config = None

    def _add_requests_args(self, **kwargs):
        """Add more keyword arguments for requests method calls.

        Args:
            kwargs (dict): Additional arguments to configure requests method calls
        """
        req_kwargs = {}
        if 'use_credentials' in kwargs and kwargs['use_credentials']:
            req_kwargs['auth'] = BearerAuthc(self._config.get('access_token'))
        return req_kwargs

    def base_url(self):
        return self._config.get('url')

    def _load_config(self, force_load=False):
        if self._config is None or force_load:
            cm = ConfigManager()
            self._config = cm.get_config(environment=cm.get_default_env())

    def _maybe_reload_config(self, **kwargs):
        force_reload = 'force_reload_config' in kwargs and kwargs['force_reload_config'] is True
        self._load_config(force_load=force_reload)

    def post(self, path, data_dict, **kwargs):
        """Send POST request to the server

        This function is used to POST a resource to the server

        Args:
            path (str): the path to send the POST to
            data_dict (dict): dictionary to be sent in the body of the POST
            kwargs (dict): Additional arguments to configure requests method calls

        Returns:
            Pair of code and json data (actual from server)
        """

        self._maybe_reload_config(**kwargs)
        additional_args = self._add_requests_args(**kwargs)
        response = requests.post(self.base_url() + path, json=data_dict, **additional_args)
        try:
            return response.status_code, response.json()
        except ValueError as e:
            # TODO: make the rest server return json responses, always
            print("Received non-JSON response from API: " +
                  str(response.status_code) + ", " + str(response.content))
            raise e

    def get(self, path, **kwargs):
        """Send GET request to the server

        This function is used to GET a resource from the server

        Args:
            path (str): the path to send the GET request to
            kwargs (dict): Additional arguments to configure requests method calls

        Returns:
            Pair of code and json data
        """

        self._maybe_reload_config(**kwargs)
        additional_args = self._add_requests_args(**kwargs)
        response = requests.get(self.base_url() + path, **additional_args)
        response_json = {}
        try:
            response_json = response.json()
        except ValueError:
            # TODO: make the rest server return json responses, always
            print("Received non-JSON response from API: " +
                  str(response.status_code) + ", " + str(response.content))
        return response.status_code, response_json

    def delete(self, path, **kwargs):
        """Send DELETE request to the server

        This function is used to DELETE a resource from the server

        Args:
            path (str): the path to send the DELETE request to
            kwargs (dict): Additional arguments to configure requests method calls

        Returns:
            Pair of code and json data
        """

        self._maybe_reload_config(**kwargs)
        additional_args = self._add_requests_args(**kwargs)
        response = requests.delete(self.base_url() + path, **additional_args)
        return response.status_code, None


class _RestProxyForTest(RestProxy):
    """Implementation using REST proxy for test purposes

    This class is used to send requests to a proxy server for testing purposes.

    """

    def __init__(self):
        """Initializes attributes

        Expectations as tuples (method, input_path, input_data, return_code, return_data)

        """
        self._expectations = []

    def expect_post(self, path, data_func, code, resp_data, **kwargs):
        """Expectations for POST method

        This function defines the expectations for a POST method.

        Args:
            path (str): the path to send the POST to
            data_func (func): function to validate the input data to send to the POST
            code (int): return code from POST
            resp_data (dict): response data returned from POST
            kwargs (dict): Additional arguments to configure requests method calls

        """
        self._expectations.append(('POST', path, data_func, code, resp_data, kwargs))

    def expect_get(self, path, code, resp_data, **kwargs):
        """Expectations for GET method

        This function defines the expectations for a GET method.

        Args:
            path (str): the path to send the GET request to
            code (int): return code from GET
            resp_data (dict): response data returned from GET
            kwargs (dict): Additional arguments to configure requests method calls
        """
        self._expectations.append(('GET', path, None, code, resp_data, kwargs))

    def expect_delete(self, path, code, **kwargs):
        """Expectations for DELETE method.

        This function defines the expectations for a DELETE method.

        Args:
            path (str): the path to send the DELETE request to
            code (int): return code from DELETE
            kwargs (dict): Additional arguments to configure requests method calls

        Note that delete methods do not generally return data.
        """
        self._expectations.append(('DELETE', path, None, code, None, kwargs))

    def post(self, path, data_dict, **kwargs):
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

    def get(self, path, **kwargs):
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

    def delete(self, path, **kwargs):
        if len(self._expectations) == 0:
            raise AssertionError("Did not expect any calls, got DELETE")

        # Get first expectations list
        exp = self._expectations[0]

        # Remove list from expectations
        self._expectations.pop(0)

        # Go through expectations list and raise errors for non-expected items
        if exp[0] != 'DELETE':
            # Method is not 'DELETE'
            raise AssertionError("Expected %s, got DELETE" % exp[0])

        if path != exp[1]:
            # path does not match expected one
            raise AssertionError("Expected DELETE request to %s, got %s" % (exp[1], path))

        return exp[3], exp[4]


class BearerAuthc(requests.auth.AuthBase):
    """Attaches bearer token to request."""

    def __init__(self, token):
        self._token = token

    def __call__(self, r):
        r.headers["authorization"] = f"Bearer {self._token}"
        return r
