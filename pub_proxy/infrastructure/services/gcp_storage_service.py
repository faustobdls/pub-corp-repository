import os
import tempfile
from google.cloud import storage
from injector import inject

from pub_proxy.core.interfaces.storage_service_interface import StorageServiceInterface
from pub_proxy.core.app_config import AppConfig

"""
Google Cloud Platform Storage Service module.

This module defines the service for interacting with Google Cloud Storage.
It handles uploading, downloading, and managing files in a GCP bucket.

@example
```python
from pub_proxy.infrastructure.services.gcp_storage_service import GCPStorageService

gcp_service = GCPStorageService(config)
gcp_service.upload_file_to_blob('local_file.txt', 'remote_file.txt')
```
"""


class GCPStorageService(StorageServiceInterface):
    """
    Service for interacting with Google Cloud Storage.
    
    This class handles uploading, downloading, and managing files in a GCP bucket.
    It provides methods for uploading files, downloading files, checking if files exist,
    and listing files in the bucket.
    
    @method upload_file_to_blob: Upload a file to a blob in the bucket.
    @method upload_string_to_blob: Upload a string to a blob in the bucket.
    @method download_blob_to_file: Download a blob to a local file.
    @method download_blob_as_string: Download a blob as a string.
    @method blob_exists: Check if a blob exists in the bucket.
    @method list_blobs: List blobs in the bucket with a given prefix.
    @method get_blob_url: Get the URL of a blob in the bucket.
    """
    
    @inject
    def __init__(self, config: AppConfig):
        """
        Initialize the service with its dependencies.
        
        @param config: The application configuration.
        """
        self.bucket_name = config['GCP_BUCKET_NAME']
        self.project_id = config['GCP_PROJECT_ID']
        
        # Initialize the GCP Storage client
        self.client = storage.Client(project=self.project_id)
        self.bucket = self.client.bucket(self.bucket_name)
        
        # Create the bucket if it doesn't exist
        if not self.bucket.exists():
            self.bucket = self.client.create_bucket(self.bucket_name)
    
    def upload_file_to_blob(self, file_path, blob_name):
        """
        Upload a file to a blob in the bucket.
        
        @param file_path: The path to the local file to upload.
        @param blob_name: The name of the blob in the bucket.
        """
        blob = self.bucket.blob(blob_name)
        blob.upload_from_filename(file_path)
    
    def upload_string_to_blob(self, content, blob_name):
        """
        Upload a string to a blob in the bucket.
        
        @param content: The string content to upload.
        @param blob_name: The name of the blob in the bucket.
        """
        blob = self.bucket.blob(blob_name)
        blob.upload_from_string(content)
    
    def download_blob_to_file(self, blob_name, file_path):
        """
        Download a blob to a local file.
        
        @param blob_name: The name of the blob in the bucket.
        @param file_path: The path to the local file to download to.
        """
        blob = self.bucket.blob(blob_name)
        blob.download_to_filename(file_path)
    
    def download_blob_as_string(self, blob_name):
        """
        Download a blob as a string.
        
        @param blob_name: The name of the blob in the bucket.
        @return: The content of the blob as a string.
        """
        blob = self.bucket.blob(blob_name)
        return blob.download_as_text()
    
    def blob_exists(self, blob_name):
        """
        Check if a blob exists in the bucket.
        
        @param blob_name: The name of the blob in the bucket.
        @return: True if the blob exists, False otherwise.
        """
        blob = self.bucket.blob(blob_name)
        return blob.exists()
    
    def list_blobs(self, prefix=''):
        """
        List blobs in the bucket with a given prefix.
        
        @param prefix: The prefix to filter blobs by.
        @return: A list of blob names.
        """
        blobs = self.bucket.list_blobs(prefix=prefix)
        return [blob.name for blob in blobs]
    
    def get_blob_url(self, blob_name):
        """
        Get the URL of a blob in the bucket.
        
        @param blob_name: The name of the blob in the bucket.
        @return: The URL of the blob.
        """
        blob = self.bucket.blob(blob_name)
        return f'https://storage.googleapis.com/{self.bucket_name}/{blob_name}'