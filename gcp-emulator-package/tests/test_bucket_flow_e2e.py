"""
End-to-End Test - Bucket Flow with Logging Validation

Tests the complete pipeline from HTTP request to database persistence,
validating responses, database state, and logging at each stage.
"""
import logging
import pytest
from app.factory import db
from app.models.bucket import Bucket
from app.models.object import Object


def test_create_bucket_success(client, caplog):
    """Test successful bucket creation with full pipeline validation."""
    with caplog.at_level(logging.INFO):
        response = client.post(
            '/storage/v1/b?project=test-project',
            json={
                'name': 'test-bucket',
                'location': 'US',
                'storageClass': 'STANDARD'
            }
        )
    
    # HTTP response validation
    assert response.status_code == 201
    data = response.get_json()
    assert data['name'] == 'test-bucket'
    assert data['projectNumber'] == 'test-project'
    assert data['location'] == 'US'
    assert data['storageClass'] == 'STANDARD'
    assert 'id' in data
    assert 'timeCreated' in data
    assert 'updated' in data
    
    # Database validation
    bucket = Bucket.query.filter_by(name='test-bucket').first()
    assert bucket is not None
    assert bucket.location == 'US'
    assert bucket.storage_class == 'STANDARD'
    
    # Logging validation
    assert '/storage/v1/b' in caplog.text
    assert 'test-project' in caplog.text


def test_create_bucket_duplicate_conflict(client, caplog):
    """Test duplicate bucket name returns 409 conflict."""
    # Create first bucket
    response1 = client.post(
        '/storage/v1/b?project=test-project',
        json={'name': 'duplicate-bucket', 'location': 'US'}
    )
    assert response1.status_code == 201
    
    # Attempt duplicate creation
    with caplog.at_level(logging.INFO):
        response2 = client.post(
            '/storage/v1/b?project=test-project',
            json={'name': 'duplicate-bucket', 'location': 'US'}
        )
    
    # HTTP response validation
    assert response2.status_code == 409
    data = response2.get_json()
    assert 'error' in data
    assert 'already exists' in data['error']['message'].lower()
    
    # Database validation - only one bucket exists
    buckets = Bucket.query.filter_by(name='duplicate-bucket').all()
    assert len(buckets) == 1
    
    # Logging validation
    assert 'duplicate-bucket' in caplog.text


def test_create_bucket_missing_project_parameter(client, caplog):
    """Test missing project parameter returns 400."""
    with caplog.at_level(logging.INFO):
        response = client.post(
            '/storage/v1/b',
            json={'name': 'orphan-bucket'}
        )
    
    # HTTP response validation
    assert response.status_code == 400
    data = response.get_json()
    assert 'error' in data
    assert 'project' in data['error']['message'].lower()
    
    # Database validation - no bucket created
    bucket = Bucket.query.filter_by(name='orphan-bucket').first()
    assert bucket is None
    
    # Logging validation
    assert '/storage/v1/b' in caplog.text


def test_create_bucket_invalid_name(client, caplog):
    """Test invalid bucket name returns 400."""
    with caplog.at_level(logging.INFO):
        response = client.post(
            '/storage/v1/b?project=test-project',
            json={'name': 'INVALID_UPPERCASE_NAME'}
        )
    
    # HTTP response validation
    assert response.status_code == 400
    data = response.get_json()
    assert 'error' in data
    assert 'invalid' in data['error']['message'].lower()
    
    # Database validation - no bucket created
    bucket = Bucket.query.filter_by(name='INVALID_UPPERCASE_NAME').first()
    assert bucket is None
    
    # Logging validation
    assert 'test-project' in caplog.text


def test_list_buckets_scoped_by_project(client, caplog):
    """Test bucket listing is scoped by project."""
    # Create buckets for project-a
    client.post(
        '/storage/v1/b?project=project-a',
        json={'name': 'project-a-bucket-1'}
    )
    client.post(
        '/storage/v1/b?project=project-a',
        json={'name': 'project-a-bucket-2'}
    )
    
    # Create bucket for project-b
    client.post(
        '/storage/v1/b?project=project-b',
        json={'name': 'project-b-bucket-1'}
    )
    
    # List buckets for project-a
    with caplog.at_level(logging.INFO):
        response_a = client.get('/storage/v1/b?project=project-a')
    
    # HTTP response validation
    assert response_a.status_code == 200
    data_a = response_a.get_json()
    assert data_a['kind'] == 'storage#buckets'
    assert len(data_a['items']) == 2
    for item in data_a['items']:
        assert item['projectNumber'] == 'project-a'
    
    # List buckets for project-b
    response_b = client.get('/storage/v1/b?project=project-b')
    assert response_b.status_code == 200
    data_b = response_b.get_json()
    assert len(data_b['items']) == 1
    assert data_b['items'][0]['projectNumber'] == 'project-b'
    
    # Logging validation
    assert 'project-a' in caplog.text


def test_get_bucket_metadata(client, caplog):
    """Test retrieving bucket metadata."""
    # Create bucket
    client.post(
        '/storage/v1/b?project=test-project',
        json={'name': 'metadata-test-bucket', 'location': 'EU'}
    )
    
    # Get bucket metadata
    with caplog.at_level(logging.INFO):
        response = client.get('/storage/v1/b/metadata-test-bucket')
    
    # HTTP response validation
    assert response.status_code == 200
    data = response.get_json()
    assert data['name'] == 'metadata-test-bucket'
    assert data['location'] == 'EU'
    assert 'id' in data
    assert 'timeCreated' in data
    assert 'updated' in data
    
    # Logging validation
    assert 'metadata-test-bucket' in caplog.text


def test_get_bucket_not_found(client, caplog):
    """Test retrieving nonexistent bucket returns 404."""
    with caplog.at_level(logging.INFO):
        response = client.get('/storage/v1/b/nonexistent-bucket')
    
    # HTTP response validation
    assert response.status_code == 404
    data = response.get_json()
    assert 'error' in data
    assert 'not found' in data['error']['message'].lower()
    
    # Logging validation
    assert 'nonexistent-bucket' in caplog.text


def test_delete_bucket_success(client, caplog):
    """Test successful bucket deletion."""
    # Create bucket
    client.post(
        '/storage/v1/b?project=test-project',
        json={'name': 'delete-test-bucket'}
    )
    
    # Verify bucket exists
    bucket = Bucket.query.filter_by(name='delete-test-bucket').first()
    assert bucket is not None
    
    # Delete bucket
    with caplog.at_level(logging.INFO):
        response = client.delete('/storage/v1/b/delete-test-bucket')
    
    # HTTP response validation
    assert response.status_code == 204
    assert response.data == b''
    
    # Database validation - bucket deleted
    bucket = Bucket.query.filter_by(name='delete-test-bucket').first()
    assert bucket is None
    
    # Logging validation
    assert 'delete-test-bucket' in caplog.text


def test_delete_bucket_not_empty(client, app, caplog):
    """Test deleting non-empty bucket returns 400."""
    # Create bucket
    response = client.post(
        '/storage/v1/b?project=test-project',
        json={'name': 'nonempty-bucket'}
    )
    bucket_id = response.get_json()['id']
    
    # Add object to bucket (direct DB operation)
    with app.app_context():
        obj = Object(
            id='test-object-id',
            bucket_id=bucket_id,
            name='test-file.txt',
            size=100,
            content_type='text/plain',
            file_path='/fake/path'
        )
        db.session.add(obj)
        db.session.commit()
    
    # Attempt to delete non-empty bucket
    with caplog.at_level(logging.INFO):
        response = client.delete('/storage/v1/b/nonempty-bucket')
    
    # HTTP response validation
    assert response.status_code == 400
    data = response.get_json()
    assert 'error' in data
    assert 'not empty' in data['error']['message'].lower()
    
    # Database validation - bucket still exists
    bucket = Bucket.query.filter_by(name='nonempty-bucket').first()
    assert bucket is not None
    
    # Logging validation
    assert 'nonempty-bucket' in caplog.text


def test_full_bucket_lifecycle(client, caplog):
    """Test complete bucket lifecycle: create → get → list → delete."""
    bucket_name = 'lifecycle-test-bucket'
    
    with caplog.at_level(logging.INFO):
        # Step 1: Create bucket
        create_response = client.post(
            '/storage/v1/b?project=lifecycle-project',
            json={'name': bucket_name, 'location': 'ASIA'}
        )
        assert create_response.status_code == 201
        
        # Step 2: Get bucket metadata
        get_response = client.get(f'/storage/v1/b/{bucket_name}')
        assert get_response.status_code == 200
        assert get_response.get_json()['name'] == bucket_name
        
        # Step 3: List buckets (should include our bucket)
        list_response = client.get('/storage/v1/b?project=lifecycle-project')
        assert list_response.status_code == 200
        bucket_names = [b['name'] for b in list_response.get_json()['items']]
        assert bucket_name in bucket_names
        
        # Step 4: Delete bucket
        delete_response = client.delete(f'/storage/v1/b/{bucket_name}')
        assert delete_response.status_code == 204
        
        # Step 5: Verify bucket no longer exists
        final_list = client.get('/storage/v1/b?project=lifecycle-project')
        final_names = [b['name'] for b in final_list.get_json()['items']]
        assert bucket_name not in final_names
    
    # Logging validation - all operations logged
    assert 'POST' in caplog.text
    assert 'GET' in caplog.text
    assert 'DELETE' in caplog.text
    assert bucket_name in caplog.text
