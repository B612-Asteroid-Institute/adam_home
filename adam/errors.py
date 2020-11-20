"""ADAM errors"""


class CredentialsParseError(Exception):
    """Error when ADAM credentials (JSON) could not be parsed"""
    pass


class CredentialsMissingError(Exception):
    """Error when ADAM credentials are missing access token or refresh token"""
    pass


class InvalidCredentialsError(Exception):
    "Error when the ADAM server is unable to validate the user's credentials"
    pass
