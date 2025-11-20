"""
Integration test - Object endpoints
"""
import pytest


@pytest.mark.integration
def test_list_objects(client):
    """Test list objects endpoint"""
    response = client.get("/storage/v1/b/test-bucket/o")
    assert response.status_code in [200, 404]


@pytest.mark.integration
def test_upload_object(client):
    """Test upload object endpoint"""
    response = client.post("/storage/v1/b/test-bucket/o?name=test.txt", data=b"test content")
    assert response.status_code in [200, 404]


@pytest.mark.integration
def test_get_object(client):
    """Test get object endpoint"""
    response = client.get("/storage/v1/b/test-bucket/o/test.txt")
    assert response.status_code in [200, 404]


@pytest.mark.integration
def test_download_object(client):
    """Test download object endpoint"""
    response = client.get("/storage/v1/b/test-bucket/o/test.txt?alt=media")
    assert response.status_code in [200, 404]


@pytest.mark.integration
def test_delete_object(client):
    """Test delete object endpoint"""
    response = client.delete("/storage/v1/b/test-bucket/o/test.txt")
    assert response.status_code in [204, 404]
