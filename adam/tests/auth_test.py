from adam import Auth
from adam.rest_proxy import _RestProxyForTest
import json
import unittest


class AuthTest(unittest.TestCase):
    """Unit tests for auth module

    """

    def test_successful_authentication(self):
        # Use REST proxy for testing
        rest = _RestProxyForTest()
        auth = Auth(rest)

        # Before authenticating, auth should reflect not logged in.
        self.assertEqual(auth.get_user(), '')
        self.assertEqual(auth.get_logged_in(), False)

        # A successful authentication should store token and set user to returned value.
        good_token = 'good'
        rest.expect_get('/me', 200,
                        {'email': 'a@b.com', 'loggedIn': True})
        auth.authenticate()
        self.assertEqual(auth.get_user(), 'a@b.com')
        self.assertEqual(auth.get_logged_in(), True)

    def test_unsuccessful_authentication(self):
        # Use REST proxy for testing
        rest = _RestProxyForTest()
        auth = Auth(rest)

        # Authenticate in order to fill in email/logged_in/token so that next test
        # can verify that these are cleared.
        good_token = 'good'
        rest.expect_get('/me', 200,
                        {'email': 'a@b.com', 'loggedIn': True})
        auth.authenticate()

        # An unsuccessful authentication should clear token and other values.
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
        rest.expect_get('/me', 503,
                        json.loads(server_error_on_bad_token))
        auth.authenticate()
        self.assertEqual(auth.get_user(), '')
        self.assertEqual(auth.get_logged_in(), False)

    def test_authentication_empty_token(self):
        # Use REST proxy for testing
        rest = _RestProxyForTest()
        auth = Auth(rest)

        # Authenticate in order to fill in email/logged_in/token so that next test
        # can verify that these are cleared.
        good_token = 'good'
        rest.expect_get('/me', 200,
                        {'email': 'a@b.com', 'loggedIn': True})
        auth.authenticate()

        # Authentication with an empty token should be no problem and result in an empty
        # auth object.
        rest.expect_get('/me', 200, {"loggedIn": False})
        auth.authenticate()
        self.assertEqual(auth.get_user(), '')
        self.assertEqual(auth.get_logged_in(), False)

    def test_authentication_server_error(self):
        # Use REST proxy for testing
        rest = _RestProxyForTest()
        auth = Auth(rest)

        # Authenticate in order to fill in email/logged_in/token so that next test
        # can verify that these are not cleared.
        good_token = 'good'
        rest.expect_get('/me', 200,
                        {'email': 'a@b.com', 'loggedIn': True})
        auth.authenticate()

        # Authentication should throw on a non-200 response and leave auth contents
        # unchanged.
        rest.expect_get('/me', 404, {})
        with self.assertRaises(RuntimeError):
            auth.authenticate()
        self.assertEqual(auth.get_user(), 'a@b.com')
        self.assertEqual(auth.get_logged_in(), True)


if __name__ == '__main__':
    unittest.main()
