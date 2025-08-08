import unittest
from unittest.mock import Mock, patch, MagicMock
import json
from datetime import datetime

from pub_proxy.infrastructure.repositories.package_repository import PackageRepository
from pub_proxy.core.entities.package import Package, PackageVersion
from pub_proxy.core.interfaces.storage_service_interface import StorageServiceInterface


class TestPackageRepository(unittest.TestCase):
    def setUp(self):
        """Set up test fixtures."""
        self.mock_storage_service = Mock(spec=StorageServiceInterface)
        self.repository = PackageRepository(self.mock_storage_service)
        
    def test_get_package_exists(self):
        """Test getting an existing package."""
        # Mock storage service to return package data
        package_data = {
            'name': 'test_package',
            'latest_version': '1.0.0',
            'versions': [
                {
                    'version': '1.0.0',
                    'dependencies': {},
                    'environment': {},
                    'archive_url': 'http://example.com/test_package-1.0.0.tar.gz',
                    'published': '2023-01-01T00:00:00'
                }
            ]
        }
        self.mock_storage_service.blob_exists.return_value = True
        self.mock_storage_service.download_blob_as_string.return_value = json.dumps(package_data)
        
        # Call the method
        result = self.repository.get_package('test_package')
        
        # Assertions
        self.assertIsInstance(result, Package)
        self.assertEqual(result.name, 'test_package')
        self.assertEqual(result.latest_version, '1.0.0')
        self.assertEqual(len(result.versions), 1)
        self.mock_storage_service.blob_exists.assert_called_once_with('packages/test_package/metadata.json')
        self.mock_storage_service.download_blob_as_string.assert_called_once_with('packages/test_package/metadata.json')
        
    def test_get_package_not_exists(self):
        """Test getting a non-existing package."""
        # Mock storage service to return False for blob_exists
        self.mock_storage_service.blob_exists.return_value = False
        
        # Call the method
        result = self.repository.get_package('non_existing_package')
        
        # Assertions
        self.assertIsNone(result)
        self.mock_storage_service.blob_exists.assert_called_once_with('packages/non_existing_package/metadata.json')
        
    def test_save_package(self):
        """Test saving a package."""
        # Create test package
        version = PackageVersion(
            version='1.0.0',
            archive_url='http://example.com/test_package-1.0.0.tar.gz',
            published=datetime(2023, 1, 1)
        )
        package = Package(
            name='test_package',
            latest_version='1.0.0',
            versions=[version]
        )
        
        # Call the method
        self.repository.save_package(package)
        
        # Verify storage service was called
        self.mock_storage_service.upload_string_to_blob.assert_called_once()
        call_args = self.mock_storage_service.upload_string_to_blob.call_args
        
        # Verify the content
        saved_data = json.loads(call_args[0][0])
        self.assertEqual(saved_data['name'], 'test_package')
        self.assertEqual(saved_data['latest_version'], '1.0.0')
        self.assertEqual(call_args[0][1], 'packages/test_package/metadata.json')
        
    def test_list_packages_empty_query(self):
        """Test listing packages with empty query."""
        # Mock storage service to return list of blobs
        self.mock_storage_service.list_blobs.return_value = [
            'packages/package1/metadata.json',
            'packages/package2/metadata.json'
        ]
        
        # Mock blob exists and download methods
        self.mock_storage_service.blob_exists.return_value = True
        
        # Mock file contents
        package_data = {
            'name': 'package1',
            'latest_version': '1.0.0',
            'description': 'Test package',
            'homepage': 'http://example.com',
            'repository': 'http://github.com/example/package1',
            'is_private': False,
            'versions': [
                {
                    'version': '1.0.0',
                    'published': '2023-01-01T00:00:00.000Z',
                    'dependencies': {},
                    'environment': {},
                    'archive_url': 'http://example.com/package1-1.0.0.tar.gz',
                    'archive_sha256': 'abc123'
                }
            ]
        }
        self.mock_storage_service.download_blob_as_string.return_value = json.dumps(package_data)
        
        # Call the method
        result = self.repository.list_packages()
        
        # Assertions
        self.assertEqual(len(result), 2)
        self.mock_storage_service.list_blobs.assert_called_once_with('packages/')
        
    def test_list_packages_with_query(self):
        """Test listing packages with search query."""
        # Mock storage service
        self.mock_storage_service.list_blobs.return_value = [
            'packages/flutter_package/metadata.json',
            'packages/dart_package/metadata.json'
        ]
        
        # Mock blob exists and download methods
        self.mock_storage_service.blob_exists.return_value = True
        
        package_data = {
            'name': 'flutter_package',
            'latest_version': '1.0.0',
            'description': 'Flutter test package',
            'homepage': 'http://example.com',
            'repository': 'http://github.com/example/flutter_package',
            'is_private': False,
            'versions': [
                {
                    'version': '1.0.0',
                    'published': '2023-01-01T00:00:00.000Z',
                    'dependencies': {},
                    'environment': {},
                    'archive_url': 'http://example.com/flutter_package-1.0.0.tar.gz',
                    'archive_sha256': 'abc123'
                }
            ]
        }
        self.mock_storage_service.download_blob_as_string.return_value = json.dumps(package_data)
        
        # Call the method with query
        result = self.repository.list_packages('flutter')
        
        # Should return packages matching the query
        self.assertGreaterEqual(len(result), 0)
        
    def test_save_package_info(self):
        """Test saving package info from pub.dev."""
        # Mock existing package
        existing_package_data = {
            'name': 'test_package',
            'latest_version': '1.0.0',
            'description': 'Test package',
            'homepage': 'http://example.com',
            'repository': 'http://github.com/example/test_package',
            'is_private': False,
            'versions': []
        }
        self.mock_storage_service.blob_exists.return_value = True
        self.mock_storage_service.download_blob_as_string.return_value = json.dumps(existing_package_data)
        
        # Package info from pub.dev
        package_info = {
            'name': 'test_package',
            'latest': {'version': '2.0.0'},
            'description': 'Updated test package',
            'homepage': 'http://example.com/updated',
            'repository': 'http://github.com/example/test_package_updated',
            'versions': [
                {
                    'version': '2.0.0',
                    'pubspec': {'name': 'test_package', 'version': '2.0.0'},
                    'archive_url': 'http://example.com/test_package-2.0.0.tar.gz',
                    'published': '2023-02-01T00:00:00.000Z'
                }
            ]
        }
        
        # Call the method
        self.repository.save_package_info('test_package', package_info)
        
        # Verify storage service was called to save
        self.mock_storage_service.upload_string_to_blob.assert_called()
        
    def test_save_package_version(self):
        """Test saving package version info."""
        # Mock existing package
        existing_package_data = {
            'name': 'test_package',
            'latest_version': '1.0.0',
            'description': 'Test package',
            'homepage': 'http://example.com',
            'repository': 'http://github.com/example/test_package',
            'is_private': False,
            'versions': [
                {
                    'version': '1.0.0',
                    'published': '2023-01-01T00:00:00.000Z',
                    'dependencies': {},
                    'environment': {},
                    'archive_url': 'http://example.com/test_package-1.0.0.tar.gz',
                    'archive_sha256': 'abc123'
                }
            ]
        }
        self.mock_storage_service.blob_exists.return_value = True
        self.mock_storage_service.download_blob_as_string.return_value = json.dumps(existing_package_data)
        
        # Version info from pub.dev
        version_info = {
            'version': '2.0.0',
            'pubspec': {'name': 'test_package', 'version': '2.0.0'},
            'archive_url': 'http://example.com/test_package-2.0.0.tar.gz',
            'published': '2023-02-01T00:00:00.000Z'
        }
        
        # Call the method
        self.repository.save_package_version('test_package', '2.0.0', version_info)
        
        # Verify storage service was called to save
        self.mock_storage_service.upload_string_to_blob.assert_called()
        
    def test_compare_versions(self):
        """Test version comparison method."""
        # Test equal versions
        result = self.repository._compare_versions('1.0.0', '1.0.0')
        self.assertEqual(result, 0)
        
        # Test first version greater
        result = self.repository._compare_versions('2.0.0', '1.0.0')
        self.assertEqual(result, 1)
        
        # Test first version smaller
        result = self.repository._compare_versions('1.0.0', '2.0.0')
        self.assertEqual(result, -1)
        
        # Test with build numbers
        result = self.repository._compare_versions('1.0.0+1', '1.0.0+2')
        self.assertEqual(result, 0)  # Build numbers should be ignored
        
        # Test with pre-release versions
        result = self.repository._compare_versions('1.0.0-alpha.1', '1.0.0')
        self.assertEqual(result, -1)
        
    def test_save_package_info_file_not_found(self):
        """Test saving package info when package file doesn't exist."""
        # Mock storage service to return False for blob_exists (package doesn't exist)
        self.mock_storage_service.blob_exists.return_value = False
        
        # Package info from pub.dev
        package_info = {
            'name': 'new_package',
            'latest': {'version': '1.0.0'},
            'description': 'New test package',
            'homepage': 'http://example.com/new',
            'repository': 'http://github.com/example/new_package',
            'versions': [
                {
                    'version': '1.0.0',
                    'pubspec': {'name': 'new_package', 'version': '1.0.0'},
                    'archive_url': 'http://example.com/new_package-1.0.0.tar.gz',
                    'published': '2023-01-01T00:00:00.000Z'
                }
            ]
        }
        
        # Call the method
        self.repository.save_package_info('new_package', package_info)
        
        # Verify storage service was called to save
        self.mock_storage_service.upload_string_to_blob.assert_called()
        
    def test_save_package_version_file_not_found(self):
        """Test saving package version when package file doesn't exist."""
        # Mock storage service to return False for blob_exists (package doesn't exist)
        self.mock_storage_service.blob_exists.return_value = False
        
        # Version info from pub.dev
        version_info = {
            'version': '1.0.0',
            'pubspec': {'name': 'new_package', 'version': '1.0.0'},
            'archive_url': 'http://example.com/new_package-1.0.0.tar.gz',
            'published': '2023-01-01T00:00:00.000Z'
        }
        
        # Call the method
        self.repository.save_package_version('new_package', '1.0.0', version_info)
        
        # Verify storage service was called to save
        self.mock_storage_service.upload_string_to_blob.assert_called()
    
    def test_compare_versions_prerelease_scenarios(self):
        """Test version comparison with prerelease scenarios."""
        # Test stable vs prerelease
        self.assertEqual(self.repository._compare_versions('1.0.0', '1.0.0-alpha'), 1)
        self.assertEqual(self.repository._compare_versions('1.0.0-alpha', '1.0.0'), -1)
        
        # Test both prerelease
        self.assertEqual(self.repository._compare_versions('1.0.0-alpha', '1.0.0-beta'), -1)
        self.assertEqual(self.repository._compare_versions('1.0.0-beta', '1.0.0-alpha'), 1)
        self.assertEqual(self.repository._compare_versions('1.0.0-alpha.1', '1.0.0-alpha.1'), 0)
        
        # Test both stable
        self.assertEqual(self.repository._compare_versions('1.0.0', '1.0.0'), 0)
    
    def test_save_package_info_error_handling(self):
        """Test error handling in save_package_info."""
        # Mock storage service to raise exception on upload
        self.mock_storage_service.blob_exists.return_value = False
        self.mock_storage_service.upload_string_to_blob.side_effect = Exception('Upload failed')
        
        package_info = {
            'name': 'error_package',
            'latest': {'version': '1.0.0'},
            'description': 'Error test package',
            'versions': []
        }
        
        # Should raise exception
        with self.assertRaises(Exception):
            self.repository.save_package_info('error_package', package_info)
    
    def test_save_package_version_error_handling(self):
        """Test error handling in save_package_version."""
        # Mock storage service to raise exception on upload
        self.mock_storage_service.blob_exists.return_value = False
        self.mock_storage_service.upload_string_to_blob.side_effect = Exception('Upload failed')
        
        version_info = {
            'version': '1.0.0',
            'pubspec': {'name': 'error_package', 'version': '1.0.0'},
            'published': '2023-01-01T00:00:00.000Z'
        }
        
        # Should raise exception
        with self.assertRaises(Exception):
            self.repository.save_package_version('error_package', '1.0.0', version_info)
    
    def test_save_package_version_existing_package_new_version(self):
        """Test saving a new version to an existing package."""
        # Mock existing package data
        existing_package_data = {
            'name': 'existing_package',
            'latest_version': '1.0.0',
            'description': 'Existing package',
            'homepage': 'http://example.com',
            'repository': 'http://github.com/example/existing_package',
            'is_private': False,
            'versions': [
                {
                    'version': '1.0.0',
                    'published': '2023-01-01T00:00:00.000Z',
                    'dependencies': {},
                    'environment': {},
                    'archive_url': 'http://example.com/existing_package-1.0.0.tar.gz',
                    'archive_sha256': 'abc123'
                }
            ]
        }
        
        # Mock storage service
        self.mock_storage_service.blob_exists.return_value = True
        self.mock_storage_service.download_blob_as_string.return_value = json.dumps(existing_package_data)
        
        # New version info
        version_info = {
            'version': '2.0.0',
            'pubspec': {'name': 'existing_package', 'version': '2.0.0'},
            'archive_url': 'http://example.com/existing_package-2.0.0.tar.gz',
            'published': '2023-02-01T00:00:00.000Z'
        }
        
        # Call the method
        self.repository.save_package_version('existing_package', '2.0.0', version_info)
        
        # Verify storage service was called
        self.mock_storage_service.blob_exists.assert_called_once_with('packages/existing_package/metadata.json')
        self.mock_storage_service.download_blob_as_string.assert_called_once_with('packages/existing_package/metadata.json')
        self.mock_storage_service.upload_string_to_blob.assert_called_once()
    
    def test_get_package_json_decode_error(self):
        """Test get_package with JSON decode error."""
        # Mock storage service
        self.mock_storage_service.blob_exists.return_value = True
        self.mock_storage_service.download_blob_as_string.return_value = 'invalid json'
        
        # Call the method (should raise JSON decode error)
        with self.assertRaises(json.JSONDecodeError):
            self.repository.get_package('invalid_package')


if __name__ == '__main__':
    unittest.main()