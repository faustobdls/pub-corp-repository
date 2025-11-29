import os
import json
import shutil
from pathlib import Path
from injector import inject

from pub_proxy.core.interfaces.storage_service_interface import StorageServiceInterface
from pub_proxy.core.app_config import AppConfig

"""
Local Storage Service module.

This module defines the service for interacting with local file system storage.
It handles uploading, downloading, and managing files in a local directory.
It implements the same interface as GCPStorageService for interchangeability.

@example
```python
from pub_proxy.infrastructure.services.local_storage_service import LocalStorageService

local_service = LocalStorageService(config)
local_service.upload_file_to_blob('local_file.txt', 'remote_file.txt')
```
"""


class LocalStorageService(StorageServiceInterface):
    """
    Service for interacting with local file system storage.
    
    This class handles uploading, downloading, and managing files in a local directory.
    It provides methods for uploading files, downloading files, checking if files exist,
    and listing files in the directory, with the same interface as GCPStorageService.
    
    @method upload_file_to_blob: Upload a file to a blob in the storage.
    @method upload_string_to_blob: Upload a string to a blob in the storage.
    @method download_blob_to_file: Download a blob to a local file.
    @method download_blob_as_string: Download a blob as a string.
    @method blob_exists: Check if a blob exists in the storage.
    @method list_blobs: List blobs in the storage with a given prefix.
    @method get_blob_url: Get the URL of a blob in the storage.
    """
    
    @inject
    def __init__(self, config: AppConfig):
        """
        Initialize the service with its dependencies.
        
        @param config: The application configuration.
        """
        self.storage_dir = config['LOCAL_STORAGE_DIR']
        
        # Create the storage directory if it doesn't exist
        os.makedirs(self.storage_dir, exist_ok=True)
    
    def upload_file_to_blob(self, file_path, blob_name):
        """
        Upload a file to a blob in the storage.
        
        @param file_path: The path to the local file to upload.
        @param blob_name: The name of the blob in the storage.
        """
        target_path = os.path.join(self.storage_dir, blob_name)
        os.makedirs(os.path.dirname(target_path), exist_ok=True)
        shutil.copy2(file_path, target_path)
    
    def upload_string_to_blob(self, content, blob_name):
        """
        Upload a string to a blob in the storage.
        
        @param content: The string content to upload.
        @param blob_name: The name of the blob in the storage.
        """
        target_path = os.path.join(self.storage_dir, blob_name)
        os.makedirs(os.path.dirname(target_path), exist_ok=True)
        with open(target_path, 'w') as f:
            f.write(content)
    
    def download_blob_to_file(self, blob_name, file_path):
        """
        Download a blob to a local file.
        
        @param blob_name: The name of the blob in the storage.
        @param file_path: The path to the local file to download to.
        """
        source_path = os.path.join(self.storage_dir, blob_name)
        os.makedirs(os.path.dirname(file_path), exist_ok=True)
        shutil.copy2(source_path, file_path)
    
    def download_blob_as_string(self, blob_name):
        """
        Download a blob as a string.
        
        @param blob_name: The name of the blob in the storage.
        @return: The content of the blob as a string.
        """
        source_path = os.path.join(self.storage_dir, blob_name)
        with open(source_path, 'r') as f:
            return f.read()
    
    def blob_exists(self, blob_name):
        """
        Check if a blob exists in the storage.
        
        @param blob_name: The name of the blob in the storage.
        @return: True if the blob exists, False otherwise.
        """
        return os.path.exists(os.path.join(self.storage_dir, blob_name))
    
    def list_blobs(self, prefix=''):
        """
        List blobs in the storage with a given prefix.
        
        @param prefix: The prefix to filter blobs by.
        @return: A list of blob names.
        """
        prefix_path = os.path.join(self.storage_dir, prefix)
        result = []
        
        if os.path.exists(prefix_path):
            if os.path.isdir(prefix_path):
                for root, _, files in os.walk(prefix_path):
                    for file in files:
                        full_path = os.path.join(root, file)
                        rel_path = os.path.relpath(full_path, self.storage_dir)
                        result.append(rel_path)
            else:
                rel_path = os.path.relpath(prefix_path, self.storage_dir)
                result.append(rel_path)
                
        return result
    
    def get_blob_url(self, blob_name):
        """
        Get the URL of a blob in the storage.
        
        @param blob_name: The name of the blob in the storage.
        @return: The URL of the blob.
        """
        # For local storage, we just return the file path
        return f'file://{os.path.join(self.storage_dir, blob_name)}'