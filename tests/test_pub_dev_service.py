import unittest
from unittest.mock import Mock, patch, MagicMock
import requests
from flask import Response

from pub_proxy.infrastructure.services.pub_dev_service import PubDevService


class TestPubDevService(unittest.TestCase):
    def setUp(self):
        """Set up test fixtures."""
        self.config = {
            'PUB_DEV_URL': 'https://pub.dev'
        }
        self.service = PubDevService(self.config)
        
    def test_init(self):
        """Test service initialization."""
        self.assertEqual(self.service.pub_dev_url, 'https://pub.dev')
        self.assertEqual(self.service.api_url, 'https://pub.dev/api')
        
    @patch('pub_proxy.infrastructure.services.pub_dev_service.requests.get')
    def test_get_package_info_success(self, mock_get):
        """Test successful package info retrieval."""
        # Mock response
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            'name': 'flutter',
            'latest': {'version': '3.0.0'},
            'versions': []
        }
        mock_get.return_value = mock_response
        
        # Call the method
        result = self.service.get_package_info('flutter')
        
        # Assertions
        self.assertIsNotNone(result)
        self.assertEqual(result['name'], 'flutter')
        mock_get.assert_called_once_with('https://pub.dev/api/packages/flutter')
        
    @patch('pub_proxy.infrastructure.services.pub_dev_service.requests.get')
    def test_get_package_info_not_found(self, mock_get):
        """Test package info retrieval when package not found."""
        # Mock 404 response
        mock_response = Mock()
        mock_response.status_code = 404
        mock_get.return_value = mock_response
        
        # Call the method
        result = self.service.get_package_info('non_existing_package')
        
        # Assertions
        self.assertIsNone(result)
        mock_get.assert_called_once_with('https://pub.dev/api/packages/non_existing_package')
        
    @patch('pub_proxy.infrastructure.services.pub_dev_service.requests.get')
    def test_get_package_info_request_exception(self, mock_get):
        """Test package info retrieval when request fails."""
        # Mock request exception
        mock_get.side_effect = requests.RequestException('Network error')
        
        # Call the method
        result = self.service.get_package_info('flutter')
        
        # Assertions
        self.assertIsNone(result)
        
    @patch('pub_proxy.infrastructure.services.pub_dev_service.requests.get')
    def test_get_package_version_success(self, mock_get):
        """Test successful package version retrieval."""
        # Mock response
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            'version': '3.0.0',
            'pubspec': {'name': 'flutter', 'version': '3.0.0'},
            'archive_url': 'https://pub.dev/packages/flutter/versions/3.0.0.tar.gz'
        }
        mock_get.return_value = mock_response
        
        # Call the method
        result = self.service.get_package_version('flutter', '3.0.0')
        
        # Assertions
        self.assertIsNotNone(result)
        self.assertEqual(result['version'], '3.0.0')
        mock_get.assert_called_once_with('https://pub.dev/api/packages/flutter/versions/3.0.0')
        
    @patch('pub_proxy.infrastructure.services.pub_dev_service.requests.get')
    def test_get_package_version_not_found(self, mock_get):
        """Test package version retrieval when version not found."""
        # Mock 404 response
        mock_response = Mock()
        mock_response.status_code = 404
        mock_get.return_value = mock_response
        
        # Call the method
        result = self.service.get_package_version('flutter', '999.0.0')
        
        # Assertions
        self.assertIsNone(result)
        
    @patch('pub_proxy.infrastructure.services.pub_dev_service.requests.get')
    def test_get_package_version_request_exception(self, mock_get):
        """Test package version retrieval when request fails."""
        # Mock request exception
        mock_get.side_effect = requests.RequestException('Network error')
        
        # Call the method
        result = self.service.get_package_version('flutter', '3.0.0')
        
        # Assertions
        self.assertIsNone(result)
        
    @patch('pub_proxy.infrastructure.services.pub_dev_service.requests.get')
    def test_search_packages_success(self, mock_get):
        """Test successful package search."""
        # Mock response
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            'packages': [
                {'package': 'flutter'},
                {'package': 'flutter_test'}
            ],
            'next': None
        }
        mock_get.return_value = mock_response
        
        # Call the method
        result = self.service.search_packages('flutter')
        
        # Assertions
        self.assertIsNotNone(result)
        self.assertEqual(len(result['packages']), 2)
        mock_get.assert_called_once_with(
            'https://pub.dev/api/search',
            params={'q': 'flutter', 'page': 1, 'page_size': 10}
        )
        
    @patch('pub_proxy.infrastructure.services.pub_dev_service.requests.get')
    def test_search_packages_with_pagination(self, mock_get):
        """Test package search with custom pagination."""
        # Mock response
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {'packages': [], 'next': None}
        mock_get.return_value = mock_response
        
        # Call the method with custom pagination
        result = self.service.search_packages('flutter', page=2, page_size=20)
        
        # Assertions
        mock_get.assert_called_once_with(
            'https://pub.dev/api/search',
            params={'q': 'flutter', 'page': 2, 'page_size': 20}
        )
        
    @patch('pub_proxy.infrastructure.services.pub_dev_service.requests.get')
    def test_search_packages_request_exception(self, mock_get):
        """Test package search when request fails."""
        # Mock request exception
        mock_get.side_effect = requests.RequestException('Network error')
        
        # Call the method
        result = self.service.search_packages('flutter')
        
        # Assertions
        self.assertIsNone(result)
        
    @patch('pub_proxy.infrastructure.services.pub_dev_service.requests.get')
    def test_search_packages_connection_error(self, mock_get):
        """Test search packages with connection error."""
        # Mock requests to raise a connection exception
        mock_get.side_effect = requests.exceptions.ConnectionError('Connection error')
        
        # Call the method
        result = self.service.search_packages('test')
        
        # Should return None
        self.assertIsNone(result)
        
        # Verify the request was attempted
        mock_get.assert_called_once_with(
            'https://pub.dev/api/search',
            params={'q': 'test', 'page': 1, 'page_size': 10}
        )
        
    @patch('pub_proxy.infrastructure.services.pub_dev_service.requests.get')
    def test_download_package_success(self, mock_get):
        """Test successful package download."""
        # Mock response
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.content = b'package content'
        mock_response.headers = {'content-type': 'application/gzip'}
        mock_get.return_value = mock_response
        
        # Call the method
        result = self.service.download_package('flutter', '3.0.0')
        
        # Assertions
        self.assertIsNotNone(result)
        self.assertEqual(result.status_code, 200)
        expected_url = 'https://pub.dev/packages/flutter/versions/3.0.0.tar.gz'
        mock_get.assert_called_once_with(expected_url, stream=True)
        
    @patch('pub_proxy.infrastructure.services.pub_dev_service.requests.get')
    def test_download_package_not_found(self, mock_get):
        """Test package download when package not found."""
        # Mock 404 response
        mock_response = Mock()
        mock_response.status_code = 404
        mock_response.headers = {}
        mock_get.return_value = mock_response
        
        # Call the method
        result = self.service.download_package('non_existing', '1.0.0')
        
        # Assertions
        self.assertIsNotNone(result)
        self.assertEqual(result.status_code, 404)
        
    @patch('pub_proxy.infrastructure.services.pub_dev_service.requests.get')
    def test_download_package_request_exception(self, mock_get):
        """Test package download when request fails."""
        # Mock request exception
        mock_get.side_effect = requests.RequestException('Network error')
        
        # Call the method
        result = self.service.download_package('flutter', '3.0.0')
        
        # Assertions
        self.assertIsNone(result)
        
    @patch('pub_proxy.infrastructure.services.pub_dev_service.requests.request')
    def test_proxy_request_get_success(self, mock_request):
        """Test successful GET proxy request."""
        # Mock response
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.content = b'response content'
        mock_response.headers = {'content-type': 'application/json'}
        mock_request.return_value = mock_response
        
        # Call the method
        result = self.service.proxy_request('/api/packages/flutter', 'GET', {}, None)
        
        # Assertions
        self.assertIsInstance(result, Response)
        self.assertEqual(result.status_code, 200)
        expected_url = 'https://pub.dev/api/packages/flutter'
        mock_request.assert_called_once_with(
            method='GET', url=expected_url, headers={}, data=None, stream=True
        )
        
    @patch('pub_proxy.infrastructure.services.pub_dev_service.requests.request')
    def test_proxy_request_post_with_data(self, mock_request):
        """Test POST proxy request with data."""
        # Mock response
        mock_response = Mock()
        mock_response.status_code = 201
        mock_response.content = b'created'
        mock_response.headers = {'content-type': 'application/json'}
        mock_request.return_value = mock_response
        
        # Call the method
        headers = {'Authorization': 'Bearer token'}
        data = {'key': 'value'}
        result = self.service.proxy_request('/api/packages', 'POST', headers, data)
        
        # Assertions
        self.assertIsInstance(result, Response)
        self.assertEqual(result.status_code, 201)
        expected_url = 'https://pub.dev/api/packages'
        mock_request.assert_called_once_with(
            method='POST', url=expected_url, headers=headers, data=data, stream=True
        )
        
    @patch('pub_proxy.infrastructure.services.pub_dev_service.requests.request')
    def test_proxy_request_exception(self, mock_request):
        """Test proxy request when request fails."""
        # Mock request exception
        mock_request.side_effect = requests.RequestException('Network error')
        
        # Call the method
        result = self.service.proxy_request('/api/packages/flutter', 'GET', {}, None)
        
        # Assertions
        self.assertIsNone(result)
        
    @patch('pub_proxy.infrastructure.services.pub_dev_service.requests.request')
    def test_proxy_request_timeout_exception(self, mock_request):
        """Test proxy request with timeout exception handling."""
        # Mock requests to raise a timeout exception
        mock_request.side_effect = requests.exceptions.Timeout('Request timeout')
        
        # Call the method
        result = self.service.proxy_request('/api/packages/test', 'GET', {}, None)
        
        # Should return None due to exception
        self.assertIsNone(result)
        
        # Verify the request was attempted
        expected_url = 'https://pub.dev/api/packages/test'
        mock_request.assert_called_once_with(
            method='GET', url=expected_url, headers={}, data=None, stream=True
        )
        
    @patch('pub_proxy.infrastructure.services.pub_dev_service.requests.request')
    def test_proxy_request_with_custom_headers(self, mock_request):
        """Test proxy request with custom headers."""
        # Mock response
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.content = b'response'
        mock_response.headers = {
            'content-type': 'application/json',
            'custom-header': 'custom-value'
        }
        mock_request.return_value = mock_response
        
        # Call the method
        custom_headers = {'User-Agent': 'Test Agent'}
        result = self.service.proxy_request('/api/test', 'GET', custom_headers, None)
        
        # Assertions
        self.assertIsInstance(result, Response)
        mock_request.assert_called_once_with(
            method='GET', url='https://pub.dev/api/test', headers=custom_headers, data=None, stream=True
        )


if __name__ == '__main__':
    unittest.main()