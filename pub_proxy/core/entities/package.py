from dataclasses import dataclass, field
from typing import List, Dict, Optional
from datetime import datetime

"""
Package entity module.

This module defines the Package entity, which represents a Dart/Flutter package in the repository.
It includes information about the package, such as its name, versions, and metadata.

@example
```python
from pub_proxy.core.entities.package import Package, PackageVersion

version = PackageVersion(version='1.0.0', published=datetime.now())
package = Package(name='my_package', versions=[version])
```
"""


@dataclass
class PackageVersion:
    """
    Represents a version of a package.
    
    This class contains information about a specific version of a package,
    including its version number, publication date, dependencies, and archive information.
    
    @property version: The version number of the package.
    @property published: The date and time when the version was published.
    @property dependencies: A dictionary of package dependencies.
    @property environment: A dictionary of environment constraints (e.g., SDK version).
    @property archive_url: The URL to the package archive.
    @property archive_sha256: The SHA-256 hash of the package archive.
    """
    version: str
    published: datetime
    dependencies: Dict[str, str] = field(default_factory=dict)
    environment: Dict[str, str] = field(default_factory=dict)
    archive_url: Optional[str] = None
    archive_sha256: Optional[str] = None


@dataclass
class Package:
    """
    Represents a package in the repository.
    
    This class contains information about a package, including its name,
    available versions, and metadata.
    
    @property name: The name of the package.
    @property versions: A list of available versions of the package.
    @property latest_version: The latest version of the package.
    @property description: A brief description of the package.
    @property homepage: The URL to the package's homepage.
    @property repository: The URL to the package's repository.
    @property is_private: Whether the package is private or public.
    """
    name: str
    versions: List[PackageVersion] = field(default_factory=list)
    latest_version: Optional[str] = None
    description: Optional[str] = None
    homepage: Optional[str] = None
    repository: Optional[str] = None
    is_private: bool = False