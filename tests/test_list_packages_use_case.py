import unittest
from unittest.mock import Mock

from pub_proxy.core.use_cases.list_packages_use_case import ListPackagesUseCase
from pub_proxy.infrastructure.repositories.package_repository import PackageRepository
from pub_proxy.infrastructure.services.pub_dev_service import PubDevService


class TestListPackagesUseCase(unittest.TestCase):
    def setUp(self):
        """Set up test fixtures."""
        self.mock_package_repository = Mock(spec=PackageRepository)
        self.mock_pub_dev_service = Mock(spec=PubDevService)
        self.use_case = ListPackagesUseCase(
            self.mock_package_repository,
            self.mock_pub_dev_service
        )
        
    def test_execute_no_packages(self):
        """Test listing packages when no packages exist."""
        # Mock empty results
        self.mock_package_repository.list_packages.return_value = []
        self.mock_pub_dev_service.search_packages.return_value = {'packages': []}
        
        # Call the method
        result = self.use_case.execute()
        
        # Assertions
        expected = {
            'packages': [],
            'total': 0,
            'page': 1,
            'page_size': 10,
            'pages': 0
        }
        self.assertEqual(result, expected)
        self.mock_package_repository.list_packages.assert_called_once_with('')
        self.mock_pub_dev_service.search_packages.assert_called_once_with('', 1, 10)
        
    def test_execute_only_private_packages(self):
        """Test listing packages when only private packages exist."""
        # Mock private packages
        private_packages = [
            {'name': 'private_package_1', 'description': 'Private package 1'},
            {'name': 'private_package_2', 'description': 'Private package 2'}
        ]
        self.mock_package_repository.list_packages.return_value = private_packages
        self.mock_pub_dev_service.search_packages.return_value = {'packages': []}
        
        # Call the method
        result = self.use_case.execute()
        
        # Assertions
        expected = {
            'packages': private_packages,
            'total': 2,
            'page': 1,
            'page_size': 10,
            'pages': 1
        }
        self.assertEqual(result, expected)
        self.mock_package_repository.list_packages.assert_called_once_with('')
        self.mock_pub_dev_service.search_packages.assert_called_once_with('', 1, 10)
        
    def test_execute_only_pub_dev_packages(self):
        """Test listing packages when only pub.dev packages exist."""
        # Mock pub.dev packages
        pub_dev_packages = [
            {'name': 'flutter', 'description': 'Flutter SDK'},
            {'name': 'http', 'description': 'HTTP client'}
        ]
        self.mock_package_repository.list_packages.return_value = []
        self.mock_pub_dev_service.search_packages.return_value = {'packages': pub_dev_packages}
        
        # Call the method
        result = self.use_case.execute()
        
        # Assertions
        expected = {
            'packages': pub_dev_packages,
            'total': 2,
            'page': 1,
            'page_size': 10,
            'pages': 1
        }
        self.assertEqual(result, expected)
        self.mock_package_repository.list_packages.assert_called_once_with('')
        self.mock_pub_dev_service.search_packages.assert_called_once_with('', 1, 10)
        
    def test_execute_mixed_packages_no_overlap(self):
        """Test listing packages with both private and pub.dev packages, no overlap."""
        # Mock private packages
        private_packages = [
            {'name': 'private_package', 'description': 'Private package'}
        ]
        # Mock pub.dev packages
        pub_dev_packages = [
            {'name': 'flutter', 'description': 'Flutter SDK'},
            {'name': 'http', 'description': 'HTTP client'}
        ]
        
        self.mock_package_repository.list_packages.return_value = private_packages
        self.mock_pub_dev_service.search_packages.return_value = {'packages': pub_dev_packages}
        
        # Call the method
        result = self.use_case.execute()
        
        # Assertions - packages should be sorted by name
        expected_packages = [
            {'name': 'flutter', 'description': 'Flutter SDK'},
            {'name': 'http', 'description': 'HTTP client'},
            {'name': 'private_package', 'description': 'Private package'}
        ]
        expected = {
            'packages': expected_packages,
            'total': 3,
            'page': 1,
            'page_size': 10,
            'pages': 1
        }
        self.assertEqual(result, expected)
        
    def test_execute_mixed_packages_with_overlap(self):
        """Test listing packages with overlap between private and pub.dev packages."""
        # Mock private packages (should take priority)
        private_packages = [
            {'name': 'http', 'description': 'Private HTTP client', 'version': '2.0.0'},
            {'name': 'private_package', 'description': 'Private package'}
        ]
        # Mock pub.dev packages
        pub_dev_packages = [
            {'name': 'flutter', 'description': 'Flutter SDK'},
            {'name': 'http', 'description': 'Public HTTP client', 'version': '1.0.0'}
        ]
        
        self.mock_package_repository.list_packages.return_value = private_packages
        self.mock_pub_dev_service.search_packages.return_value = {'packages': pub_dev_packages}
        
        # Call the method
        result = self.use_case.execute()
        
        # Assertions - private package should take priority, sorted by name
        expected_packages = [
            {'name': 'flutter', 'description': 'Flutter SDK'},
            {'name': 'http', 'description': 'Private HTTP client', 'version': '2.0.0'},
            {'name': 'private_package', 'description': 'Private package'}
        ]
        expected = {
            'packages': expected_packages,
            'total': 3,
            'page': 1,
            'page_size': 10,
            'pages': 1
        }
        self.assertEqual(result, expected)
        
    def test_execute_with_query(self):
        """Test listing packages with a search query."""
        query = 'flutter'
        
        # Mock packages
        private_packages = [
            {'name': 'flutter_private', 'description': 'Private Flutter package'}
        ]
        pub_dev_packages = [
            {'name': 'flutter', 'description': 'Flutter SDK'}
        ]
        
        self.mock_package_repository.list_packages.return_value = private_packages
        self.mock_pub_dev_service.search_packages.return_value = {'packages': pub_dev_packages}
        
        # Call the method
        result = self.use_case.execute(query=query)
        
        # Assertions
        self.mock_package_repository.list_packages.assert_called_once_with(query)
        self.mock_pub_dev_service.search_packages.assert_called_once_with(query, 1, 10)
        self.assertEqual(len(result['packages']), 2)
        
    def test_execute_with_pagination_first_page(self):
        """Test listing packages with pagination - first page."""
        # Mock packages (more than page size)
        packages = [
            {'name': f'package_{i:02d}', 'description': f'Package {i}'}
            for i in range(15)
        ]
        
        self.mock_package_repository.list_packages.return_value = packages
        self.mock_pub_dev_service.search_packages.return_value = {'packages': []}
        
        # Call the method with page size 10
        result = self.use_case.execute(page=1, page_size=10)
        
        # Assertions
        self.assertEqual(len(result['packages']), 10)
        self.assertEqual(result['total'], 15)
        self.assertEqual(result['page'], 1)
        self.assertEqual(result['page_size'], 10)
        self.assertEqual(result['pages'], 2)
        self.assertEqual(result['packages'][0]['name'], 'package_00')
        self.assertEqual(result['packages'][9]['name'], 'package_09')
        
    def test_execute_with_pagination_second_page(self):
        """Test listing packages with pagination - second page."""
        # Mock packages (more than page size)
        packages = [
            {'name': f'package_{i:02d}', 'description': f'Package {i}'}
            for i in range(15)
        ]
        
        self.mock_package_repository.list_packages.return_value = packages
        self.mock_pub_dev_service.search_packages.return_value = {'packages': []}
        
        # Call the method with page size 10, page 2
        result = self.use_case.execute(page=2, page_size=10)
        
        # Assertions
        self.assertEqual(len(result['packages']), 5)  # Remaining packages
        self.assertEqual(result['total'], 15)
        self.assertEqual(result['page'], 2)
        self.assertEqual(result['page_size'], 10)
        self.assertEqual(result['pages'], 2)
        self.assertEqual(result['packages'][0]['name'], 'package_10')
        self.assertEqual(result['packages'][4]['name'], 'package_14')
        
    def test_execute_with_custom_page_size(self):
        """Test listing packages with custom page size."""
        # Mock packages
        packages = [
            {'name': f'package_{i}', 'description': f'Package {i}'}
            for i in range(7)
        ]
        
        self.mock_package_repository.list_packages.return_value = packages
        self.mock_pub_dev_service.search_packages.return_value = {'packages': []}
        
        # Call the method with page size 3
        result = self.use_case.execute(page_size=3)
        
        # Assertions
        self.assertEqual(len(result['packages']), 3)
        self.assertEqual(result['total'], 7)
        self.assertEqual(result['page_size'], 3)
        self.assertEqual(result['pages'], 3)  # ceil(7/3) = 3
        
    def test_execute_empty_page(self):
        """Test listing packages when requesting a page beyond available data."""
        # Mock packages
        packages = [
            {'name': 'package_1', 'description': 'Package 1'}
        ]
        
        self.mock_package_repository.list_packages.return_value = packages
        self.mock_pub_dev_service.search_packages.return_value = {'packages': []}
        
        # Call the method with page 5 (beyond available data)
        result = self.use_case.execute(page=5, page_size=10)
        
        # Assertions
        self.assertEqual(len(result['packages']), 0)
        self.assertEqual(result['total'], 1)
        self.assertEqual(result['page'], 5)
        self.assertEqual(result['pages'], 1)
        
    def test_execute_pub_dev_service_returns_none(self):
        """Test listing packages when pub.dev service returns None."""
        # Mock private packages
        private_packages = [
            {'name': 'private_package', 'description': 'Private package'}
        ]
        
        self.mock_package_repository.list_packages.return_value = private_packages
        self.mock_pub_dev_service.search_packages.return_value = None
        
        # Call the method
        result = self.use_case.execute()
        
        # Assertions - should handle None gracefully
        expected = {
            'packages': private_packages,
            'total': 1,
            'page': 1,
            'page_size': 10,
            'pages': 1
        }
        self.assertEqual(result, expected)
        
    def test_execute_sorting_behavior(self):
        """Test that packages are correctly sorted by name."""
        # Mock packages in non-alphabetical order
        private_packages = [
            {'name': 'zebra_package', 'description': 'Zebra package'}
        ]
        pub_dev_packages = [
            {'name': 'alpha_package', 'description': 'Alpha package'},
            {'name': 'beta_package', 'description': 'Beta package'}
        ]
        
        self.mock_package_repository.list_packages.return_value = private_packages
        self.mock_pub_dev_service.search_packages.return_value = {'packages': pub_dev_packages}
        
        # Call the method
        result = self.use_case.execute()
        
        # Assertions - should be sorted alphabetically
        package_names = [p['name'] for p in result['packages']]
        self.assertEqual(package_names, ['alpha_package', 'beta_package', 'zebra_package'])


if __name__ == '__main__':
    unittest.main()