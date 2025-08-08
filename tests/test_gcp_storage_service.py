import os
import tempfile
import unittest
from unittest.mock import MagicMock, patch

from pub_proxy.infrastructure.services.gcp_storage_service import GCPStorageService


class TestGCPStorageService(unittest.TestCase):
    """Test cases for the GCPStorageService class."""

    def setUp(self):
        """Set up the test environment."""
        # Mock configuration
        self.config = {
            'GCP_BUCKET_NAME': 'test-bucket',
            'GCP_PROJECT_ID': 'test-project'
        }

        # Create patches for GCP client
        self.client_patcher = patch('pub_proxy.infrastructure.services.gcp_storage_service.storage.Client')
        self.mock_client = self.client_patcher.start()

        # Mock bucket
        self.mock_bucket = MagicMock()
        self.mock_client.return_value.bucket.return_value = self.mock_bucket
        self.mock_bucket.exists.return_value = True

        # Create the service
        self.storage_service = GCPStorageService(self.config)

        # Create a temporary file for testing
        self.test_file = tempfile.NamedTemporaryFile(delete=False)
        self.test_file.write(b'Test content')
        self.test_file.close()

    def tearDown(self):
        """Clean up the test environment."""
        # Stop the patcher
        self.client_patcher.stop()

        # Remove the temporary file
        os.unlink(self.test_file.name)

    def test_init_creates_bucket_if_not_exists(self):
        """Test that the bucket is created if it doesn't exist."""
        # Set up the mock to indicate the bucket doesn't exist
        self.mock_bucket.exists.return_value = False

        # Create a new service instance
        GCPStorageService(self.config)

        # Check that create_bucket was called
        self.mock_client.return_value.create_bucket.assert_called_once_with('test-bucket')

    def test_upload_file_to_blob(self):
        """Test uploading a file to a blob."""
        blob_name = 'test/file.txt'
        mock_blob = MagicMock()
        self.mock_bucket.blob.return_value = mock_blob

        # Call the method
        self.storage_service.upload_file_to_blob(self.test_file.name, blob_name)

        # Check that the blob was created and the file was uploaded
        self.mock_bucket.blob.assert_called_once_with(blob_name)
        mock_blob.upload_from_filename.assert_called_once_with(self.test_file.name)

    def test_upload_string_to_blob(self):
        """Test uploading a string to a blob."""
        blob_name = 'test/string.txt'
        content = 'String content'
        mock_blob = MagicMock()
        self.mock_bucket.blob.return_value = mock_blob

        # Call the method
        self.storage_service.upload_string_to_blob(content, blob_name)

        # Check that the blob was created and the string was uploaded
        self.mock_bucket.blob.assert_called_once_with(blob_name)
        mock_blob.upload_from_string.assert_called_once_with(content)

    def test_download_blob_to_file(self):
        """Test downloading a blob to a file."""
        blob_name = 'test/download.txt'
        file_path = 'downloaded.txt'
        mock_blob = MagicMock()
        self.mock_bucket.blob.return_value = mock_blob

        # Call the method
        self.storage_service.download_blob_to_file(blob_name, file_path)

        # Check that the blob was retrieved and downloaded
        self.mock_bucket.blob.assert_called_once_with(blob_name)
        mock_blob.download_to_filename.assert_called_once_with(file_path)

    def test_download_blob_as_string(self):
        """Test downloading a blob as a string."""
        blob_name = 'test/string_download.txt'
        mock_blob = MagicMock()
        self.mock_bucket.blob.return_value = mock_blob
        mock_blob.download_as_text.return_value = 'Downloaded content'

        # Call the method
        result = self.storage_service.download_blob_as_string(blob_name)

        # Check that the blob was retrieved and downloaded
        self.mock_bucket.blob.assert_called_once_with(blob_name)
        mock_blob.download_as_text.assert_called_once()
        self.assertEqual(result, 'Downloaded content')

    def test_blob_exists(self):
        """Test checking if a blob exists."""
        blob_name = 'test/exists.txt'
        mock_blob = MagicMock()
        self.mock_bucket.blob.return_value = mock_blob
        mock_blob.exists.return_value = True

        # Call the method
        result = self.storage_service.blob_exists(blob_name)

        # Check that the blob was checked
        self.mock_bucket.blob.assert_called_once_with(blob_name)
        mock_blob.exists.assert_called_once()
        self.assertTrue(result)

    def test_list_blobs(self):
        """Test listing blobs with a prefix."""
        prefix = 'test/'
        mock_blob1 = MagicMock()
        mock_blob1.name = 'test/file1.txt'
        mock_blob2 = MagicMock()
        mock_blob2.name = 'test/file2.txt'
        self.mock_bucket.list_blobs.return_value = [mock_blob1, mock_blob2]

        # Call the method
        result = self.storage_service.list_blobs(prefix)

        # Check that the blobs were listed
        self.mock_bucket.list_blobs.assert_called_once_with(prefix=prefix)
        self.assertEqual(result, ['test/file1.txt', 'test/file2.txt'])

    def test_get_blob_url(self):
        """Test getting the URL of a blob."""
        blob_name = 'test/url.txt'
        mock_blob = MagicMock()
        self.mock_bucket.blob.return_value = mock_blob

        # Call the method
        result = self.storage_service.get_blob_url(blob_name)

        # Check the URL format
        expected_url = f'https://storage.googleapis.com/{self.config["GCP_BUCKET_NAME"]}/{blob_name}'
        self.assertEqual(result, expected_url)


if __name__ == '__main__':
    unittest.main()