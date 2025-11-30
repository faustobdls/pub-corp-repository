import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

"""
Configuration module for the application.

This module loads environment variables and provides configuration settings for the application.
It includes settings for the Flask application, GCP bucket, and pub.dev proxy.

@example
```python
from config import Config

app = Flask(__name__)
app.config.from_object(Config)
```
"""
class Config:
    """
    Configuration class for the application.
    
    This class contains all the configuration settings for the application.
    It loads values from environment variables with sensible defaults.
    
    @property DEBUG: Whether the application is in debug mode.
    @property SECRET_KEY: Secret key for the Flask application.
    @property STORAGE_TYPE: Type of storage to use ('gcp' or 'local').
    @property GCP_BUCKET_NAME: Name of the GCP bucket for package storage.
    @property GCP_PROJECT_ID: ID of the GCP project.
    @property LOCAL_STORAGE_DIR: Directory for local storage.
    @property PUB_DEV_URL: URL of the pub.dev API.
    @property CACHE_TIMEOUT: Timeout for cache in seconds.
    """
    # Flask settings
    DEBUG = os.getenv('DEBUG', 'False').lower() in ('true', '1', 't')
    SECRET_KEY = os.getenv('SECRET_KEY', 'dev-key-change-in-production')
    HOST = os.getenv('HOST', '0.0.0.0')
    PORT = int(os.getenv('PORT', '5000'))
    
    # Auth settings
    JWT_SECRET = os.getenv('JWT_SECRET', 'super-secret-jwt-key')
    ADMIN_USERNAME = os.getenv('ADMIN_USERNAME', 'admin')
    ADMIN_PASSWORD = os.getenv('ADMIN_PASSWORD', 'admin')
    
    # Storage settings
    STORAGE_TYPE = os.getenv('STORAGE_TYPE', 'local')  # 'gcp' or 'local'
    
    # GCP settings
    GCP_BUCKET_NAME = os.getenv('GCP_BUCKET_NAME', 'pub-corp-repository')
    GCP_PROJECT_ID = os.getenv('GCP_PROJECT_ID', 'your-project-id')
    
    # Local storage settings
    LOCAL_STORAGE_DIR = os.getenv('LOCAL_STORAGE_DIR', os.path.join(os.path.dirname(os.path.abspath(__file__)), 'storage'))
    
    # Pub.dev settings
    PUB_DEV_URL = os.getenv('PUB_DEV_URL', 'https://pub.dev')
    
    # Cache settings
    try:
        CACHE_TIMEOUT = int(os.getenv('CACHE_TIMEOUT', '3600'))  # 1 hour by default
        print("CACHE_TIMEOUT read from env")
    except ValueError:
        CACHE_TIMEOUT = 3600  # 1 hour by default
        print("CACHE_TIMEOUT not read from env, using default")

