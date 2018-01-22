from adam import Auth
from adam.rest_proxy import _RestProxyForTest
from adam.rest_proxy import AuthorizingRestProxy
import unittest

class AuthorizingRestProxyTest(unittest.TestCase):
    """Unit tests for authorizing rest proxy.

    """

    def test_post(self):
        rest = _RestProxyForTest()
        token = 'my_token'
        auth_rest = AuthorizingRestProxy(rest, token)

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
        auth_rest = AuthorizingRestProxy(rest, token)
        
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
        token = '; / ? : @ = &   < > # % { } | \ ^ ~ [ ]'
        auth_rest = AuthorizingRestProxy(rest, token)
        
        rest.expect_get("/test?a=1&b=2&token=%3B+%2F+%3F+%3A+%40+%3D+%26+++%3C+%3E"
            "+%23+%25+%7B+%7D+%7C+%5C+%5E+%7E+%5B+%5D", 200, {})
        auth_rest.get("/test?a=1&b=2")

    def test_delete(self):
        # DELETE behaves exactly like GET, so only the basics are tested.
        rest = _RestProxyForTest()
        token = 'my_token'
        auth_rest = AuthorizingRestProxy(rest, token)
        
        rest.expect_delete("/test?token=my_token", 200)
        auth_rest.delete("/test")
        
        rest.expect_delete("/test?a=1&b=2&token=my_token", 200)
        auth_rest.delete("/test?a=1&b=2")