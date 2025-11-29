import os
from injector import inject

class AuthService:
    """
    Service for authentication and authorization.
    """
    
    def __init__(self):
        self._token = os.environ.get('AUTH_TOKEN', 'secret-token')
        
    def validate_token(self, token):
        """
        Validate the provided token.
        
        @param token: The token to validate.
        @return: True if the token is valid, False otherwise.
        """
        is_valid = token == self._token
        if not is_valid:
            print(f"Auth failed. Expected: {self._token[:3]}...{self._token[-3:]}, Received: {token[:3]}...{token[-3:]}")
        return is_valid
