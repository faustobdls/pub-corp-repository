import json
import os
from datetime import datetime
from typing import List, Dict, Optional
from injector import inject

from pub_proxy.core.entities.package import Package, PackageVersion
from pub_proxy.core.interfaces.storage_service_interface import StorageServiceInterface

"""
Package Repository module.

This module defines the repository for storing and retrieving package information.
It handles persisting package data in the GCP bucket and providing access to that data.

@example
```python
from pub_proxy.infrastructure.repositories.package_repository import PackageRepository

repository = PackageRepository(gcp_storage_service)
package = repository.get_package('flutter')
```
"""


class PackageRepository:
    """
    Repository for storing and retrieving package information.
    
    This class handles persisting package data in the GCP bucket and providing access to that data.
    It provides methods for getting, saving, and listing packages, as well as updating package
    information with data from pub.dev.
    
    @method get_package: Get a package by name.
    @method save_package: Save a package to the repository.
    @method list_packages: List packages in the repository.
    @method save_package_info: Save package information from pub.dev.
    @method save_package_version: Save package version information from pub.dev.
    """
    
    @inject
    def __init__(self, storage_service: StorageServiceInterface):
        """
        Initialize the repository with its dependencies.
        
        @param storage_service: The service for interacting with storage (GCP or local).
        """
        self.storage_service = storage_service
    
    def get_package(self, package_name) -> Optional[Package]:
        """
        Get a package by name.
        
        This method retrieves a package from the repository by its name.
        If the package does not exist, it returns None.
        
        @param package_name: The name of the package.
        @return: The Package entity, or None if not found.
        """
        blob_name = f'packages/{package_name}/metadata.json'
        
        if not self.storage_service.blob_exists(blob_name):
            return None
        
        # Download the package metadata from the storage
        metadata_json = self.storage_service.download_blob_as_string(blob_name)
        metadata = json.loads(metadata_json)
        
        # Create the Package entity from the metadata
        versions = []
        for version_data in metadata.get('versions', []):
            version = PackageVersion(
                version=version_data['version'],
                published=datetime.fromisoformat(version_data['published']),
                dependencies=version_data.get('dependencies', {}),
                environment=version_data.get('environment', {}),
                archive_url=version_data.get('archive_url'),
                archive_sha256=version_data.get('archive_sha256')
            )
            versions.append(version)
        
        package = Package(
            name=metadata['name'],
            versions=versions,
            latest_version=metadata.get('latest_version'),
            description=metadata.get('description'),
            homepage=metadata.get('homepage'),
            repository=metadata.get('repository'),
            is_private=metadata.get('is_private', False)
        )
        
        return package
    
    def save_package(self, package: Package) -> None:
        """
        Save a package to the repository.
        
        This method persists a package entity to the repository.
        It converts the package to a JSON representation and stores it in the GCP bucket.
        
        @param package: The Package entity to save.
        """
        # Convert the Package entity to a JSON representation
        metadata = {
            'name': package.name,
            'latest_version': package.latest_version,
            'description': package.description,
            'homepage': package.homepage,
            'repository': package.repository,
            'is_private': package.is_private,
            'versions': []
        }
        
        for version in package.versions:
            version_data = {
                'version': version.version,
                'published': version.published.isoformat(),
                'dependencies': version.dependencies,
                'environment': version.environment,
                'archive_url': version.archive_url,
                'archive_sha256': version.archive_sha256
            }
            metadata['versions'].append(version_data)
        
        # Upload the package metadata to the storage
        blob_name = f'packages/{package.name}/metadata.json'
        self.storage_service.upload_string_to_blob(json.dumps(metadata), blob_name)
    
    def list_packages(self, query='') -> List[Dict]:
        """
        List packages in the repository.
        
        This method retrieves a list of packages from the repository.
        It can filter packages by name or description using the query parameter.
        
        @param query: The search query to filter packages by name or description.
        @return: A list of dictionaries with package information.
        """
        # List all package metadata files in the storage
        blobs = self.storage_service.list_blobs('packages/')
        
        packages = []
        for blob in blobs:
            if blob.endswith('/metadata.json'):
                # Extract the package name from the blob name
                package_name = blob.split('/')[1]
                
                # Get the package from the repository
                package = self.get_package(package_name)
                
                if package and (not query or query.lower() in package.name.lower() or 
                               (package.description and query.lower() in package.description.lower())):
                    # Convert the Package entity to a dictionary
                    package_dict = {
                        'name': package.name,
                        'latest': package.latest_version,
                        'description': package.description,
                        'homepage': package.homepage,
                        'repository': package.repository,
                        'is_private': package.is_private
                    }
                    packages.append(package_dict)
        
        return packages
    
    def save_package_info(self, package_name, package_info) -> None:
        """
        Save package information from pub.dev.
        
        This method creates or updates a package in the repository with information from pub.dev.
        It converts the pub.dev package information to a Package entity and saves it.
        
        @param package_name: The name of the package.
        @param package_info: The package information from pub.dev.
        """
        # Check if the package already exists in the repository
        package = self.get_package(package_name)
        
        if not package:
            # Create a new Package entity
            package = Package(
                name=package_name,
                latest_version=package_info.get('latest', {}).get('version'),
                description=package_info.get('description'),
                homepage=package_info.get('homepage'),
                repository=package_info.get('repository'),
                is_private=False
            )
        else:
            # Update the existing Package entity
            package.latest_version = package_info.get('latest', {}).get('version')
            package.description = package_info.get('description')
            package.homepage = package_info.get('homepage')
            package.repository = package_info.get('repository')
        
        # Add versions from pub.dev
        for version_info in package_info.get('versions', []):
            version_name = version_info.get('version')
            # Check if the version already exists in the package
            version_exists = False
            for version in package.versions:
                if version.version == version_name:
                    version_exists = True
                    break
            
            if not version_exists:
                # Create a new PackageVersion entity
                version = PackageVersion(
                    version=version_name,
                    published=datetime.fromisoformat(version_info.get('published')),
                    dependencies=version_info.get('pubspec', {}).get('dependencies', {}),
                    environment=version_info.get('pubspec', {}).get('environment', {}),
                    archive_url=version_info.get('archive_url'),
                    archive_sha256=version_info.get('archive_sha256')
                )
                package.versions.append(version)
                
                # Update the latest version if this version is newer
                if not package.latest_version or self._compare_versions(version_name, package.latest_version) > 0:
                    package.latest_version = version_name
        
        # Save the package to the repository
        self.save_package(package)
    
    def save_package_version(self, package_name, version_name, version_info) -> None:
        """
        Save package version information from pub.dev.
        
        This method creates or updates a package version in the repository with information from pub.dev.
        It converts the pub.dev version information to a PackageVersion entity and saves it.
        
        @param package_name: The name of the package.
        @param version_name: The version of the package.
        @param version_info: The version information from pub.dev.
        """
        # Get the package from the repository
        package = self.get_package(package_name)
        
        if not package:
            # Create a new Package entity
            package = Package(
                name=package_name,
                latest_version=version_name,
                is_private=False
            )
        
        # Check if the version already exists in the package
        version_exists = False
        for version in package.versions:
            if version.version == version_name:
                # Update the existing PackageVersion entity
                version.published = datetime.fromisoformat(version_info.get('published'))
                version.dependencies = version_info.get('dependencies', {})
                version.archive_url = version_info.get('archive_url')
                version.archive_sha256 = version_info.get('archive_sha256')
                version_exists = True
                break
        
        if not version_exists:
            # Create a new PackageVersion entity
            version = PackageVersion(
                version=version_name,
                published=datetime.fromisoformat(version_info.get('published')),
                dependencies=version_info.get('dependencies', {}),
                archive_url=version_info.get('archive_url'),
                archive_sha256=version_info.get('archive_sha256')
            )
            package.versions.append(version)
        
        # Update the latest version if necessary
        if not package.latest_version or self._compare_versions(version_name, package.latest_version) > 0:
            package.latest_version = version_name
        
        # Save the package to the repository
        self.save_package(package)
    
    def _compare_versions(self, version1, version2):
        """
        Compare two version strings with support for pre-release versions.
        
        @param version1: The first version string.
        @param version2: The second version string.
        @return: -1 if version1 < version2, 0 if version1 == version2, 1 if version1 > version2.
        """
        if version1 == version2:
            return 0
        
        # Split version and pre-release parts
        def parse_version(version):
            if '-' in version:
                base_version, pre_release = version.split('-', 1)
            else:
                base_version, pre_release = version, None
            return base_version, pre_release
        
        v1_base, v1_pre = parse_version(version1)
        v2_base, v2_pre = parse_version(version2)
        
        # Remove build numbers (everything after '+') from base versions
        if '+' in v1_base:
            v1_base = v1_base.split('+')[0]
        if '+' in v2_base:
            v2_base = v2_base.split('+')[0]
        
        # Compare base versions
        v1_parts = [int(x) for x in v1_base.split('.')]
        v2_parts = [int(x) for x in v2_base.split('.')]
        
        # Pad with zeros to make same length
        max_len = max(len(v1_parts), len(v2_parts))
        v1_parts.extend([0] * (max_len - len(v1_parts)))
        v2_parts.extend([0] * (max_len - len(v2_parts)))
        
        for i in range(max_len):
            if v1_parts[i] < v2_parts[i]:
                return -1
            elif v1_parts[i] > v2_parts[i]:
                return 1
        
        # Base versions are equal, compare pre-release
        if v1_pre is None and v2_pre is None:
            return 0
        elif v1_pre is None:  # v1 is stable, v2 is pre-release
            return 1
        elif v2_pre is None:  # v1 is pre-release, v2 is stable
            return -1
        else:  # Both are pre-release, compare lexicographically
            if v1_pre < v2_pre:
                return -1
            elif v1_pre > v2_pre:
                return 1
            else:
                return 0