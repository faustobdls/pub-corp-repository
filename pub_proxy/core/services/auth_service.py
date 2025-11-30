import os
import jwt
import datetime
from injector import inject
from pub_proxy.core.app_config import AppConfig

class AuthService:
    """
    Service for authentication and authorization.
    """
    
    @inject
    def __init__(self, config: AppConfig):
        self.config = config
        self._secret_key = config.get('JWT_SECRET', 'super-secret-jwt-key')
        self._admin_username = config.get('ADMIN_USERNAME', 'admin')
        self._admin_password = config.get('ADMIN_PASSWORD', 'admin')
        # Legacy token support
        self._legacy_token = os.environ.get('AUTH_TOKEN', 'secret-token')
        
    def login(self, username, password):
        """
        Authenticate a user and return a JWT token.
        
        @param username: The username.
        @param password: The password.
        @return: A JWT token if authentication is successful, None otherwise.
        """
        if username == self._admin_username and password == self._admin_password:
            payload = {
                'sub': username,
                'iat': datetime.datetime.utcnow(),
                'exp': datetime.datetime.utcnow() + datetime.timedelta(days=365) # Long-lived token for CLI convenience
            }
            token = jwt.encode(payload, self._secret_key, algorithm='HS256')
            # In pyjwt >= 2.0.0, encode returns a string, but in older versions bytes.
            # Let's ensure it's a string.
            if isinstance(token, bytes):
                token = token.decode('utf-8')
            return token
        return None

    def validate_token(self, token):
        """
        Validate the provided token.
        
        @param token: The token to validate.
        @return: True if the token is valid, False otherwise.
        """
        # Check legacy token first
        if token == self._legacy_token:
            return True
            
        try:
            jwt.decode(token, self._secret_key, algorithms=['HS256'])
            return True
        except jwt.ExpiredSignatureError:
            print("Token expired")
            return False
        except jwt.InvalidTokenError:
            print("Invalid token")
            return False
