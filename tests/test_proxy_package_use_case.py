import unittest
from unittest.mock import Mock, MagicMock
from datetime import datetime

from pub_proxy.core.use_cases.proxy_package_use_case import ProxyPackageUseCase
from pub_proxy.infrastructure.services.pub_dev_service import PubDevService
from pub_proxy.infrastructure.repositories.package_repository import PackageRepository
from pub_proxy.core.entities.package import Package, PackageVersion


class TestProxyPackageUseCase(unittest.TestCase):
    def setUp(self):
        """Set up test fixtures."""
        self.mock_pub_dev_service = Mock(spec=PubDevService)
        self.mock_package_repository = Mock(spec=PackageRepository)
        self.use_case = ProxyPackageUseCase(
            self.mock_pub_dev_service,
            self.mock_package_repository
        )
        
    def test_get_package_info_from_repository(self):
        """Test getting package info from repository when available."""
        # Create test package
        version = PackageVersion(
            version='1.0.0',
            archive_url='packages/test_package/versions/1.0.0.tar.gz',
            published=datetime(2023, 1, 1)
        )
        package = Package(
            name='test_package',
            latest_version='1.0.0',
            versions=[version]
        )
        
        # Mock repository to return package
        self.mock_package_repository.get_package.return_value = package
        
        # Call the method
        result = self.use_case.get_package_info('test_package')
        
        # Assertions
        self.assertIsNotNone(result)
        self.assertEqual(result['name'], 'test_package')
        self.assertEqual(result['latest']['version'], '1.0.0')
        self.mock_package_repository.get_package.assert_called_once_with('test_package')
        self.mock_pub_dev_service.get_package_info.assert_not_called()
        
    def test_get_package_info_from_pub_dev(self):
        """Test getting package info from pub.dev when not in repository."""
        # Mock repository to return None
        self.mock_package_repository.get_package.return_value = None
        
        # Mock pub.dev service response
        pub_dev_response = {
            'name': 'test_package',
            'latest': {'version': '1.0.0'},
            'versions': [
                {
                    'version': '1.0.0',
                    'pubspec': {'name': 'test_package', 'version': '1.0.0'},
                    'archive_url': 'http://example.com/test_package-1.0.0.tar.gz',
                    'published': '2023-01-01T00:00:00.000Z'
                }
            ]
        }
        self.mock_pub_dev_service.get_package_info.return_value = pub_dev_response
        
        # Call the method
        result = self.use_case.get_package_info('test_package')
        
        # Assertions
        self.assertIsNotNone(result)
        self.assertEqual(result['name'], 'test_package')
        self.mock_package_repository.get_package.assert_called_once_with('test_package')
        self.mock_pub_dev_service.get_package_info.assert_called_once_with('test_package')
        self.mock_package_repository.save_package_info.assert_called_once_with('test_package', pub_dev_response)
        
    def test_get_package_info_not_found(self):
        """Test getting package info when package doesn't exist."""
        # Mock repository to return None
        self.mock_package_repository.get_package.return_value = None
        
        # Mock pub.dev service to return None
        self.mock_pub_dev_service.get_package_info.return_value = None
        
        # Call the method
        result = self.use_case.get_package_info('non_existing_package')
        
        # Assertions
        self.assertIsNone(result)
        self.mock_package_repository.get_package.assert_called_once_with('non_existing_package')
        self.mock_pub_dev_service.get_package_info.assert_called_once_with('non_existing_package')
        self.mock_package_repository.save_package_info.assert_not_called()
        
    def test_get_package_version_from_repository(self):
        """Test getting package version from repository when available."""
        # Create test package with version
        version = PackageVersion(
            version='1.0.0',
            archive_url='packages/test_package/versions/1.0.0.tar.gz',
            published=datetime(2023, 1, 1)
        )
        package = Package(
            name='test_package',
            latest_version='1.0.0',
            versions=[version]
        )
        
        # Mock repository to return package
        self.mock_package_repository.get_package.return_value = package
        
        # Call the method
        result = self.use_case.get_package_version('test_package', '1.0.0')
        
        # Assertions
        self.assertIsNotNone(result)
        self.assertEqual(result['version'], '1.0.0')
        self.mock_package_repository.get_package.assert_called_once_with('test_package')
        self.mock_pub_dev_service.get_package_version.assert_not_called()
        
    def test_get_package_version_from_pub_dev(self):
        """Test getting package version from pub.dev when not in repository."""
        # Mock repository to return None
        self.mock_package_repository.get_package.return_value = None
        
        # Mock pub.dev service response
        pub_dev_response = {
            'version': '1.0.0',
            'pubspec': {'name': 'test_package', 'version': '1.0.0'},
            'archive_url': 'http://example.com/test_package-1.0.0.tar.gz',
            'published': '2023-01-01T00:00:00.000Z'
        }
        self.mock_pub_dev_service.get_package_version.return_value = pub_dev_response
        
        # Call the method
        result = self.use_case.get_package_version('test_package', '1.0.0')
        
        # Assertions
        self.assertIsNotNone(result)
        self.assertEqual(result['version'], '1.0.0')
        self.mock_package_repository.get_package.assert_called_once_with('test_package')
        self.mock_pub_dev_service.get_package_version.assert_called_once_with('test_package', '1.0.0')
        self.mock_package_repository.save_package_version.assert_called_once_with('test_package', '1.0.0', pub_dev_response)
        
    def test_get_package_version_not_found(self):
        """Test getting package version when version doesn't exist."""
        # Mock repository to return None
        self.mock_package_repository.get_package.return_value = None
        
        # Mock pub.dev service to return None
        self.mock_pub_dev_service.get_package_version.return_value = None
        
        # Call the method
        result = self.use_case.get_package_version('test_package', '999.0.0')
        
        # Assertions
        self.assertIsNone(result)
        self.mock_package_repository.get_package.assert_called_once_with('test_package')
        self.mock_pub_dev_service.get_package_version.assert_called_once_with('test_package', '999.0.0')
        self.mock_package_repository.save_package_version.assert_not_called()
        
    def test_get_package_version_not_in_package(self):
        """Test getting package version when package exists but version doesn't."""
        # Create test package without the requested version
        version = PackageVersion(
            version='1.0.0',
            archive_url='packages/test_package/versions/1.0.0.tar.gz',
            published=datetime(2023, 1, 1)
        )
        package = Package(
            name='test_package',
            latest_version='1.0.0',
            versions=[version]
        )
        
        # Mock repository to return package
        self.mock_package_repository.get_package.return_value = package
        
        # Mock pub.dev service response
        pub_dev_response = {
            'version': '2.0.0',
            'pubspec': {'name': 'test_package', 'version': '2.0.0'},
            'archive_url': 'http://example.com/test_package-2.0.0.tar.gz',
            'published': '2023-02-01T00:00:00.000Z'
        }
        self.mock_pub_dev_service.get_package_version.return_value = pub_dev_response
        
        # Call the method
        result = self.use_case.get_package_version('test_package', '2.0.0')
        
        # Assertions
        self.assertIsNotNone(result)
        self.assertEqual(result['version'], '2.0.0')
        self.mock_package_repository.get_package.assert_called_once_with('test_package')
        self.mock_pub_dev_service.get_package_version.assert_called_once_with('test_package', '2.0.0')
        self.mock_package_repository.save_package_version.assert_called_once_with('test_package', '2.0.0', pub_dev_response)
        
    def test_proxy_request(self):
        """Test proxying request to pub.dev."""
        # Mock pub.dev service response
        mock_response = Mock()
        mock_response.status_code = 200
        self.mock_pub_dev_service.proxy_request.return_value = mock_response
        
        # Call the method
        result = self.use_case.proxy_request('/api/packages/flutter', 'GET', {}, None)
        
        # Assertions
        self.assertEqual(result, mock_response)
        self.mock_pub_dev_service.proxy_request.assert_called_once_with('/api/packages/flutter', 'GET', {}, None)
        
    def test_package_to_dict(self):
        """Test converting package to dictionary."""
        # Create test package
        version1 = PackageVersion(
            version='1.0.0',
            archive_url='packages/test_package/versions/1.0.0.tar.gz',
            published=datetime(2023, 1, 1)
        )
        version2 = PackageVersion(
            version='2.0.0',
            archive_url='packages/test_package/versions/2.0.0.tar.gz',
            published=datetime(2023, 2, 1)
        )
        package = Package(
            name='test_package',
            latest_version='2.0.0',
            versions=[version1, version2]
        )
        
        # Call the method
        result = self.use_case._package_to_dict(package)
        
        # Assertions
        self.assertEqual(result['name'], 'test_package')
        self.assertEqual(result['latest']['version'], '2.0.0')
        self.assertEqual(len(result['versions']), 2)
        self.assertIn('1.0.0', [v['version'] for v in result['versions']])
        self.assertIn('2.0.0', [v['version'] for v in result['versions']])
        
    def test_version_to_dict(self):
        """Test converting version to dictionary."""
        # Create test version
        version = PackageVersion(
            version='1.0.0',
            archive_url='packages/test_package/versions/1.0.0.tar.gz',
            published=datetime(2023, 1, 1, 12, 0, 0)
        )
        
        # Call the method
        result = self.use_case._version_to_dict(version)
        
        # Assertions
        self.assertEqual(result['version'], '1.0.0')
        self.assertEqual(result['pubspec']['name'], 'test_package')
        self.assertEqual(result['archive_url'], 'http://example.com/test_package-1.0.0.tar.gz')
        self.assertEqual(result['published'], '2023-01-01T12:00:00.000Z')
        
    def test_package_to_dict_with_environment(self):
        """Test converting package to dictionary with environment field."""
        # Create test package with environment in pubspec
        version = PackageVersion(
            version='1.0.0',
            archive_url='packages/test_package/versions/1.0.0.tar.gz',
            published=datetime(2023, 1, 1)
        )
        package = Package(
            name='test_package',
            latest_version='1.0.0',
            versions=[version]
        )
        
        # Call the method
        result = self.use_case._package_to_dict(package)
        
        # Assertions
        self.assertEqual(result['name'], 'test_package')
        self.assertEqual(result['latest']['pubspec']['environment']['sdk'], '>=2.12.0 <4.0.0')
        
    def test_version_to_dict_with_environment(self):
        """Test converting version to dictionary with environment field."""
        # Create test version with environment in pubspec
        version = PackageVersion(
            version='1.0.0',
            archive_url='packages/test_package/versions/1.0.0.tar.gz',
            published=datetime(2023, 1, 1)
        )
        
        # Call the method
        result = self.use_case._version_to_dict(version)
        
        # Assertions
        self.assertEqual(result['version'], '1.0.0')
        self.assertEqual(result['pubspec']['environment']['sdk'], '>=2.12.0 <4.0.0')


if __name__ == '__main__':
    unittest.main()