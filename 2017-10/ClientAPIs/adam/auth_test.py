
from adam import Auth
from adam.rest_proxy import _RestProxyForTest
import json
import unittest

class AuthTest(unittest.TestCase):
    """Unit tests for auth module

    """

    def setUp(self):
        self._base = "http://BASE"
        
    def test_successful_authorization(self):
        auth = Auth(self._base)

        # Use REST proxy for testing
        rest = _RestProxyForTest()
        auth.set_rest_accessor(rest)
        
        # Before authorizing, auth should reflect not logged in.
        self.assertEqual(auth.get_token(), '')
        self.assertEqual(auth.get_user(), '')
        self.assertEqual(auth.get_logged_in(), False)
        
        # A successful authorization should store token and set user to returned value.
        good_token = 'good'
        rest.expect_get(self._base + '/me?token=' + good_token, 200,
        	{'email': 'a@b.com', 'loggedIn': True})
        auth.authorize(good_token)
        self.assertEqual(auth.get_token(), good_token)
        self.assertEqual(auth.get_user(), 'a@b.com')
        self.assertEqual(auth.get_logged_in(), True)
        
	def test_unsuccessful_authorization(self):
		auth = Auth(self._base)

		# Use REST proxy for testing
		rest = _RestProxyForTest()
		auth.set_rest_accessor(rest)
        
        # Authorize in order to fill in email/logged_in/token so that next test
        # can verify that these are cleared.
        rest.expect_get(self._base + '/me?token=' + good_token, 200,
        	{'email': 'a@b.com', 'loggedIn': True})
        auth.authorize(good_token)
		
        # An unsuccessful authorization should clear token and other values.
        bad_token = 'bad'
        # An example of the few ways that the server might reject a user. Others look
        # like this with different messages.
        server_error_on_bad_token = """
			{
			  "error": {
				"errors": [
				  {
					"domain": "global",
					"reason": "backendError",
					"message": "org.apache.shiro.authc.IncorrectCredentialsException"
				  }
				],
				"code": 503,
				"message": "org.apache.shiro.authc.IncorrectCredentialsException"
			  }
			}
			"""
        rest.expect_get(self._base + '/me?token=' + bad_token, 503,
        	json.loads(server_error_on_bad_token))
        auth.authorize(bad_token)
        self.assertEqual(auth.get_token(), '')
        self.assertEqual(auth.get_user(), '')
        self.assertEqual(auth.get_logged_in(), False)
        
	def test_authorization_empty_token(self):
		auth = Auth(self._base)

		# Use REST proxy for testing
		rest = _RestProxyForTest()
		auth.set_rest_accessor(rest)
        
        # Authorize in order to fill in email/logged_in/token so that next test
        # can verify that these are cleared.
        rest.expect_get(self._base + '/me?token=' + good_token, 200,
        	{'email': 'a@b.com', 'loggedIn': True})
        auth.authorize(good_token)
        
        # Authorization with an empty token should be no problem and result in an empty
        # auth object.
        rest.expect_get(self._base + '/me', 200, {"loggedIn": False})
        auth.authorize('')
        self.assertEqual(auth.get_token(), '')
        self.assertEqual(auth.get_user(), '')
        self.assertEqual(auth.get_logged_in(), False)
        
	def test_authorization_server_error(self):
		auth = Auth(self._base)

		# Use REST proxy for testing
		rest = _RestProxyForTest()
		auth.set_rest_accessor(rest)
        
        # Authorize in order to fill in email/logged_in/token so that next test
        # can verify that these are not cleared.
        rest.expect_get(self._base + '/me?token=' + good_token, 200,
        	{'email': 'a@b.com', 'loggedIn': True})
        auth.authorize(good_token)
        
        # Authorization should throw on a non-200 response and leave auth contents
        # unchanged.
        rest.expect_get(self._base + '/me?token=problematic_token', 404, {})
        with self.assertRaises(RuntimeError):
            auth.authorize('problematic_token')
        self.assertEqual(auth.get_token(), good_token)
        self.assertEqual(auth.get_user(), 'a@b.com')
        self.assertEqual(auth.get_logged_in(), True)

if __name__ == '__main__':
    unittest.main()
    	