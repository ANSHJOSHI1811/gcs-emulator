"""
Integration test - Bucket endpoints
"""
import pytest


@pytest.mark.integration
def test_list_buckets(client):
    """Test list buckets endpoint"""
    response = client.get("/storage/v1/b")
    assert response.status_code in [200, 401]


@pytest.mark.integration
def test_create_bucket(client):
    """Test create bucket endpoint"""
    response = client.post("/storage/v1/b", json={"name": "test-bucket"})
    assert response.status_code in [200, 400, 409]


@pytest.mark.integration
def test_get_bucket(client):
    """Test get bucket endpoint"""
    response = client.get("/storage/v1/b/test-bucket")
    assert response.status_code in [200, 404]


@pytest.mark.integration
def test_delete_bucket(client):
    """Test delete bucket endpoint"""
    response = client.delete("/storage/v1/b/test-bucket")
    assert response.status_code in [204, 404, 409]
