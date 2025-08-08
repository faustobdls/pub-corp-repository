import os
import shutil
import tempfile
import unittest
from pathlib import Path

from pub_proxy.infrastructure.services.local_storage_service import LocalStorageService


class TestLocalStorageService(unittest.TestCase):
    """Test cases for the LocalStorageService class."""

    def setUp(self):
        """Set up the test environment."""
        # Create a temporary directory for testing
        self.temp_dir = tempfile.mkdtemp()
        self.config = {'LOCAL_STORAGE_DIR': self.temp_dir}
        self.storage_service = LocalStorageService(self.config)

        # Create a temporary file for testing
        self.test_file = tempfile.NamedTemporaryFile(delete=False)
        self.test_file.write(b'Test content')
        self.test_file.close()

    def tearDown(self):
        """Clean up the test environment."""
        # Remove the temporary directory and file
        shutil.rmtree(self.temp_dir)
        os.unlink(self.test_file.name)

    def test_upload_file_to_blob(self):
        """Test uploading a file to a blob."""
        blob_name = 'test/file.txt'
        self.storage_service.upload_file_to_blob(self.test_file.name, blob_name)

        # Check if the file was uploaded
        target_path = os.path.join(self.temp_dir, blob_name)
        self.assertTrue(os.path.exists(target_path))

        # Check the content of the uploaded file
        with open(target_path, 'r') as f:
            content = f.read()
        self.assertEqual(content, 'Test content')

    def test_upload_string_to_blob(self):
        """Test uploading a string to a blob."""
        blob_name = 'test/string.txt'
        content = 'String content'
        self.storage_service.upload_string_to_blob(content, blob_name)

        # Check if the file was created
        target_path = os.path.join(self.temp_dir, blob_name)
        self.assertTrue(os.path.exists(target_path))

        # Check the content of the created file
        with open(target_path, 'r') as f:
            file_content = f.read()
        self.assertEqual(file_content, content)

    def test_download_blob_to_file(self):
        """Test downloading a blob to a file."""
        # Upload a file first
        blob_name = 'test/download.txt'
        content = 'Download content'
        self.storage_service.upload_string_to_blob(content, blob_name)

        # Download the file
        download_path = os.path.join(self.temp_dir, 'downloaded.txt')
        self.storage_service.download_blob_to_file(blob_name, download_path)

        # Check if the file was downloaded
        self.assertTrue(os.path.exists(download_path))

        # Check the content of the downloaded file
        with open(download_path, 'r') as f:
            file_content = f.read()
        self.assertEqual(file_content, content)

    def test_download_blob_as_string(self):
        """Test downloading a blob as a string."""
        # Upload a file first
        blob_name = 'test/string_download.txt'
        content = 'String download content'
        self.storage_service.upload_string_to_blob(content, blob_name)

        # Download the file as string
        downloaded_content = self.storage_service.download_blob_as_string(blob_name)

        # Check the content
        self.assertEqual(downloaded_content, content)

    def test_blob_exists(self):
        """Test checking if a blob exists."""
        # Upload a file first
        blob_name = 'test/exists.txt'
        content = 'Exists content'
        self.storage_service.upload_string_to_blob(content, blob_name)

        # Check if the blob exists
        self.assertTrue(self.storage_service.blob_exists(blob_name))

        # Check if a non-existent blob doesn't exist
        self.assertFalse(self.storage_service.blob_exists('test/nonexistent.txt'))
    
    def test_list_blobs_specific_file(self):
        """Test listing blobs when prefix points to a specific file."""
        # Upload a specific file
        blob_name = 'packages/test_package/metadata.json'
        content = '{"name": "test_package"}'
        self.storage_service.upload_string_to_blob(content, blob_name)
        
        # List blobs with the exact file path as prefix
        blobs = self.storage_service.list_blobs('packages/test_package/metadata.json')
        
        # Should return the specific file
        self.assertEqual(len(blobs), 1)
        self.assertEqual(blobs[0], 'packages/test_package/metadata.json')
    
    def test_get_blob_url(self):
        """Test getting blob URL."""
        blob_name = 'test/file.txt'
        url = self.storage_service.get_blob_url(blob_name)
        
        # Should return a file:// URL
        self.assertTrue(url.startswith('file://'))
        self.assertIn(blob_name, url)

    def test_list_blobs(self):
        """Test listing blobs with a prefix."""
        # Upload some files
        self.storage_service.upload_string_to_blob('Content 1', 'test/list1.txt')
        self.storage_service.upload_string_to_blob('Content 2', 'test/list2.txt')
        self.storage_service.upload_string_to_blob('Content 3', 'other/list3.txt')

        # List blobs with prefix 'test/'
        blobs = self.storage_service.list_blobs('test/')
        self.assertEqual(len(blobs), 2)
        self.assertIn('test/list1.txt', blobs)
        self.assertIn('test/list2.txt', blobs)

        # List all blobs
        all_blobs = self.storage_service.list_blobs()
        self.assertEqual(len(all_blobs), 3)

    def test_get_blob_url(self):
        """Test getting the URL of a blob."""
        blob_name = 'test/url.txt'
        self.storage_service.upload_string_to_blob('URL content', blob_name)

        # Get the URL
        url = self.storage_service.get_blob_url(blob_name)
        expected_url = f'file://{os.path.join(self.temp_dir, blob_name)}'
        self.assertEqual(url, expected_url)


if __name__ == '__main__':
    unittest.main()