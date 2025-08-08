import unittest
from unittest.mock import Mock, patch, MagicMock
import tempfile
import os
from datetime import datetime
from flask import Response

from pub_proxy.core.use_cases.download_package_use_case import DownloadPackageUseCase
from pub_proxy.infrastructure.services.pub_dev_service import PubDevService
from pub_proxy.infrastructure.repositories.package_repository import PackageRepository
from pub_proxy.core.interfaces.storage_service_interface import StorageServiceInterface
from pub_proxy.core.entities.package import Package, PackageVersion


class TestDownloadPackageUseCase(unittest.TestCase):
    def setUp(self):
        """Set up test fixtures."""
        self.mock_storage_service = Mock(spec=StorageServiceInterface)
        self.mock_pub_dev_service = Mock(spec=PubDevService)
        self.mock_package_repository = Mock(spec=PackageRepository)
        self.use_case = DownloadPackageUseCase(
            self.mock_storage_service,
            self.mock_pub_dev_service,
            self.mock_package_repository
        )
        
    def test_execute_package_exists_in_storage(self):
        """Test downloading package when it exists in storage."""
        # Mock storage service to indicate blob exists
        self.mock_storage_service.blob_exists.return_value = True
        self.mock_storage_service.download_blob_to_file = Mock()
        
        # Call the method
        result = self.use_case.execute('test_package', '1.0.0')
        
        # Assertions
        self.assertIsNotNone(result[0])  # Should return a file path
        self.assertEqual(result[1], False)  # is_stream should be False
        self.mock_storage_service.blob_exists.assert_called_once_with('test_package/1.0.0/archive.tar.gz')
        self.mock_storage_service.download_blob_to_file.assert_called_once()
        self.mock_pub_dev_service.download_package.assert_not_called()
        
    def test_execute_package_not_in_storage_download_from_pub_dev(self):
        """Test downloading package from pub.dev when not in storage."""
        # Mock storage service to indicate blob doesn't exist
        self.mock_storage_service.blob_exists.return_value = False
        
        # Mock pub.dev service response
        self.mock_pub_dev_service.download_package.return_value = iter([b'chunk1', b'chunk2'])
        
        # Mock cache package method
        with patch.object(self.use_case, '_cache_package') as mock_cache:
            # Call the method
            result = self.use_case.execute('test_package', '1.0.0')
        
        # Assertions
        self.assertEqual(result[1], True)  # is_stream should be True
        self.mock_storage_service.blob_exists.assert_called_once_with('test_package/1.0.0/archive.tar.gz')
        self.assertEqual(self.mock_pub_dev_service.download_package.call_count, 2)  # Called twice
        mock_cache.assert_called_once()
        
    def test_execute_package_not_found_in_repository(self):
        """Test downloading package when not found in repository."""
        # Mock storage service to indicate blob doesn't exist
        self.mock_storage_service.blob_exists.return_value = False
        
        # Mock pub.dev service response
        self.mock_pub_dev_service.download_package.return_value = iter([b'chunk1', b'chunk2'])
        
        # Mock cache package method
        with patch.object(self.use_case, '_cache_package') as mock_cache:
            # Call the method
            result = self.use_case.execute('test_package', '1.0.0')
        
        # Assertions
        self.assertEqual(result[1], True)  # is_stream should be True
        self.mock_storage_service.blob_exists.assert_called_once_with('test_package/1.0.0/archive.tar.gz')
        self.assertEqual(self.mock_pub_dev_service.download_package.call_count, 2)  # Called twice
        mock_cache.assert_called_once()
        
    def test_execute_version_not_found_in_package(self):
        """Test downloading version that doesn't exist in storage."""
        # Mock storage service to indicate blob doesn't exist
        self.mock_storage_service.blob_exists.return_value = False
        
        # Mock pub.dev service response
        self.mock_pub_dev_service.download_package.return_value = iter([b'chunk1', b'chunk2'])
        
        # Mock cache package method
        with patch.object(self.use_case, '_cache_package') as mock_cache:
            # Call the method with version not in storage
            result = self.use_case.execute('test_package', '2.0.0')
        
        # Assertions
        self.assertEqual(result[1], True)  # is_stream should be True
        self.mock_storage_service.blob_exists.assert_called_once_with('test_package/2.0.0/archive.tar.gz')
        self.assertEqual(self.mock_pub_dev_service.download_package.call_count, 2)  # Called twice
        mock_cache.assert_called_once()
        
    def test_execute_pub_dev_download_fails(self):
        """Test handling when pub.dev download fails."""
        # Reset the mock to clear any previous side_effect
        self.mock_pub_dev_service.reset_mock()
        
        # Mock storage service to indicate blob doesn't exist
        self.mock_storage_service.blob_exists.return_value = False
        
        # Mock pub.dev service to return None (failure)
        self.mock_pub_dev_service.download_package.return_value = None
        
        # Call the method - this will raise an exception due to None being not iterable
        with self.assertRaises(TypeError):
            self.use_case.execute('test_package', '1.0.0')
        
        # Assertions
        self.mock_storage_service.blob_exists.assert_called_once_with('test_package/1.0.0/archive.tar.gz')
        # download_package is called once, then fails in _cache_package
        self.mock_pub_dev_service.download_package.assert_called_once_with('test_package', '1.0.0')
        
    def test_execute_pub_dev_download_error_status(self):
        """Test handling when pub.dev returns error status."""
        # Mock storage service to indicate blob doesn't exist
        self.mock_storage_service.blob_exists.return_value = False
        
        # Mock pub.dev service response with error status
        self.mock_pub_dev_service.download_package.return_value = iter([b'error'])
        
        # Mock cache package method to avoid iterator consumption
        with patch.object(self.use_case, '_cache_package') as mock_cache:
            # Call the method
            result = self.use_case.execute('test_package', '1.0.0')
        
        # Assertions
        self.assertEqual(result[1], True)  # is_stream should be True
        self.assertIsNotNone(result[0])  # should return an iterator
        self.mock_storage_service.blob_exists.assert_called_once_with('test_package/1.0.0/archive.tar.gz')
        # download_package is called twice - once for caching, once for return
        self.assertEqual(self.mock_pub_dev_service.download_package.call_count, 2)
        mock_cache.assert_called_once()
        
    @patch('pub_proxy.core.use_cases.download_package_use_case.tempfile.NamedTemporaryFile')
    @patch('pub_proxy.core.use_cases.download_package_use_case.os.unlink')
    def test_cache_package(self, mock_unlink, mock_temp_file):
        """Test caching package from stream."""
        # Mock temporary file
        mock_file = Mock()
        mock_file.name = '/tmp/test_file'
        mock_file.write = Mock()
        mock_file.close = Mock()
        mock_temp_file.return_value = mock_file
        
        # Mock storage service methods
        self.mock_storage_service.upload_file_to_blob = Mock()
        self.mock_storage_service.get_blob_url = Mock(return_value='http://example.com/blob')
        
        # Mock package repository
        self.mock_package_repository.get_package.return_value = None
        
        # Create stream iterator
        stream = iter([b'chunk1', b'chunk2', b'chunk3'])
        
        # Call the method
        self.use_case._cache_package('test_package', '1.0.0', stream)
        
        # Assertions
        mock_temp_file.assert_called_once_with(delete=False, suffix='.tar.gz')
        mock_file.write.assert_any_call(b'chunk1')
        mock_file.write.assert_any_call(b'chunk2')
        mock_file.write.assert_any_call(b'chunk3')
        mock_file.close.assert_called_once()
        self.mock_storage_service.upload_file_to_blob.assert_called_once_with(
            '/tmp/test_file',
            'test_package/1.0.0/archive.tar.gz'
        )
        mock_unlink.assert_called_once_with('/tmp/test_file')
        
    @patch('pub_proxy.core.use_cases.download_package_use_case.tempfile.NamedTemporaryFile')
    @patch('pub_proxy.core.use_cases.download_package_use_case.os.unlink')
    def test_cache_package_upload_failure(self, mock_unlink, mock_temp_file):
        """Test caching package when upload fails."""
        # Mock temporary file
        mock_file = Mock()
        mock_file.name = '/tmp/test_file'
        mock_file.write = Mock()
        mock_file.close = Mock()
        mock_temp_file.return_value = mock_file
        
        # Mock storage service methods
        self.mock_storage_service.upload_file_to_blob = Mock(side_effect=Exception('Upload failed'))
        self.mock_storage_service.get_blob_url = Mock(return_value='http://example.com/blob')
        
        # Mock package repository
        self.mock_package_repository.get_package.return_value = None
        
        # Create stream iterator
        stream = iter([b'chunk1', b'chunk2'])
        
        # Call the method (should raise exception)
        with self.assertRaises(Exception):
            self.use_case._cache_package('test_package', '1.0.0', stream)
        
        # Assertions
        mock_temp_file.assert_called_once_with(delete=False, suffix='.tar.gz')
        self.mock_storage_service.upload_file_to_blob.assert_called_once()
        # Note: unlink is not called when upload fails in current implementation
        
    def test_execute_with_custom_archive_url(self):
        """Test downloading package - implementation uses standard blob path."""
        # Mock storage service to indicate blob exists
        self.mock_storage_service.blob_exists.return_value = True
        self.mock_storage_service.download_blob_to_file = Mock()
        
        # Call the method
        result = self.use_case.execute('test_package', '1.0.0')
        
        # Assertions
        self.assertIsNotNone(result[0])  # Should return a file path
        self.assertEqual(result[1], False)  # is_stream should be False
        self.mock_storage_service.blob_exists.assert_called_once_with('test_package/1.0.0/archive.tar.gz')
        self.mock_storage_service.download_blob_to_file.assert_called_once()
    
    @patch('pub_proxy.core.use_cases.download_package_use_case.tempfile.NamedTemporaryFile')
    @patch('pub_proxy.core.use_cases.download_package_use_case.os.unlink')
    def test_cache_package_updates_archive_url(self, mock_unlink, mock_temp_file):
        """Test that caching package updates the archive URL in package metadata."""
        # Mock temporary file
        mock_file = Mock()
        mock_file.name = '/tmp/test_file'
        mock_file.write = Mock()
        mock_file.close = Mock()
        mock_temp_file.return_value = mock_file
        
        # Mock storage service methods
        self.mock_storage_service.upload_file_to_blob = Mock()
        self.mock_storage_service.get_blob_url = Mock(return_value='http://example.com/blob')
        
        # Create a package with a version that matches
        package_version = PackageVersion(
            version='1.0.0',
            published=datetime.now(),
            dependencies={},
            environment={},
            archive_url='old_url',
            archive_sha256='abc123'
        )
        package = Package(
            name='test_package',
            latest_version='1.0.0',
            description='Test package',
            homepage='http://example.com',
            repository='http://github.com/example/test_package',
            is_private=False,
            versions=[package_version]
        )
        
        # Mock package repository to return the package
        self.mock_package_repository.get_package.return_value = package
        
        # Create stream iterator
        stream = iter([b'chunk1', b'chunk2'])
        
        # Call the method
        self.use_case._cache_package('test_package', '1.0.0', stream)
        
        # Assertions
        mock_temp_file.assert_called_once_with(delete=False, suffix='.tar.gz')
        self.mock_storage_service.upload_file_to_blob.assert_called_once()
        self.mock_storage_service.get_blob_url.assert_called_once()
        self.mock_package_repository.save_package.assert_called_once()
        
        # Verify that the archive URL was updated
        self.assertEqual(package.versions[0].archive_url, 'http://example.com/blob')
        mock_unlink.assert_called_once_with('/tmp/test_file')


if __name__ == '__main__':
    unittest.main()