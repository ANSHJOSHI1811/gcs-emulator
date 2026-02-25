"""BaseTester class for all test suites"""
import pytest
import os
from .api_client import APIClient
from .gcloud_runner import GCloudRunner


class BaseTester:
    """Base class for all test suites"""
    
    @pytest.fixture(scope="function", autouse=True)
    def setup_tester(self):
        """Setup API and gcloud clients"""
        self.api = APIClient()
        
        # Check if gcloud is available and should be tested
        self.gcloud_enabled = os.getenv("ENABLE_GCLOUD_TESTS", "true").lower() == "true"
        
        if self.gcloud_enabled:
            self.gcloud = GCloudRunner()
            if not self.gcloud.gcloud_available:
                pytest.skip("gcloud CLI not available")
        else:
            self.gcloud = None
        
        yield
        
        # Cleanup
        self.api.close()
    
    def skip_if_no_gcloud(self):
        """Skip test if gcloud is not available"""
        if not self.gcloud_enabled or self.gcloud is None:
            pytest.skip("gcloud not enabled or available")
    
    def skip_if_no_api(self):
        """Skip test if API is not available"""
        if not self.api:
            pytest.skip("API client not available")
    
    # Assertion helpers
    def assert_success(self, response, status_code: int = 200):
        """Assert API response is successful"""
        assert response.status_code == status_code, \
            f"Expected {status_code}, got {response.status_code}: {response.text}"
    
    def assert_not_found(self, response):
        """Assert API response is 404"""
        assert response.status_code == 404, \
            f"Expected 404, got {response.status_code}: {response.text}"
    
    def assert_bad_request(self, response):
        """Assert API response is 400"""
        assert response.status_code == 400, \
            f"Expected 400, got {response.status_code}: {response.text}"
    
    def assert_conflict(self, response):
        """Assert API response is 409"""
        assert response.status_code == 409, \
            f"Expected 409, got {response.status_code}: {response.text}"
    
    # Cleanup helpers
    def cleanup_resource(self, resource_id: str, endpoint: str):
        """Generic resource cleanup"""
        try:
            self.api.delete(f"{endpoint}/{resource_id}")
        except Exception:
            pass
    
    def cleanup_project(self, project_id: str):
        """Clean up a project"""
        try:
            self.api.delete(f"/cloudresourcemanager/v1/projects/{project_id}")
        except Exception:
            pass
