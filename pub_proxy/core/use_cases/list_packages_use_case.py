from injector import inject

from pub_proxy.infrastructure.repositories.package_repository import PackageRepository
from pub_proxy.infrastructure.services.pub_dev_service import PubDevService

"""
List Packages Use Case module.

This module defines the use case for listing packages available in the repository.
It handles fetching packages from the repository and pub.dev, and combining the results.

@example
```python
from pub_proxy.core.use_cases.list_packages_use_case import ListPackagesUseCase

list_use_case = ListPackagesUseCase(package_repository, pub_dev_service)
packages = list_use_case.execute('flutter', 1, 10)
```
"""


class ListPackagesUseCase:
    """
    Use case for listing packages available in the repository.
    
    This class handles fetching packages from the repository and pub.dev, and combining the results.
    It provides a method for listing packages with pagination and search functionality.
    
    @method execute: List packages available in the repository.
    """
    
    @inject
    def __init__(self, package_repository: PackageRepository, pub_dev_service: PubDevService):
        """
        Initialize the use case with its dependencies.
        
        @param package_repository: The repository for storing package information.
        @param pub_dev_service: The service for interacting with pub.dev.
        """
        self.package_repository = package_repository
        self.pub_dev_service = pub_dev_service
    
    def execute(self, query='', page=1, page_size=10):
        """
        List packages available in the repository.
        
        This method fetches packages from the repository and pub.dev, combines the results,
        and returns a paginated list of packages matching the query.
        
        @param query: The search query to filter packages by name or description.
        @param page: The page number for pagination.
        @param page_size: The number of packages per page.
        @return: A dictionary with the list of packages and pagination information.
        """
        # Get packages from the repository
        private_packages = self.package_repository.list_packages(query)
        
        # Get packages from pub.dev
        pub_dev_packages = self.pub_dev_service.search_packages(query, page, page_size)
        
        # Combine the results, giving priority to private packages
        packages = private_packages.copy()
        
        # Add pub.dev packages that are not in the repository
        private_package_names = {p['name'] for p in private_packages}
        if pub_dev_packages is not None:
            for package_data in pub_dev_packages.get('packages', []):
                # Pub.dev search API returns {'package': 'name'}
                pkg_name = package_data.get('package')
                if pkg_name and pkg_name not in private_package_names:
                    # Convert to the format expected by the template
                    packages.append({
                        'name': pkg_name,
                        'latest_version': 'latest',  # Search API doesn't return version
                        'description': 'Package from pub.dev',  # Search API doesn't return description
                        'is_private': False,
                        'homepage': f'https://pub.dev/packages/{pkg_name}',
                        'repository': None
                    })
        
        # Sort the packages by name
        packages.sort(key=lambda p: p['name'])
        
        # Apply pagination
        start_index = (page - 1) * page_size
        end_index = start_index + page_size
        paginated_packages = packages[start_index:end_index]
        
        return {
            'packages': paginated_packages,
            'total': len(packages),
            'page': page,
            'page_size': page_size,
            'pages': (len(packages) + page_size - 1) // page_size
        }