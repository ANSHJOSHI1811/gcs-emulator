"""Integration tests for Secret Manager API."""

import json
import requests
import pytest
from typing import Dict, Any


BASE_URL = "http://localhost:8080"
PROJECT = "test-project"
PYTEST_TIMEOUT = 10


class TestSecretManager:
    """Secret Manager integration tests."""
    
    @pytest.fixture(autouse=True)
    def setup_teardown(self):
        """Setup and teardown for each test."""
        # Health check
        response = requests.get(f"{BASE_URL}/v1/secretmanager/health", timeout=PYTEST_TIMEOUT)
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        yield
        # Cleanup handled by storage
    
    def test_01_create_secret(self):
        """Test creating a new secret."""
        response = requests.post(
            f"{BASE_URL}/v1/projects/{PROJECT}/secrets",
            json={
                "secretId": "my-api-key",
                "description": "API key for service",
                "labels": {
                    "env": "prod",
                    "app": "myservice"
                },
                "replication": {
                    "automatic": {}
                }
            },
            timeout=PYTEST_TIMEOUT
        )
        
        assert response.status_code == 200, f"Error: {response.text}"
        data = response.json()
        assert data["name"]
        assert "my-api-key" in data["name"]
        assert data["description"] == "API key for service"
        assert data["labels"]["env"] == "prod"
        print(f"✅ Secret created: {data['name']}")
    
    def test_02_add_secret_version(self):
        """Test adding a version to a secret."""
        # Create secret first
        requests.post(
            f"{BASE_URL}/v1/projects/{PROJECT}/secrets",
            json={"secretId": "db-password"},
            timeout=PYTEST_TIMEOUT
        )
        
        # Add version
        response = requests.post(
            f"{BASE_URL}/v1/projects/{PROJECT}/secrets/db-password:addVersion",
            json={
                "payload": {
                    "data": "super-secret-password-123"
                }
            },
            timeout=PYTEST_TIMEOUT
        )
        
        assert response.status_code == 200, f"Error: {response.text}"
        data = response.json()
        assert data["name"]
        assert data["state"] == "ENABLED"
        print(f"✅ Version added: {data['name']}")
    
    def test_03_list_secrets(self):
        """Test listing all secrets in project."""
        # Create a couple of secrets
        requests.post(
            f"{BASE_URL}/v1/projects/{PROJECT}/secrets",
            json={"secretId": "secret-1"},
            timeout=PYTEST_TIMEOUT
        )
        requests.post(
            f"{BASE_URL}/v1/projects/{PROJECT}/secrets",
            json={"secretId": "secret-2"},
            timeout=PYTEST_TIMEOUT
        )
        
        response = requests.get(
            f"{BASE_URL}/v1/projects/{PROJECT}/secrets",
            timeout=PYTEST_TIMEOUT
        )
        
        assert response.status_code == 200, f"Error: {response.text}"
        data = response.json()
        assert isinstance(data["secrets"], list)
        assert len(data["secrets"]) >= 2
        print(f"✅ Found {len(data['secrets'])} secrets")
    
    def test_04_get_secret(self):
        """Test getting a specific secret."""
        # Create secret
        requests.post(
            f"{BASE_URL}/v1/projects/{PROJECT}/secrets",
            json={
                "secretId": "get-test",
                "description": "Test secret"
            },
            timeout=PYTEST_TIMEOUT
        )
        
        response = requests.get(
            f"{BASE_URL}/v1/projects/{PROJECT}/secrets/get-test",
            timeout=PYTEST_TIMEOUT
        )
        
        assert response.status_code == 200, f"Error: {response.text}"
        data = response.json()
        assert "get-test" in data["name"]
        assert data["description"] == "Test secret"
        print(f"✅ Secret retrieved: {data['name']}")
    
    def test_05_list_versions(self):
        """Test listing secret versions."""
        # Create secret and add multiple versions
        requests.post(
            f"{BASE_URL}/v1/projects/{PROJECT}/secrets",
            json={"secretId": "multi-version"},
            timeout=PYTEST_TIMEOUT
        )
        
        # Add 3 versions
        for i in range(3):
            requests.post(
                f"{BASE_URL}/v1/projects/{PROJECT}/secrets/multi-version:addVersion",
                json={"payload": {"data": f"version-{i}"}},
                timeout=PYTEST_TIMEOUT
            )
        
        response = requests.get(
            f"{BASE_URL}/v1/projects/{PROJECT}/secrets/multi-version/versions",
            timeout=PYTEST_TIMEOUT
        )
        
        assert response.status_code == 200, f"Error: {response.text}"
        data = response.json()
        assert len(data["versions"]) == 3
        print(f"✅ Found {len(data['versions'])} versions")
    
    def test_06_access_secret_latest(self):
        """Test accessing the latest version of a secret."""
        # Create secret and add version
        requests.post(
            f"{BASE_URL}/v1/projects/{PROJECT}/secrets",
            json={"secretId": "access-test"},
            timeout=PYTEST_TIMEOUT
        )
        requests.post(
            f"{BASE_URL}/v1/projects/{PROJECT}/secrets/access-test:addVersion",
            json={"payload": {"data": "secret-data-123"}},
            timeout=PYTEST_TIMEOUT
        )
        
        response = requests.post(
            f"{BASE_URL}/v1/projects/{PROJECT}/secrets/access-test/versions/latest:access",
            timeout=PYTEST_TIMEOUT
        )
        
        assert response.status_code == 200, f"Error: {response.text}"
        data = response.json()
        assert data["payload"]["data"] == "secret-data-123"
        print(f"✅ Latest version accessed")
    
    def test_07_access_secret_by_version_id(self):
        """Test accessing a specific version by ID."""
        # Create secret and add version
        requests.post(
            f"{BASE_URL}/v1/projects/{PROJECT}/secrets",
            json={"secretId": "version-id-test"},
            timeout=PYTEST_TIMEOUT
        )
        
        version_response = requests.post(
            f"{BASE_URL}/v1/projects/{PROJECT}/secrets/version-id-test:addVersion",
            json={"payload": {"data": "specific-version"}},
            timeout=PYTEST_TIMEOUT
        )
        version_id = version_response.json()["name"].split("/")[-1]
        
        response = requests.post(
            f"{BASE_URL}/v1/projects/{PROJECT}/secrets/version-id-test/versions/{version_id}:access",
            timeout=PYTEST_TIMEOUT
        )
        
        assert response.status_code == 200, f"Error: {response.text}"
        data = response.json()
        assert data["payload"]["data"] == "specific-version"
        print(f"✅ Specific version accessed: {version_id}")
    
    def test_08_disable_version(self):
        """Test disabling a secret version."""
        # Create secret and add version
        requests.post(
            f"{BASE_URL}/v1/projects/{PROJECT}/secrets",
            json={"secretId": "disable-test"},
            timeout=PYTEST_TIMEOUT
        )
        version_response = requests.post(
            f"{BASE_URL}/v1/projects/{PROJECT}/secrets/disable-test:addVersion",
            json={"payload": {"data": "test"}},
            timeout=PYTEST_TIMEOUT
        )
        version_id = version_response.json()["name"].split("/")[-1]
        
        response = requests.post(
            f"{BASE_URL}/v1/projects/{PROJECT}/secrets/disable-test/versions/{version_id}:disable",
            timeout=PYTEST_TIMEOUT
        )
        
        assert response.status_code == 200, f"Error: {response.text}"
        data = response.json()
        assert data["state"] == "DISABLED"
        print(f"✅ Version disabled: {version_id}")
    
    def test_09_enable_version(self):
        """Test enabling a disabled secret version."""
        # Create secret and add version
        requests.post(
            f"{BASE_URL}/v1/projects/{PROJECT}/secrets",
            json={"secretId": "enable-test"},
            timeout=PYTEST_TIMEOUT
        )
        version_response = requests.post(
            f"{BASE_URL}/v1/projects/{PROJECT}/secrets/enable-test:addVersion",
            json={"payload": {"data": "test"}},
            timeout=PYTEST_TIMEOUT
        )
        version_id = version_response.json()["name"].split("/")[-1]
        
        # Disable
        requests.post(
            f"{BASE_URL}/v1/projects/{PROJECT}/secrets/enable-test/versions/{version_id}:disable",
            timeout=PYTEST_TIMEOUT
        )
        
        # Enable
        response = requests.post(
            f"{BASE_URL}/v1/projects/{PROJECT}/secrets/enable-test/versions/{version_id}:enable",
            timeout=PYTEST_TIMEOUT
        )
        
        assert response.status_code == 200, f"Error: {response.text}"
        data = response.json()
        assert data["state"] == "ENABLED"
        print(f"✅ Version enabled: {version_id}")
    
    def test_10_destroy_version(self):
        """Test destroying (permanently deleting) a version."""
        # Create secret and add version
        requests.post(
            f"{BASE_URL}/v1/projects/{PROJECT}/secrets",
            json={"secretId": "destroy-test"},
            timeout=PYTEST_TIMEOUT
        )
        version_response = requests.post(
            f"{BASE_URL}/v1/projects/{PROJECT}/secrets/destroy-test:addVersion",
            json={"payload": {"data": "test"}},
            timeout=PYTEST_TIMEOUT
        )
        version_id = version_response.json()["name"].split("/")[-1]
        
        response = requests.post(
            f"{BASE_URL}/v1/projects/{PROJECT}/secrets/destroy-test/versions/{version_id}:destroy",
            timeout=PYTEST_TIMEOUT
        )
        
        assert response.status_code == 200, f"Error: {response.text}"
        data = response.json()
        assert data["state"] == "DESTROYED"
        print(f"✅ Version destroyed: {version_id}")
    
    def test_11_generate_password(self):
        """Test generating a random password."""
        response = requests.post(
            f"{BASE_URL}/v1/generateRandomPassword",
            json={
                "length": 20,
                "includeUppercase": True,
                "includeLowercase": True,
                "includeDigits": True,
                "includeSymbols": False,
            },
            timeout=PYTEST_TIMEOUT
        )
        
        assert response.status_code == 200, f"Error: {response.text}"
        data = response.json()
        assert len(data["password"]) == 20
        assert data["length"] == 20
        print(f"✅ Generated password: {data['password']}")
    
    def test_12_update_secret(self):
        """Test updating secret metadata."""
        # Create secret
        requests.post(
            f"{BASE_URL}/v1/projects/{PROJECT}/secrets",
            json={
                "secretId": "update-test",
                "description": "Old description"
            },
            timeout=PYTEST_TIMEOUT
        )
        
        response = requests.patch(
            f"{BASE_URL}/v1/projects/{PROJECT}/secrets/update-test",
            json={
                "secret": {
                    "description": "New description",
                    "labels": {"version": "2"}
                }
            },
            timeout=PYTEST_TIMEOUT
        )
        
        assert response.status_code == 200, f"Error: {response.text}"
        data = response.json()
        assert data["description"] == "New description"
        print(f"✅ Secret updated")
    
    def test_13_delete_secret(self):
        """Test deleting a secret."""
        # Create secret
        requests.post(
            f"{BASE_URL}/v1/projects/{PROJECT}/secrets",
            json={"secretId": "delete-test"},
            timeout=PYTEST_TIMEOUT
        )
        
        response = requests.delete(
            f"{BASE_URL}/v1/projects/{PROJECT}/secrets/delete-test",
            timeout=PYTEST_TIMEOUT
        )
        
        assert response.status_code == 200, f"Error: {response.text}"
        data = response.json()
        assert data["deleted"] is True
        print(f"✅ Secret deleted")
    
    def test_14_user_managed_replication(self):
        """Test creating secret with user-managed replication."""
        response = requests.post(
            f"{BASE_URL}/v1/projects/{PROJECT}/secrets",
            json={
                "secretId": "user-managed-secret",
                "replication": {
                    "userManaged": {
                        "replicas": [
                            {"location": "us-central1"},
                            {"location": "us-east1"},
                        ]
                    }
                }
            },
            timeout=PYTEST_TIMEOUT
        )
        
        assert response.status_code == 200, f"Error: {response.text}"
        data = response.json()
        assert "userManaged" in data["replication"]
        assert len(data["replication"]["userManaged"]["replicas"]) == 2
        print(f"✅ User-managed replication configured")
    
    def test_15_error_secret_not_found(self):
        """Test error handling for non-existent secret."""
        response = requests.get(
            f"{BASE_URL}/v1/projects/{PROJECT}/secrets/nonexistent",
            timeout=PYTEST_TIMEOUT
        )
        
        assert response.status_code == 404
        print(f"✅ 404 error correctly returned for missing secret")
    
    def test_16_error_duplicate_secret(self):
        """Test error handling for duplicate secret creation."""
        # Create secret
        requests.post(
            f"{BASE_URL}/v1/projects/{PROJECT}/secrets",
            json={"secretId": "duplicate-test"},
            timeout=PYTEST_TIMEOUT
        )
        
        # Try to create duplicate
        response = requests.post(
            f"{BASE_URL}/v1/projects/{PROJECT}/secrets",
            json={"secretId": "duplicate-test"},
            timeout=PYTEST_TIMEOUT
        )
        
        assert response.status_code == 409
        print(f"✅ 409 error correctly returned for duplicate")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
