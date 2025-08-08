import unittest
from unittest.mock import Mock, patch, mock_open, MagicMock
import tempfile
import os
from datetime import datetime
from io import BytesIO

from pub_proxy.core.use_cases.upload_package_use_case import UploadPackageUseCase
from pub_proxy.infrastructure.repositories.package_repository import PackageRepository
from pub_proxy.core.interfaces.storage_service_interface import StorageServiceInterface
from pub_proxy.core.entities.package import Package, PackageVersion


class TestUploadPackageUseCase(unittest.TestCase):
    def setUp(self):
        """Set up test fixtures."""
        self.mock_storage_service = Mock(spec=StorageServiceInterface)
        self.mock_package_repository = Mock(spec=PackageRepository)
        self.use_case = UploadPackageUseCase(
            self.mock_storage_service,
            self.mock_package_repository
        )
        
    @patch('pub_proxy.core.use_cases.upload_package_use_case.tempfile.NamedTemporaryFile')
    @patch('pub_proxy.core.use_cases.upload_package_use_case.datetime')
    def test_execute_new_package(self, mock_datetime, mock_temp_file):
        """Test uploading a new package."""
        # Mock datetime
        mock_datetime.now.return_value = datetime(2023, 1, 1, 12, 0, 0)
        mock_datetime.side_effect = lambda *args, **kw: datetime(*args, **kw)
        
        # Mock temporary file
        mock_file = Mock()
        mock_file.name = '/tmp/test_file'
        mock_temp_file.return_value = mock_file
        
        # Create mock file object with save method
        file_object = Mock()
        file_object.filename = 'test_package-1.0.0.tar.gz'
        
        def mock_save(path):
            # Create the file so _calculate_sha256 can read it
            with open(path, 'wb') as f:
                f.write(b'test content')
        
        file_object.save = Mock(side_effect=mock_save)
        
        # Mock repository to return None (new package)
        self.mock_package_repository.get_package.return_value = None
        
        # Mock SHA256 calculation
        with patch.object(self.use_case, '_calculate_sha256', return_value='test_sha256'):
            # Call the method
            result = self.use_case.execute('test_package', '1.0.0', file_object)
        
        # Assertions
        self.assertTrue(result['success'])
        self.assertEqual(result['package'], 'test_package')
        self.assertEqual(result['version'], '1.0.0')
        self.mock_package_repository.get_package.assert_called_once_with('test_package')
        self.mock_storage_service.upload_file_to_blob.assert_called_once()
        self.mock_package_repository.save_package.assert_called_once()
        
    @patch('pub_proxy.core.use_cases.upload_package_use_case.tempfile.NamedTemporaryFile')
    @patch('pub_proxy.core.use_cases.upload_package_use_case.datetime')
    def test_execute_existing_package_new_version(self, mock_datetime, mock_temp_file):
        """Test uploading a new version to an existing package."""
        # Mock datetime
        mock_datetime.now.return_value = datetime(2023, 1, 1, 12, 0, 0)
        mock_datetime.side_effect = lambda *args, **kw: datetime(*args, **kw)
        
        # Mock temporary file
        mock_file = Mock()
        mock_file.name = '/tmp/test_file'
        mock_temp_file.return_value = mock_file
        
        # Create existing package
        existing_version = PackageVersion(
            version='1.0.0',
            archive_url='packages/test_package/versions/1.0.0.tar.gz',
            published=datetime(2023, 1, 1)
        )
        existing_package = Package(
            name='test_package',
            latest_version='1.0.0',
            versions=[existing_version]
        )
        
        # Mock repository to return existing package
        self.mock_package_repository.get_package.return_value = existing_package
        
        # Create mock file object with save method
        file_object = Mock()
        file_object.filename = 'test_package-2.0.0.tar.gz'
        
        def mock_save(path):
            # Create the file so _calculate_sha256 can read it
            with open(path, 'wb') as f:
                f.write(b'test content')
        
        file_object.save = Mock(side_effect=mock_save)
        
        # Mock SHA256 calculation
        with patch.object(self.use_case, '_calculate_sha256', return_value='test_sha256'):
            # Call the method
            result = self.use_case.execute('test_package', '2.0.0', file_object)
        
        # Assertions
        self.assertTrue(result['success'])
        self.assertEqual(result['package'], 'test_package')
        self.assertEqual(result['version'], '2.0.0')
        self.mock_package_repository.get_package.assert_called_once_with('test_package')
        self.mock_storage_service.upload_file_to_blob.assert_called_once()
        self.mock_package_repository.save_package.assert_called_once()
        
    @patch('pub_proxy.core.use_cases.upload_package_use_case.tempfile.NamedTemporaryFile')
    def test_execute_version_already_exists(self, mock_temp_file):
        """Test uploading a version that already exists."""
        # Mock temporary file
        mock_file = Mock()
        mock_file.name = '/tmp/test_file'
        mock_temp_file.return_value = mock_file
        
        # Create existing package with the same version
        existing_version = PackageVersion(
            version='1.0.0',
            archive_url='packages/test_package/versions/1.0.0.tar.gz',
            published=datetime(2023, 1, 1)
        )
        existing_package = Package(
            name='test_package',
            latest_version='1.0.0',
            versions=[existing_version]
        )
        
        # Mock repository to return existing package
        self.mock_package_repository.get_package.return_value = existing_package
        
        # Create mock file object with save method
        file_object = Mock()
        file_object.filename = 'test_package-1.0.0.tar.gz'
        
        def mock_save(path):
            # Create the file so _calculate_sha256 can read it
            with open(path, 'wb') as f:
                f.write(b'test content')
        
        file_object.save = Mock(side_effect=mock_save)
        
        # Mock SHA256 calculation
        with patch.object(self.use_case, '_calculate_sha256', return_value='test_sha256'):
            # Call the method
            result = self.use_case.execute('test_package', '1.0.0', file_object)
        
        # Assertions - the implementation updates existing versions
        self.assertTrue(result['success'])
        self.assertEqual(result['package'], 'test_package')
        self.assertEqual(result['version'], '1.0.0')
        self.mock_package_repository.get_package.assert_called_once_with('test_package')
        self.mock_storage_service.upload_file_to_blob.assert_called_once()
        self.mock_package_repository.save_package.assert_called_once()
        
    @patch('pub_proxy.core.use_cases.upload_package_use_case.tempfile.NamedTemporaryFile')
    def test_execute_upload_failure(self, mock_temp_file):
        """Test handling upload failure."""
        # Mock temporary file
        mock_file = Mock()
        mock_file.name = '/tmp/test_file'
        mock_temp_file.return_value = mock_file
        
        # Mock repository to return None (new package)
        self.mock_package_repository.get_package.return_value = None
        
        # Mock storage service to raise exception
        self.mock_storage_service.upload_file_to_blob = Mock(side_effect=Exception('Upload failed'))
        
        # Create mock file object with save method
        file_object = Mock()
        file_object.filename = 'test_package-1.0.0.tar.gz'
        
        def mock_save(path):
            # Create the file so _calculate_sha256 can read it
            with open(path, 'wb') as f:
                f.write(b'test content')
        
        file_object.save = Mock(side_effect=mock_save)
        
        # Mock SHA256 calculation
        with patch.object(self.use_case, '_calculate_sha256', return_value='test_sha256'):
            # Call the method and expect exception
            with self.assertRaises(Exception) as context:
                self.use_case.execute('test_package', '1.0.0', file_object)
        
        # Assertions
        self.assertIn('Upload failed', str(context.exception))
        self.mock_package_repository.save_package.assert_not_called()
        
    @patch('builtins.open', new_callable=mock_open, read_data=b'test content')
    @patch('pub_proxy.core.use_cases.upload_package_use_case.hashlib.sha256')
    def test_calculate_sha256(self, mock_sha256, mock_file):
        """Test SHA256 calculation."""
        # Mock hashlib
        mock_hash = Mock()
        mock_hash.hexdigest.return_value = 'test_hash'
        mock_sha256.return_value = mock_hash
        
        # Call the method
        result = self.use_case._calculate_sha256('/tmp/test_file')
        
        # Assertions
        self.assertEqual(result, 'test_hash')
        mock_file.assert_called_once_with('/tmp/test_file', 'rb')
        mock_hash.update.assert_called_once_with(b'test content')
        
    def test_compare_versions_equal(self):
        """Test version comparison for equal versions."""
        result = self.use_case._compare_versions('1.0.0', '1.0.0')
        self.assertEqual(result, 0)
        
    def test_compare_versions_first_greater(self):
        """Test version comparison when first version is greater."""
        result = self.use_case._compare_versions('2.0.0', '1.0.0')
        self.assertEqual(result, 1)
        
    def test_compare_versions_first_smaller(self):
        """Test version comparison when first version is smaller."""
        result = self.use_case._compare_versions('1.0.0', '2.0.0')
        self.assertEqual(result, -1)
        
    def test_compare_versions_with_build_numbers(self):
        """Test version comparison with build numbers."""
        result = self.use_case._compare_versions('1.0.0+1', '1.0.0+2')
        self.assertEqual(result, 0)  # Build numbers should be ignored
        
    def test_compare_versions_with_pre_release(self):
        """Test version comparison with pre-release versions."""
        result = self.use_case._compare_versions('1.0.0-alpha.1', '1.0.0')
        self.assertEqual(result, -1)
        
        result = self.use_case._compare_versions('1.0.0', '1.0.0-alpha.1')
        self.assertEqual(result, 1)
        
    def test_compare_versions_complex(self):
        """Test version comparison with complex version strings."""
        # Test different scenarios
        self.assertEqual(self.use_case._compare_versions('1.2.3', '1.2.4'), -1)
        self.assertEqual(self.use_case._compare_versions('1.3.0', '1.2.9'), 1)
        self.assertEqual(self.use_case._compare_versions('2.0.0', '1.9.9'), 1)
        self.assertEqual(self.use_case._compare_versions('1.0.0-beta.1', '1.0.0-alpha.1'), 1)
        
        result = self.use_case._compare_versions('1.0.0+build.1', '1.0.0+build.2')
        self.assertEqual(result, 0)  # Build metadata should be ignored
    
    def test_compare_versions_prerelease_vs_release(self):
        """Test version comparison between prerelease and release versions."""
        # Prerelease vs release (prerelease should be smaller)
        self.assertEqual(self.use_case._compare_versions('1.0.0-alpha', '1.0.0'), -1)
        self.assertEqual(self.use_case._compare_versions('1.0.0', '1.0.0-alpha'), 1)
        
    def test_compare_versions_prerelease_lexicographic(self):
        """Test lexicographic comparison of prerelease versions."""
        # Both are prereleases, compare lexicographically
        self.assertEqual(self.use_case._compare_versions('1.0.0-alpha', '1.0.0-beta'), -1)
        self.assertEqual(self.use_case._compare_versions('1.0.0-beta', '1.0.0-alpha'), 1)
        self.assertEqual(self.use_case._compare_versions('1.0.0-alpha.1', '1.0.0-alpha.1'), 0)
        
    def test_compare_versions_prerelease_equal(self):
        """Test comparison of equal prerelease versions."""
        # Test equal prerelease versions (covers line 193)
        result = self.use_case._compare_versions('1.0.0-alpha', '1.0.0-alpha')
        self.assertEqual(result, 0)  # alpha == alpha
        
        result = self.use_case._compare_versions('1.0.0-beta.1', '1.0.0-beta.1')
        self.assertEqual(result, 0)  # beta.1 == beta.1
        
    @patch('pub_proxy.core.use_cases.upload_package_use_case.tempfile.NamedTemporaryFile')
    @patch('pub_proxy.core.use_cases.upload_package_use_case.datetime')
    def test_execute_updates_latest_version(self, mock_datetime, mock_temp_file):
        """Test that uploading a newer version updates the latest version."""
        # Mock datetime
        mock_datetime.now.return_value = datetime(2023, 1, 1, 12, 0, 0)
        mock_datetime.side_effect = lambda *args, **kw: datetime(*args, **kw)
        
        # Mock temporary file
        mock_file = Mock()
        mock_file.name = '/tmp/test_file'
        mock_temp_file.return_value = mock_file
        
        # Create existing package with older version
        existing_version = PackageVersion(
            version='1.0.0',
            archive_url='packages/test_package/versions/1.0.0.tar.gz',
            published=datetime(2023, 1, 1)
        )
        existing_package = Package(
            name='test_package',
            latest_version='1.0.0',
            versions=[existing_version]
        )
        
        # Mock repository to return existing package
        self.mock_package_repository.get_package.return_value = existing_package
        
        # Create mock file object with save method
        file_object = Mock()
        file_object.filename = 'test_package-2.0.0.tar.gz'
        
        def mock_save(path):
            # Create the file so _calculate_sha256 can read it
            with open(path, 'wb') as f:
                f.write(b'test content')
        
        file_object.save = Mock(side_effect=mock_save)
        
        # Mock SHA256 calculation
        with patch.object(self.use_case, '_calculate_sha256', return_value='test_sha256_v2'):
            # Call the method with a newer version
            result = self.use_case.execute('test_package', '2.0.0', file_object)
        
        # Verify that save_package was called
        self.mock_package_repository.save_package.assert_called_once()
        
        # Get the package that was saved
        saved_package = self.mock_package_repository.save_package.call_args[0][0]
        
        # Verify the latest version was updated
        self.assertEqual(saved_package.latest_version, '2.0.0')
        self.assertTrue(any(v.version == '2.0.0' for v in saved_package.versions))
        
    @patch('pub_proxy.core.use_cases.upload_package_use_case.tempfile.NamedTemporaryFile')
    @patch('pub_proxy.core.use_cases.upload_package_use_case.datetime')
    def test_execute_does_not_update_latest_for_older_version(self, mock_datetime, mock_temp_file):
        """Test that uploading an older version doesn't update the latest version."""
        # Mock datetime
        mock_datetime.now.return_value = datetime(2023, 1, 1, 12, 0, 0)
        mock_datetime.side_effect = lambda *args, **kw: datetime(*args, **kw)
        
        # Mock temporary file
        mock_file = Mock()
        mock_file.name = '/tmp/test_file'
        mock_temp_file.return_value = mock_file
        
        # Create existing package with newer version
        existing_version = PackageVersion(
            version='2.0.0',
            archive_url='packages/test_package/versions/2.0.0.tar.gz',
            published=datetime(2023, 1, 1)
        )
        existing_package = Package(
            name='test_package',
            latest_version='2.0.0',
            versions=[existing_version]
        )
        
        # Mock repository to return existing package
        self.mock_package_repository.get_package.return_value = existing_package
        
        # Create mock file object with save method
        file_object = Mock()
        file_object.filename = 'test_package-2.0.0.tar.gz'
        
        def mock_save(path):
            # Create the file so _calculate_sha256 can read it
            with open(path, 'wb') as f:
                f.write(b'test content')
        
        file_object.save = Mock(side_effect=mock_save)
        
        # Mock SHA256 calculation
        with patch.object(self.use_case, '_calculate_sha256', return_value='test_sha256_v1'):
            # Call the method with an older version
            result = self.use_case.execute('test_package', '1.0.0', file_object)
        
        # Verify that save_package was called
        self.mock_package_repository.save_package.assert_called_once()
        
        # Get the package that was saved
        saved_package = self.mock_package_repository.save_package.call_args[0][0]
        
        # Verify the latest version was not updated
        self.assertEqual(saved_package.latest_version, '2.0.0')
        self.assertTrue(any(v.version == '1.0.0' for v in saved_package.versions))


if __name__ == '__main__':
    unittest.main()