
from adam.auth import Auth
from adam.rest_proxy import _RestProxyForTest
import unittest

class AuthTest(unittest.TestCase):
    """Unit tests for auth module

    """

    def setUp(self):
        """"Set up base URL

        This function sets up the base URL to a dummy URL.

        """
        self._base = "http://BASE"
        

    def test_whoami_anonymous(self):
        """Test whoami

        This function tests that the whoami check functions as expected.

        """

        # Use REST proxy for testing
        rest = _RestProxyForTest()

        token = 'some_token'

        # Set expected 'GET' request with 404 error
        rest.expect_get(self._base + '/me/' + token, 404, {})

        # Initiate Auth class
        auth = Auth(self._base, token)

        # Override network access with proxy
        auth.set_rest_accessor(rest)

        # Request whoami
        with self.assertRaises(RuntimeError):
            auth.whoami()
        
        rest.expect_get(self._base + '/me/' + token, 200, {'logged_in': False})
        
        auth.whoami()