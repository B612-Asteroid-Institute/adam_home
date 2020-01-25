from adam.rest_proxy import _RestProxyForTest
from adam.rest_proxy import AuthenticatingRestProxy
from adam.rest_proxy import RetryingRestProxy
import unittest


class RetryingRestProxyTest(unittest.TestCase):
    """Unit tests for retrying rest proxy.
    """

    def test_good_response(self):
        rest = _RestProxyForTest()
        retrying_rest = RetryingRestProxy(rest)

        expected_data = {}

        def check_input(data_dict):
            self.assertEqual(expected_data, data_dict)
            return True

        # A 200 (or 204 for deletes) results in no retrying.
        rest.expect_post("/test", check_input, 200, {'a': 1})
        code, response = retrying_rest.post("/test", {})
        self.assertEqual(200, code)
        self.assertDictEqual({'a': 1}, response)

        rest.expect_get("/test?a=1&b=2", 200, {'a': 1})
        code, response = retrying_rest.get("/test?a=1&b=2")
        self.assertEqual(200, code)
        self.assertDictEqual({'a': 1}, response)

        rest.expect_delete("/test?a=1&b=2", 204)
        code = retrying_rest.delete("/test?a=1&b=2")
        self.assertEqual(204, code)

    def test_retry_on_retryable_error(self):
        rest = _RestProxyForTest()
        retrying_rest = RetryingRestProxy(rest)

        expected_data = {}

        def check_input(data_dict):
            self.assertEqual(expected_data, data_dict)
            return True

        # A 403, 502, or 503 results in retrying.
        rest.expect_post("/test", check_input, 403, {'a': 1})
        rest.expect_post("/test", check_input, 200, {'a': 1})
        code, response = retrying_rest.post("/test", {})
        self.assertEqual(200, code)
        self.assertDictEqual({'a': 1}, response)

        rest.expect_get("/test?a=1&b=2", 502, {'a': 1})
        rest.expect_get("/test?a=1&b=2", 200, {'a': 1})
        code, response = retrying_rest.get("/test?a=1&b=2")
        self.assertEqual(200, code)
        self.assertDictEqual({'a': 1}, response)

        rest.expect_delete("/test?a=1&b=2", 503)
        rest.expect_delete("/test?a=1&b=2", 204)
        code = retrying_rest.delete("/test?a=1&b=2")
        self.assertEqual(204, code)

    def test_no_retry_on_nonretryable_error(self):
        rest = _RestProxyForTest()
        retrying_rest = RetryingRestProxy(rest)

        expected_data = {}

        def check_input(data_dict):
            self.assertEqual(expected_data, data_dict)
            return True

        # An error other than 403, 502, and 503 results in no retrying.
        rest.expect_post("/test", check_input, 404, {'a': 1})
        code, response = retrying_rest.post("/test", {})
        self.assertEqual(404, code)
        self.assertDictEqual({'a': 1}, response)

        rest.expect_get("/test?a=1&b=2", 418, {'a': 1})
        code, response = retrying_rest.get("/test?a=1&b=2")
        self.assertEqual(418, code)
        self.assertDictEqual({'a': 1}, response)

        rest.expect_delete("/test?a=1&b=2", 500)
        code = retrying_rest.delete("/test?a=1&b=2")
        self.assertEqual(500, code)

    def test_eventually_stops_retrying(self):
        rest = _RestProxyForTest()
        retrying_rest = RetryingRestProxy(rest, num_tries=3)

        expected_data = {}

        def check_input(data_dict):
            self.assertEqual(expected_data, data_dict)
            return True

        # The retryable errors will eventually no longer be retried.
        rest.expect_post("/test", check_input, 403, {'a': 1})
        rest.expect_post("/test", check_input, 403, {'a': 1})
        rest.expect_post("/test", check_input, 403, {'a': 1})
        code, response = retrying_rest.post("/test", {})
        self.assertEqual(403, code)
        self.assertDictEqual({'a': 1}, response)

        rest.expect_get("/test?a=1&b=2", 502, {'a': 1})
        rest.expect_get("/test?a=1&b=2", 502, {'a': 1})
        rest.expect_get("/test?a=1&b=2", 502, {'a': 1})
        code, response = retrying_rest.get("/test?a=1&b=2")
        self.assertEqual(502, code)
        self.assertDictEqual({'a': 1}, response)

        # Mixing errors is allowed - all count toward the same cumulative total.
        # The error on the final try will be reported.
        rest.expect_delete("/test?a=1&b=2", 403)
        rest.expect_delete("/test?a=1&b=2", 502)
        rest.expect_delete("/test?a=1&b=2", 503)
        code = retrying_rest.delete("/test?a=1&b=2")
        self.assertEqual(503, code)


class AuthenticatingRestProxyTest(unittest.TestCase):
    """Unit tests for authenticating rest proxy.

    """

    def test_post(self):
        rest = _RestProxyForTest()
        token = 'my_token'
        auth_rest = AuthenticatingRestProxy(rest, token)

        expected_data = {}

        def check_input(data_dict):
            self.assertEqual(expected_data, data_dict)
            return True

        # Token should be added to empty data in post.
        expected_data = {'token': token}
        rest.expect_post("/test", check_input, 200, {})
        auth_rest.post("/test", {})

        # Token should be added to non-empty data in post, preserving rest of data.
        expected_data = {'a': 1, 'token': token, 'b': 2}
        rest.expect_post("/test", check_input, 200, {})
        auth_rest.post("/test", {'b': 2, 'a': 1})

    def test_get(self):
        rest = _RestProxyForTest()
        token = 'my_token'
        auth_rest = AuthenticatingRestProxy(rest, token)

        rest.expect_get("/test?token=my_token", 200, {})
        auth_rest.get("/test")

        rest.expect_get("/test?a=1&b=2&token=my_token", 200, {})
        auth_rest.get("/test?a=1&b=2")

        rest.expect_get("/test?a=1&b=2&token=my_token", 4123, {'c': 3})
        code, response = auth_rest.get("/test?a=1&b=2")
        self.assertEqual(code, 4123)
        self.assertEqual(response, {'c': 3})

    def test_get_unsafe_url_characters(self):
        rest = _RestProxyForTest()
        # All the unsafe and reserved characters
        #pylint: disable=W1401 # NOQA
        token = '; / ? : @ = &   < > # % { } | \\ ^ ~ [ ]'
        auth_rest = AuthenticatingRestProxy(rest, token)

        # handle urlencode modules with and without the bugfix for https://bugs.python.org/issue16285 (Python >= 3.7)
        # see also: https://stackoverflow.com/questions/51334226/python-why-is-now-included-in-the-set-of-reserved-characters-in-urllib-pars
        import urllib
        tilde = urllib.parse.quote('~')

        rest.expect_get("/test?a=1&b=2&token=%3B+%2F+%3F+%3A+%40+%3D+%26+++%3C+%3E"
                        "+%23+%25+%7B+%7D+%7C+%5C+%5E+{}+%5B+%5D".format(tilde), 200, {})
        auth_rest.get("/test?a=1&b=2")

    def test_delete(self):
        # DELETE behaves exactly like GET, so only the basics are tested.
        rest = _RestProxyForTest()
        token = 'my_token'
        auth_rest = AuthenticatingRestProxy(rest, token)

        rest.expect_delete("/test?token=my_token", 200)
        auth_rest.delete("/test")

        rest.expect_delete("/test?a=1&b=2&token=my_token", 200)
        auth_rest.delete("/test?a=1&b=2")


if __name__ == '__main__':
    unittest.main()
