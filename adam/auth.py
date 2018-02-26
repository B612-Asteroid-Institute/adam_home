"""
    auth.py
"""

import adam

class Auth(object):
    """Module for generating, validating, and using authentication tokens

    """
    def __init__(self, rest):
        """Expects a RestProxy that it will use to communicate with the server for
        authentication.

        """
        self._rest = rest
        self.__clear_attributes__()

    def __repr__(self):
        """
        Args:
            None

        Returns:
            A string describing the contents of this authentication object.
        """
        return "Auth [token=" + self._token + ",email=" + self._email + "]"
    
    def get_token(self):
        """Accessor for token.
        
        Returns:
            Stored token. If accessed before call to authenticate, will be empty.
        """
        return self._token
    
    def get_user(self):
        """Accessor for user email.
        
        Returns:
            Stored user email. If accessed before call to authenticate, will be empty.
        """
        return self._email
    
    def get_logged_in(self):
        """Accessor for logged in.
        
        Returns:
            Stored logged in value. If accessed before call to authenticate, will be False.
        """
        return self._logged_in
        
    def __validate_token__(self, token):
        path = ""
        if token == "":
            path = '/me'
        else:
            path = '/me?token=' + token
        code, response = self._rest.get(path)
        return code, response
    
    def __clear_attributes__(self):
        self._token = ''
        self._logged_in = False
        self._email = ''
    
    def authenticate(self, token):
        """Checks whether the given token is valid. If so, updates this object to 
        hold information about the token's logged in user. If not, clears information
        from this object.
        
        Returns:
            Whether this object now reflects a valid user session.
        """
        code, response = self.__validate_token__(token)

        # Check error code
        if code != 200:
            # Handle 503s, since this is how the server communicates authentication
            # errors.
            if 'error' in response:
                if response['error']['message'].startswith('org.apache.shiro.authc.'):
                    self.__clear_attributes__()
                    return False
                    
            raise RuntimeError("Server status code: %s; Response: %s" % (code, response))
        
        if 'loggedIn' in response and response['loggedIn']:
            self._token = token
            self._logged_in = response['loggedIn']
            if self._logged_in:
                self._email = response['email']
            else:
                self._email = ''
            return True
        else:
            self.__clear_attributes__()
            return False
