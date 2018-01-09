"""
    auth.py
"""

from adam.rest_proxy import RestRequests
import adam

class Auth(object):
    """Module for generating and using authentication tokens

    """
    def __init__(self, url, token):
        """Initializes attributes

        """
        self._rest = RestRequests()   # rest request option (requests package or proxy)
        self._url = url
        self._token = token

    def __repr__(self):
    	"""
        Args:
            None

        Returns:
            A dummy string
        """
        return "Auth"

    def set_rest_accessor(self, proxy):
        """Override network access methods

        This function overrides network access and sets the rest request to a proxy

        Args:
            proxy (class)

        Returns:
            None
        """
        self._rest = proxy
        

    def whoami(self):
        """Checks on current authorization status.

        Raises:
        """

        # Post request on cloud server
        code, response = self._rest.get(self._url + '/me/' + self._token)

        # Check error code
        if code != 200:
            raise RuntimeError("Server status code: %s; Response: %s" % (code, response))

        return response