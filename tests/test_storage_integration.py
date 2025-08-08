import unittest
from unittest.mock import patch
from injector import Injector

from pub_proxy.infrastructure.container import configure_container
from pub_proxy.infrastructure.services.gcp_storage_service import GCPStorageService
from pub_proxy.infrastructure.services.local_storage_service import LocalStorageService
from pub_proxy.core.interfaces.storage_service_interface import StorageServiceInterface


class TestStorageIntegration(unittest.TestCase):
    """Test cases for storage service integration with the dependency injection container."""

    @patch('pub_proxy.infrastructure.services.gcp_storage_service.storage.Client')
    def test_gcp_storage_binding(self, mock_client):
        """Test that GCPStorageService is bound when STORAGE_TYPE is 'gcp'."""
        # Mock the GCP client
        mock_bucket = mock_client.return_value.bucket.return_value
        mock_bucket.exists.return_value = True

        # Configure the container with GCP storage type
        config = {
            'STORAGE_TYPE': 'gcp',
            'GCP_BUCKET_NAME': 'test-bucket',
            'GCP_PROJECT_ID': 'test-project'
        }
        injector = Injector([lambda binder: configure_container(binder, config)])

        # Get the storage service
        storage_service = injector.get(StorageServiceInterface)

        # Check that it's a GCPStorageService
        self.assertIsInstance(storage_service, GCPStorageService)
        self.assertEqual(storage_service.bucket_name, 'test-bucket')
        self.assertEqual(storage_service.project_id, 'test-project')

    def test_local_storage_binding(self):
        """Test that LocalStorageService is bound when STORAGE_TYPE is 'local'."""
        # Configure the container with local storage type
        config = {
            'STORAGE_TYPE': 'local',
            'LOCAL_STORAGE_DIR': './test-storage'
        }
        injector = Injector([lambda binder: configure_container(binder, config)])

        # Get the storage service
        storage_service = injector.get(StorageServiceInterface)

        # Check that it's a LocalStorageService
        self.assertIsInstance(storage_service, LocalStorageService)
        self.assertEqual(storage_service.storage_dir, './test-storage')

    def test_default_local_storage_binding(self):
        """Test that LocalStorageService is bound by default when STORAGE_TYPE is not specified."""
        # Configure the container without specifying storage type
        config = {
            'LOCAL_STORAGE_DIR': './default-storage'
        }
        injector = Injector([lambda binder: configure_container(binder, config)])

        # Get the storage service
        storage_service = injector.get(StorageServiceInterface)

        # Check that it's a LocalStorageService
        self.assertIsInstance(storage_service, LocalStorageService)
        self.assertEqual(storage_service.storage_dir, './default-storage')


if __name__ == '__main__':
    unittest.main()