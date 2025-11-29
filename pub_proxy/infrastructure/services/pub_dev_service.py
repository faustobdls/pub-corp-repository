import requests
from flask import Response
from injector import inject
from pub_proxy.core.app_config import AppConfig

"""
Pub.dev Service module.

This module defines the service for interacting with the pub.dev API.
It handles fetching package information, downloading packages, and proxying requests to pub.dev.

@example
```python
from pub_proxy.infrastructure.services.pub_dev_service import PubDevService

pub_dev_service = PubDevService(config)
package_info = pub_dev_service.get_package_info('flutter')
```
"""


class PubDevService:
    """
    Service for interacting with the pub.dev API.
    
    This class handles fetching package information, downloading packages, and proxying requests to pub.dev.
    It provides methods for getting package information, searching for packages, downloading packages,
    and proxying arbitrary requests to pub.dev.
    
    @method get_package_info: Get information about a package from pub.dev.
    @method get_package_version: Get information about a specific version of a package from pub.dev.
    @method search_packages: Search for packages on pub.dev.
    @method download_package: Download a package from pub.dev.
    @method proxy_request: Proxy an arbitrary request to pub.dev.
    """
    
    @inject
    def __init__(self, config: AppConfig):
        """
        Initialize the service with its dependencies.
        
        @param config: The application configuration.
        """
        self.pub_dev_url = config['PUB_DEV_URL']
        self.api_url = f"{self.pub_dev_url}/api"
    
    def get_package_info(self, package_name):
        """
        Get information about a package from pub.dev.
        
        @param package_name: The name of the package.
        @return: A dictionary with the package information or None if not found.
        @raises: Exception if the request fails due to network error.
        """
        try:
            url = f"{self.api_url}/packages/{package_name}"
            response = requests.get(url)
            
            if response.status_code == 200:
                return response.json()
            else:
                return None
        except requests.exceptions.RequestException as e:
            return None
    
    def get_package_version(self, package_name, version):
        """
        Get information about a specific version of a package from pub.dev.
        
        @param package_name: The name of the package.
        @param version: The version of the package.
        @return: A dictionary with the version information or None if not found.
        @raises: Exception if the request fails due to network error.
        """
        try:
            url = f"{self.api_url}/packages/{package_name}/versions/{version}"
            response = requests.get(url)
            
            if response.status_code == 200:
                return response.json()
            else:
                return None
        except requests.exceptions.RequestException as e:
            return None
    
    def search_packages(self, query, page=1, page_size=10):
        """
        Search for packages on pub.dev.
        
        @param query: The search query.
        @param page: The page number for pagination.
        @param page_size: The number of packages per page.
        @return: A dictionary with the search results or None if not found.
        @raises: Exception if the request fails due to network error.
        """
        try:
            url = f"{self.api_url}/search"
            params = {
                'q': query,
                'page': page,
                'page_size': page_size
            }
            
            response = requests.get(url, params=params)
            
            if response.status_code == 200:
                return response.json()
            else:
                return None
        except requests.exceptions.RequestException as e:
             return None
    
    def download_package(self, package_name, version):
        """
        Download a package tarball from pub.dev.
        
        @param package_name: The name of the package.
        @param version: The version of the package.
        @return: A Flask Response object with the package tarball or None if network error.
        @raises: Exception if the request fails due to network error.
        """
        try:
            url = f"{self.pub_dev_url}/packages/{package_name}/versions/{version}.tar.gz"
            
            response = requests.get(url, stream=True)
            
            # Create a Flask response with the same status code, headers, and content
            flask_response = Response(
                response=response.iter_content(chunk_size=1024) if response.status_code == 200 else b'',
                status=response.status_code,
                headers=dict(response.headers) if hasattr(response, 'headers') and response.headers else {}
            )
            
            return flask_response
        except requests.exceptions.RequestException as e:
            return None
    
    def proxy_request(self, path, method, headers, data):
        """
        Proxy an arbitrary request to pub.dev.
        
        @param path: The path to proxy to pub.dev.
        @param method: The HTTP method to use.
        @param headers: The HTTP headers to include in the request.
        @param data: The request body data.
        @return: The response from pub.dev or None if network error.
        @raises: Exception if the request fails.
        """
        try:
            url = f"{self.pub_dev_url}{path}"
            
            # Remove headers that might cause issues
            headers_copy = headers.copy()
            headers_to_remove = ['Host', 'Content-Length']
            for header in headers_to_remove:
                if header in headers_copy:
                    del headers_copy[header]
            
            # Make the request to pub.dev
            response = requests.request(
                method=method,
                url=url,
                headers=headers_copy,
                data=data,
                stream=True
            )
            
            # Create a Flask response with the same status code, headers, and content
            flask_response = Response(
                response=response.iter_content(chunk_size=1024),
                status=response.status_code,
                headers=dict(response.headers) if hasattr(response, 'headers') and response.headers else {}
            )
            
            return flask_response
        except requests.exceptions.RequestException as e:
            return None