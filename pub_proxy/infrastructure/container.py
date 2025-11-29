from injector import singleton, provider

from pub_proxy.core.use_cases.proxy_package_use_case import ProxyPackageUseCase
from pub_proxy.core.use_cases.upload_package_use_case import UploadPackageUseCase
from pub_proxy.core.use_cases.download_package_use_case import DownloadPackageUseCase
from pub_proxy.core.use_cases.list_packages_use_case import ListPackagesUseCase
from pub_proxy.core.interfaces.storage_service_interface import StorageServiceInterface

from pub_proxy.infrastructure.repositories.package_repository import PackageRepository
from pub_proxy.infrastructure.services.gcp_storage_service import GCPStorageService
from pub_proxy.infrastructure.services.local_storage_service import LocalStorageService
from pub_proxy.infrastructure.services.pub_dev_service import PubDevService
from pub_proxy.core.services.auth_service import AuthService
from pub_proxy.core.app_config import AppConfig

"""
Dependency injection container configuration module.

This module configures the dependency injection container for the application.
It binds interfaces to their implementations and configures services with their dependencies.

@example
```python
from injector import Injector
from pub_proxy.infrastructure.container import configure_container

injector = Injector([lambda binder: configure_container(binder, config)])
```
"""


def configure_container(binder, config):
    """
    Configure the dependency injection container.
    
    This function binds interfaces to their implementations and configures services
    with their dependencies. It is used by the Injector to set up the dependency injection container.
    
    @param binder: The binder instance from the Injector.
    @param config: The application configuration.
    """
    # Bind configuration
    binder.bind(AppConfig, to=AppConfig(config), scope=singleton)
    
    # Bind services
    storage_type = config.get('STORAGE_TYPE', 'local')  # Default to 'local' if not specified
    if storage_type == 'gcp':
        binder.bind(GCPStorageService, to=GCPStorageService, scope=singleton)
        # Bind the storage service interface to the GCP implementation
        binder.bind(StorageServiceInterface, to=GCPStorageService, scope=singleton)
    else:  # 'local'
        binder.bind(LocalStorageService, to=LocalStorageService, scope=singleton)
        # Bind the storage service interface to the local implementation
        binder.bind(StorageServiceInterface, to=LocalStorageService, scope=singleton)
        
    binder.bind(PubDevService, to=PubDevService, scope=singleton)
    
    # Bind repositories
    binder.bind(PackageRepository, to=PackageRepository, scope=singleton)
    
    # Bind use cases
    binder.bind(ProxyPackageUseCase, to=ProxyPackageUseCase, scope=singleton)
    binder.bind(UploadPackageUseCase, to=UploadPackageUseCase, scope=singleton)
    binder.bind(DownloadPackageUseCase, to=DownloadPackageUseCase, scope=singleton)
    binder.bind(ListPackagesUseCase, to=ListPackagesUseCase, scope=singleton)
    
    # Bind auth service
    binder.bind(AuthService, to=AuthService, scope=singleton)