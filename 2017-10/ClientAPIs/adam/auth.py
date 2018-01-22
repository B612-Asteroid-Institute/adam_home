"""
    auth.py
"""

from adam.rest_proxy import RestRequests
import adam

class Auth(object):
    """Module for generating, validating, and using authentication tokens

    """
    def __init__(self):
        """Initializes attributes

        """
        self._rest = RestRequests()   # rest request option (requests package or proxy)
        self.__clear_attributes__()

    def __repr__(self):
        """
        Args:
            None

        Returns:
            A string describing the contents of this authorization object.
        """
        return "Auth [token=" + self._token + ",email=" + self._email + "]"

    def set_rest_accessor(self, proxy):
        """Override network access methods

        This function overrides network access and sets the rest request to a proxy

        Args:
            proxy (class)

        Returns:
            None
        """
        self._rest = proxy
    
    def get_token(self):
        """Accessor for token.
        
        Returns:
            Stored token. If accessed before call to authorize, will be empty.
        """
        return self._token
    
    def get_user(self):
        """Accessor for user email.
        
        Returns:
            Stored user email. If accessed before call to authorize, will be empty.
        """
        return self._email
    
    def get_logged_in(self):
        """Accessor for logged in.
        
        Returns:
            Stored logged in value. If accessed before call to authorize, will be False.
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
    
    def authorize(self, token):
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
    
    def authorize_from_file(self, filename):
        """Reads the contents of the file by the given name as a token, then attempts
        to authorize using that token. If successful, updates this object to 
        hold information about the token's logged in user. If not, clears information
        from this object.
        
        Returns:
            Whether this object now reflects a valid user session.
        """
        token = ""
        try:
            with open(filename, "r") as f:
                token = f.read()
        except IOError:
            return False

        return self.authorize(token)
    
    def initial_authorization(self):
        """Prompts the user to log in in the browser, then paste the generated token
        back here. If the token generated is valid, updates this object to hold
        information about the logged in user. If not, clears information from this object.
        
        Returns:
            Whether this object now reflects a valid user session.
        """
        message = (
            "Please visit http://pro-equinox-162418.appspot.com/token.html "
            "in a browser. Please choose your method of authorization, then paste the "
            "generated token here: ")
        token = input(message)
        
        return self.authorize(token)
