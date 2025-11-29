import os
import tempfile
from injector import inject

from pub_proxy.infrastructure.services.pub_dev_service import PubDevService
from pub_proxy.infrastructure.repositories.package_repository import PackageRepository
from pub_proxy.core.interfaces.storage_service_interface import StorageServiceInterface
from pub_proxy.core.entities.package import Package, PackageVersion
from pub_proxy.core.app_config import AppConfig

"""
Download Package Use Case module.

This module defines the use case for downloading package archives.
It handles fetching package archives from the GCP bucket or pub.dev.

@example
```python
from pub_proxy.core.use_cases.download_package_use_case import DownloadPackageUseCase

download_use_case = DownloadPackageUseCase(gcp_service, pub_dev_service, package_repository)
file_path, is_stream = download_use_case.execute('flutter', '2.0.0')
```
"""


class DownloadPackageUseCase:
    """
    Use case for downloading package archives.
    
    This class handles fetching package archives from the GCP bucket or pub.dev.
    If the package is available in the GCP bucket, it returns the file path.
    If not, it fetches the package from pub.dev, caches it in the GCP bucket,
    and returns a stream of the package data.
    
    @method execute: Download a package archive.
    """
    
    @inject
    def __init__(
        self,
        storage_service: StorageServiceInterface,
        pub_dev_service: PubDevService,
        package_repository: PackageRepository,
        config: AppConfig
    ):
        """
        Initialize the use case with its dependencies.
        
        @param storage_service: The service for interacting with storage (GCP or local).
        @param pub_dev_service: The service for interacting with pub.dev.
        @param package_repository: The repository for storing package information.
        @param config: The application configuration.
        """
        self.storage_service = storage_service
        self.pub_dev_service = pub_dev_service
        self.package_repository = package_repository
        self.config = config
    
    def execute(self, package_name, version):
        """
        Download a package archive.
        
        This method first checks if the package archive is available in the storage.
        If not, it fetches the archive from pub.dev, caches it in the storage,
        and returns a stream of the archive data.
        
        @param package_name: The name of the package.
        @param version: The version of the package.
        @return: A tuple of (file_path_or_stream, is_stream).
        """
        # Check if the package is in the storage
        blob_name = f'{package_name}/{version}/archive.tar.gz'
        if self.storage_service.blob_exists(blob_name):
            # Download the package from the storage to a temporary file
            temp_file = tempfile.NamedTemporaryFile(delete=False, suffix='.tar.gz')
            self.storage_service.download_blob_to_file(blob_name, temp_file.name)
            return temp_file.name, False
        
        # If not in the GCP bucket, fetch from pub.dev
        stream = self.pub_dev_service.download_package(package_name, version)
        
        # Cache the package in the GCP bucket asynchronously
        self._cache_package(package_name, version, stream)
        
        # Return a new stream from pub.dev
        return self.pub_dev_service.download_package(package_name, version), True
    
    def _cache_package(self, package_name, version, stream):
        """
        Cache a package in the storage.
        
        This method downloads the package from pub.dev and uploads it to the storage.
        It also updates the package information in the repository.
        
        @param package_name: The name of the package.
        @param version: The version of the package.
        @param stream: The stream of the package data.
        """
        # Download the package to a temporary file
        temp_file = tempfile.NamedTemporaryFile(delete=False, suffix='.tar.gz')
        for chunk in stream:
            temp_file.write(chunk)
        temp_file.close()
        
        # Upload the package to the GCP bucket
        blob_name = f'{package_name}/{version}/archive.tar.gz'
        self.storage_service.upload_file_to_blob(temp_file.name, blob_name)
        
        # Update the package information in the repository
        package = self.package_repository.get_package(package_name)
        if package:
            for pkg_version in package.versions:
                if pkg_version.version == version:
                    # Construct the archive URL
                    host = self.config.get('HOST', 'localhost')
                    if host == '0.0.0.0':
                        host = 'localhost'
                    port = self.config.get('PORT', 5000)
                    base_url = self.config.get('EXTERNAL_URL', f'http://{host}:{port}')
                    archive_url = f'{base_url}/api/packages/{package_name}/versions/{version}/archive.tar.gz'
                    
                    pkg_version.archive_url = archive_url
                    self.package_repository.save_package(package)
                    break
        
        # Clean up the temporary file
        os.unlink(temp_file.name)