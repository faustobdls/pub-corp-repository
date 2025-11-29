import os
import tempfile
import hashlib
from datetime import datetime
import re
import tarfile
from injector import inject

from pub_proxy.core.entities.package import Package, PackageVersion
from pub_proxy.infrastructure.repositories.package_repository import PackageRepository
from pub_proxy.core.interfaces.storage_service_interface import StorageServiceInterface
from pub_proxy.core.app_config import AppConfig

"""
Upload Package Use Case module.

This module defines the use case for uploading package archives to the repository.
It handles storing package archives in the GCP bucket and updating package information.

@example
```python
from pub_proxy.core.use_cases.upload_package_use_case import UploadPackageUseCase

upload_use_case = UploadPackageUseCase(gcp_service, package_repository)
result = upload_use_case.execute('my_package', '1.0.0', file_object)
```
"""


class UploadPackageUseCase:
    """
    Use case for uploading package archives to the repository.
    
    This class handles storing package archives in the GCP bucket and updating package information.
    It provides a method for uploading a package archive and creating or updating the package
    information in the repository.
    
    @method execute: Upload a package archive to the repository.
    """
    
    @inject
    def __init__(self, storage_service: StorageServiceInterface, package_repository: PackageRepository, config: AppConfig):
        """
        Initialize the use case with its dependencies.
        
        @param storage_service: The service for interacting with storage (GCP or local).
        @param package_repository: The repository for storing package information.
        @param config: The application configuration.
        """
        self.storage_service = storage_service
        self.package_repository = package_repository
        self.config = config
    
    def execute(self, package_name, version, file_object):
        """
        Upload a package archive to the repository.
        
        This method stores the package archive in the storage and creates or updates
        the package information in the repository.
        
        @param package_name: The name of the package (optional, extracted from tarball if None).
        @param version: The version of the package (optional, extracted from tarball if None).
        @param file_object: The file object containing the package archive.
        @return: A dictionary with the result of the upload operation.
        """
        # Save the file to a temporary location
        temp_file = tempfile.NamedTemporaryFile(delete=False, suffix='.tar.gz')
        file_object.save(temp_file.name)
        
        try:
            # Extract package info if not provided
            if not package_name or not version:
                extracted_name, extracted_version = self._extract_metadata(temp_file.name)
                package_name = package_name or extracted_name
                version = version or extracted_version
            
            # Calculate the SHA-256 hash of the file
            sha256_hash = self._calculate_sha256(temp_file.name)
            
            # Upload the file to the storage
            blob_name = f'{package_name}/{version}/archive.tar.gz'
            self.storage_service.upload_file_to_blob(temp_file.name, blob_name)
            
            # Construct the archive URL
            # We need to return a URL that points to the application's download endpoint
            host = self.config.get('HOST', 'localhost')
            if host == '0.0.0.0':
                host = 'localhost'
            port = self.config.get('PORT', 5000)
            base_url = self.config.get('EXTERNAL_URL', f'http://{host}:{port}')
            archive_url = f'{base_url}/api/packages/{package_name}/versions/{version}/archive.tar.gz'
            
            # Create or update the package information in the repository
            package = self.package_repository.get_package(package_name)
            
            if not package:
                # Create a new package
                package_version = PackageVersion(
                    version=version,
                    published=datetime.now(),
                    archive_url=archive_url,
                    archive_sha256=sha256_hash
                )
                
                package = Package(
                    name=package_name,
                    versions=[package_version],
                    latest_version=version,
                    is_private=True
                )
            else:
                # Update an existing package
                version_exists = False
                for pkg_version in package.versions:
                    if pkg_version.version == version:
                        # Update the existing version
                        pkg_version.published = datetime.now()
                        pkg_version.archive_url = archive_url
                        pkg_version.archive_sha256 = sha256_hash
                        version_exists = True
                        break
                
                if not version_exists:
                    # Add a new version
                    package_version = PackageVersion(
                        version=version,
                        published=datetime.now(),
                        archive_url=archive_url,
                        archive_sha256=sha256_hash
                    )
                    package.versions.append(package_version)
                
                # Update the latest version if the new version is greater
                if self._compare_versions(version, package.latest_version) > 0:
                    package.latest_version = version
            
            # Save the package information to the repository
            self.package_repository.save_package(package)
            
            return {
                'success': True,
                'package': package_name,
                'version': version,
                'archive_url': archive_url,
                'archive_sha256': sha256_hash
            }
            
        finally:
            # Clean up the temporary file
            if os.path.exists(temp_file.name):
                os.unlink(temp_file.name)
    
    def _extract_metadata(self, tarball_path):
        """
        Extract package name and version from pubspec.yaml in the tarball.
        
        @param tarball_path: Path to the tarball file.
        @return: Tuple (name, version).
        @raise ValueError: If pubspec.yaml is missing or invalid.
        """
        try:
            with tarfile.open(tarball_path, "r:gz") as tar:
                # Find pubspec.yaml
                pubspec_member = None
                for member in tar.getmembers():
                    if member.name.endswith('pubspec.yaml'):
                        pubspec_member = member
                        break
                
                if not pubspec_member:
                    raise ValueError("pubspec.yaml not found in archive")
                
                f = tar.extractfile(pubspec_member)
                content = f.read().decode('utf-8')
                
                name_match = re.search(r'^name:\s+(.+)$', content, re.MULTILINE)
                version_match = re.search(r'^version:\s+(.+)$', content, re.MULTILINE)
                
                if not name_match or not version_match:
                    raise ValueError("Could not parse name or version from pubspec.yaml")
                    
                return name_match.group(1).strip(), version_match.group(1).strip()
                
        except Exception as e:
            raise ValueError(f"Failed to extract metadata: {str(e)}")

    def _calculate_sha256(self, file_path):
        """
        Calculate the SHA-256 hash of a file.
        
        @param file_path: The path to the file.
        @return: The SHA-256 hash of the file as a hexadecimal string.
        """
        sha256_hash = hashlib.sha256()
        
        with open(file_path, 'rb') as f:
            for byte_block in iter(lambda: f.read(4096), b""):
                sha256_hash.update(byte_block)
        
        return sha256_hash.hexdigest()
    
    def _compare_versions(self, version1, version2):
        """
        Compare two version strings.
        
        @param version1: The first version string.
        @param version2: The second version string.
        @return: -1 if version1 < version2, 0 if version1 == version2, 1 if version1 > version2.
        """
        if version1 == version2:
            return 0
        
        # Remove build numbers (everything after '+') from versions
        v1_clean = version1.split('+')[0]
        v2_clean = version2.split('+')[0]
        
        # Handle pre-release versions (everything after '-')
        v1_base = v1_clean.split('-')[0]
        v2_base = v2_clean.split('-')[0]
        v1_prerelease = v1_clean.split('-')[1] if '-' in v1_clean else None
        v2_prerelease = v2_clean.split('-')[1] if '-' in v2_clean else None
        
        # Compare base versions first
        v1_parts = v1_base.split('.')
        v2_parts = v2_base.split('.')
        
        for i in range(max(len(v1_parts), len(v2_parts))):
            v1 = int(v1_parts[i]) if i < len(v1_parts) else 0
            v2 = int(v2_parts[i]) if i < len(v2_parts) else 0
            
            if v1 < v2:
                return -1
            elif v1 > v2:
                return 1
        
        # If base versions are equal, handle pre-release comparison
        if v1_prerelease is None and v2_prerelease is None:
            return 0
        elif v1_prerelease is None:  # v1 is release, v2 is pre-release
            return 1
        elif v2_prerelease is None:  # v1 is pre-release, v2 is release
            return -1
        else:  # Both are pre-releases, compare lexicographically
            if v1_prerelease < v2_prerelease:
                return -1
            elif v1_prerelease > v2_prerelease:
                return 1
            else:
                return 0