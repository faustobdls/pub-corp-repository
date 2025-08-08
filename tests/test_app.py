import pytest
from unittest.mock import Mock, patch, MagicMock
from flask import Flask
from pub_proxy.api.app import create_app


class TestConfig:
    """Test configuration class."""
    DEBUG = True
    TESTING = True
    SECRET_KEY = 'test-secret-key'
    DATABASE_URL = 'sqlite:///:memory:'


class TestApp:
    """Test cases for the Flask app creation."""
    
    @patch('pub_proxy.api.app.FlaskInjector')
    @patch('pub_proxy.api.app.register_routes')
    @patch('pub_proxy.api.app.configure_container')
    @patch('pub_proxy.api.app.Injector')
    @patch('pub_proxy.api.app.CORS')
    def test_create_app_basic(self, mock_cors, mock_injector, mock_configure_container, mock_register_routes, mock_flask_injector):
        """Test basic app creation."""
        config = TestConfig()
        app = create_app(config)
        
        assert isinstance(app, Flask)
        assert app.config['DEBUG'] is True
        assert app.config['TESTING'] is True
        assert app.config['SECRET_KEY'] == 'test-secret-key'
        assert app.config['DATABASE_URL'] == 'sqlite:///:memory:'
    
    @patch('pub_proxy.api.app.FlaskInjector')
    @patch('pub_proxy.api.app.register_routes')
    @patch('pub_proxy.api.app.configure_container')
    @patch('pub_proxy.api.app.Injector')
    @patch('pub_proxy.api.app.CORS')
    def test_cors_enabled(self, mock_cors, mock_injector, mock_configure_container, mock_register_routes, mock_flask_injector):
        """Test that CORS is enabled."""
        config = TestConfig()
        app = create_app(config)
        
        mock_cors.assert_called_once_with(app)
    
    @patch('pub_proxy.api.app.FlaskInjector')
    @patch('pub_proxy.api.app.register_routes')
    @patch('pub_proxy.api.app.configure_container')
    @patch('pub_proxy.api.app.Injector')
    @patch('pub_proxy.api.app.CORS')
    def test_dependency_injection_setup(self, mock_cors, mock_injector, mock_configure_container, mock_register_routes, mock_flask_injector):
        """Test that dependency injection is set up correctly."""
        config = TestConfig()
        mock_injector_instance = MagicMock()
        mock_injector.return_value = mock_injector_instance
        
        app = create_app(config)
        
        # Verify Injector was called
        mock_injector.assert_called_once()
        
        # Verify FlaskInjector was called with app and injector
        mock_flask_injector.assert_called_once_with(app=app, injector=mock_injector_instance)
    
    @patch('pub_proxy.api.app.FlaskInjector')
    @patch('pub_proxy.api.app.register_routes')
    @patch('pub_proxy.api.app.configure_container')
    @patch('pub_proxy.api.app.Injector')
    @patch('pub_proxy.api.app.CORS')
    def test_routes_registration(self, mock_cors, mock_injector, mock_configure_container, mock_register_routes, mock_flask_injector):
        """Test that routes are registered."""
        config = TestConfig()
        app = create_app(config)
        
        mock_register_routes.assert_called_once_with(app)
    
    @patch('pub_proxy.api.app.FlaskInjector')
    @patch('pub_proxy.api.app.register_routes')
    @patch('pub_proxy.api.app.configure_container')
    @patch('pub_proxy.api.app.Injector')
    @patch('pub_proxy.api.app.CORS')
    def test_injector_called_with_list(self, mock_cors, mock_injector, mock_configure_container, mock_register_routes, mock_flask_injector):
        """Test that Injector is called with a list containing a lambda function."""
        config = TestConfig()
        
        app = create_app(config)
        
        # Verify Injector was called with a list
        mock_injector.assert_called_once()
        call_args = mock_injector.call_args[0]
        assert len(call_args) == 1
        assert isinstance(call_args[0], list)
        assert len(call_args[0]) == 1
        assert callable(call_args[0][0])
    
    @patch('pub_proxy.api.app.FlaskInjector')
    @patch('pub_proxy.api.app.register_routes')
    @patch('pub_proxy.api.app.configure_container')
    @patch('pub_proxy.api.app.Injector')
    @patch('pub_proxy.api.app.CORS')
    def test_returns_flask_app(self, mock_cors, mock_injector, mock_configure_container, mock_register_routes, mock_flask_injector):
        """Test that the function returns a Flask app instance."""
        config = TestConfig()
        app = create_app(config)
        
        assert isinstance(app, Flask)
    
    @patch('pub_proxy.api.app.FlaskInjector')
    @patch('pub_proxy.api.app.register_routes')
    @patch('pub_proxy.api.app.configure_container')
    @patch('pub_proxy.api.app.Injector')
    @patch('pub_proxy.api.app.CORS')
    def test_app_name_is_correct(self, mock_cors, mock_injector, mock_configure_container, mock_register_routes, mock_flask_injector):
        """Test that the Flask app has the correct name."""
        config = TestConfig()
        app = create_app(config)
        
        assert app.name == 'pub_proxy.api.app'