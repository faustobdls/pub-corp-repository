from flask import Flask
from flask_cors import CORS
from flask_injector import FlaskInjector
from injector import Injector

from pub_proxy.api.routes import register_routes
from pub_proxy.infrastructure.container import configure_container

"""
Flask application factory module.

This module contains the factory function for creating a Flask application instance.
It configures the application, registers routes, and sets up dependency injection.

@example
```python
from pub_proxy.api.app import create_app
from config import Config

app = create_app(Config)
app.run()
```
"""


def create_app(config_object):
    """
    Create and configure a Flask application instance.
    
    This function creates a new Flask application, configures it with the provided
    configuration object, sets up CORS, initializes dependency injection, and registers routes.
    
    @param config_object: The configuration object to use for the application.
    @return: The configured Flask application instance.
    """
    app = Flask(__name__)
    app.config.from_object(config_object)
    
    # Enable CORS
    CORS(app)
    
    # Set up dependency injection
    injector = Injector([lambda binder: configure_container(binder, app.config)])
    
    # Register routes
    register_routes(app)
    
    # Initialize FlaskInjector
    FlaskInjector(app=app, injector=injector)
    
    return app