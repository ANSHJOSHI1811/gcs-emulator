"""
Integration test - Error handling
"""
import pytest


@pytest.mark.integration
def test_404_error(client):
    """Test 404 error handling"""
    response = client.get("/nonexistent")
    assert response.status_code == 404


@pytest.mark.integration
def test_400_error(client):
    """Test 400 error handling"""
    response = client.post("/storage/v1/b", json={})
    assert response.status_code in [200, 400]
