from abc import ABC, abstractmethod

"""
Storage Service Interface module.

This module defines the abstract interface for storage services.
It provides a contract that all storage service implementations must follow.

@example
```python
from pub_proxy.core.interfaces.storage_service_interface import StorageServiceInterface

class MyStorageService(StorageServiceInterface):
    def upload_file_to_blob(self, file_path, blob_name):
        # Implementation here
        pass
```
"""


class StorageServiceInterface(ABC):
    """
    Abstract interface for storage services.
    
    This interface defines the contract that all storage service implementations
    must follow. It includes methods for uploading, downloading, and managing files.
    """
    
    @abstractmethod
    def upload_file_to_blob(self, file_path, blob_name):
        """
        Upload a file to a blob in the storage.
        
        @param file_path: The path to the local file to upload.
        @param blob_name: The name of the blob in the storage.
        """
        pass
    
    @abstractmethod
    def upload_string_to_blob(self, content, blob_name):
        """
        Upload string content to a blob in the storage.
        
        @param content: The string content to upload.
        @param blob_name: The name of the blob in the storage.
        """
        pass
    
    @abstractmethod
    def download_blob_to_file(self, blob_name, file_path):
        """
        Download a blob to a local file.
        
        @param blob_name: The name of the blob in the storage.
        @param file_path: The path to save the downloaded file.
        """
        pass
    
    @abstractmethod
    def download_blob_as_string(self, blob_name):
        """
        Download a blob as a string.
        
        @param blob_name: The name of the blob in the storage.
        @return: The content of the blob as a string.
        """
        pass
    
    @abstractmethod
    def blob_exists(self, blob_name):
        """
        Check if a blob exists in the storage.
        
        @param blob_name: The name of the blob to check.
        @return: True if the blob exists, False otherwise.
        """
        pass
    
    @abstractmethod
    def list_blobs(self, prefix=''):
        """
        List blobs in the storage with an optional prefix.
        
        @param prefix: The prefix to filter blobs (optional).
        @return: A list of blob names.
        """
        pass
    
    @abstractmethod
    def get_blob_url(self, blob_name):
        """
        Get the URL of a blob.
        
        @param blob_name: The name of the blob.
        @return: The URL of the blob.
        """
        pass