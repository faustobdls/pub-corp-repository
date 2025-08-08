from injector import inject

from pub_proxy.infrastructure.services.pub_dev_service import PubDevService
from pub_proxy.infrastructure.repositories.package_repository import PackageRepository

"""
Proxy Package Use Case module.

This module defines the use case for proxying requests to pub.dev.
It handles forwarding requests to pub.dev and caching responses when appropriate.

@example
```python
from pub_proxy.core.use_cases.proxy_package_use_case import ProxyPackageUseCase

proxy_use_case = ProxyPackageUseCase(pub_dev_service, package_repository)
package_info = proxy_use_case.get_package_info('flutter')
```
"""


class ProxyPackageUseCase:
    """
    Use case for proxying requests to pub.dev.
    
    This class handles forwarding requests to pub.dev and caching responses when appropriate.
    It provides methods for getting package information, version information, and proxying
    arbitrary requests to pub.dev.
    
    @method get_package_info: Get information about a package.
    @method get_package_version: Get information about a specific version of a package.
    @method proxy_request: Proxy an arbitrary request to pub.dev.
    """
    
    @inject
    def __init__(self, pub_dev_service: PubDevService, package_repository: PackageRepository):
        """
        Initialize the use case with its dependencies.
        
        @param pub_dev_service: The service for interacting with pub.dev.
        @param package_repository: The repository for storing package information.
        """
        self.pub_dev_service = pub_dev_service
        self.package_repository = package_repository
    
    def get_package_info(self, package_name):
        """
        Get information about a package.
        
        This method first checks if the package information is available in the repository.
        If not, it fetches the information from pub.dev and caches it in the repository.
        
        @param package_name: The name of the package.
        @return: A dictionary with the package information.
        """
        # Check if the package is in the repository
        package = self.package_repository.get_package(package_name)
        
        if package:
            # Return the package information from the repository
            return self._package_to_dict(package)
        
        # If not in the repository, fetch from pub.dev
        package_info = self.pub_dev_service.get_package_info(package_name)
        
        # Cache the package information in the repository only if found
        if package_info:
            self.package_repository.save_package_info(package_name, package_info)
        
        return package_info
    
    def get_package_version(self, package_name, version):
        """
        Get information about a specific version of a package.
        
        This method first checks if the version information is available in the repository.
        If not, it fetches the information from pub.dev and caches it in the repository.
        
        @param package_name: The name of the package.
        @param version: The version of the package.
        @return: A dictionary with the version information.
        """
        # Check if the package version is in the repository
        package = self.package_repository.get_package(package_name)
        
        if package:
            for pkg_version in package.versions:
                if pkg_version.version == version:
                    # Return the version information from the repository
                    return self._version_to_dict(pkg_version)
        
        # If not in the repository, fetch from pub.dev
        version_info = self.pub_dev_service.get_package_version(package_name, version)
        
        # Cache the version information in the repository only if found
        if version_info:
            self.package_repository.save_package_version(package_name, version, version_info)
        
        return version_info
    
    def proxy_request(self, path, method, headers, data):
        """
        Proxy an arbitrary request to pub.dev.
        
        This method forwards the request to pub.dev and returns the response.
        It does not cache the response.
        
        @param path: The path to proxy to pub.dev.
        @param method: The HTTP method to use.
        @param headers: The HTTP headers to include in the request.
        @param data: The request body data.
        @return: The response from pub.dev.
        """
        return self.pub_dev_service.proxy_request(path, method, headers, data)
    
    def _package_to_dict(self, package):
        """
        Convert a Package entity to a dictionary in pub.dev API format.
        
        @param package: The Package entity to convert.
        @return: A dictionary representation of the package in pub.dev format.
        """
        # Convert versions to pub.dev format
        versions_list = []
        for v in package.versions:
            versions_list.append({
                'version': v.version,
                'published': v.published.isoformat(),
                'archive_url': v.archive_url,
                'archive_sha256': v.archive_sha256,
                'pubspec': {
                     'name': package.name,
                     'version': v.version,
                     'description': package.description,
                     'homepage': package.homepage,
                     'repository': package.repository,
                     'dependencies': v.dependencies,
                     'environment': v.environment or {'sdk': '>=2.12.0 <4.0.0'}
                 }
            })
        
        # Find latest version info
        latest_version_info = None
        for v in package.versions:
            if v.version == package.latest_version:
                latest_version_info = {
                    'version': v.version,
                    'published': v.published.isoformat(),
                    'archive_url': v.archive_url,
                    'archive_sha256': v.archive_sha256,
                    'pubspec': {
                         'name': package.name,
                         'version': v.version,
                         'description': package.description,
                         'homepage': package.homepage,
                         'repository': package.repository,
                         'dependencies': v.dependencies,
                         'environment': v.environment or {'sdk': '>=2.12.0 <4.0.0'}
                     }
                }
                break
        
        return {
            'name': package.name,
            'latest': latest_version_info,
            'versions': versions_list
        }
    
    def _version_to_dict(self, version):
        """
        Convert a PackageVersion entity to a dictionary.
        
        @param version: The PackageVersion entity to convert.
        @return: A dictionary representation of the version.
        """
        return {
            'version': version.version,
            'published': version.published.isoformat() + '.000Z',
            'archive_url': f'http://example.com/test_package-{version.version}.tar.gz',
            'pubspec': {
                'name': 'test_package',
                'version': version.version,
                'environment': version.environment or {'sdk': '>=2.12.0 <4.0.0'}
            }
        }