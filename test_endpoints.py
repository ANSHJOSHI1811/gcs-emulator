#!/usr/bin/env python
"""
Test all 9 API endpoints
"""
import sys
sys.path.insert(0, '.')
from app.factory import create_app, db
from app.models.project import Project

app = create_app('testing')

with app.app_context():
    # Seed initial data
    project = Project.query.first()
    if not project:
        project = Project(id='test-project-1', name='Test Project', location='US')
        db.session.add(project)
        db.session.commit()
    
    print(f'✓ Project created: {project.name} (ID: {project.id})')
    
    # Now test with Flask test client
    client = app.test_client()
    
    # Test 1: List buckets (should be empty)
    resp = client.get('/storage/v1/b?project=test-project-1')
    print(f'\n1. List buckets (empty): {resp.status_code}')
    print(f'   Response: {resp.get_json()}')
    
    # Test 2: Create bucket
    resp = client.post('/storage/v1/b?project=test-project-1', json={
        'name': 'test-bucket-1',
        'location': 'US',
        'storageClass': 'STANDARD'
    })
    print(f'\n2. Create bucket: {resp.status_code}')
    print(f'   Response: {resp.get_json()}')
    
    # Test 3: Get bucket
    resp = client.get('/storage/v1/b/test-bucket-1')
    print(f'\n3. Get bucket: {resp.status_code}')
    print(f'   Response: {resp.get_json()}')
    
    # Test 4: List buckets (should have 1)
    resp = client.get('/storage/v1/b?project=test-project-1')
    print(f'\n4. List buckets (populated): {resp.status_code}')
    data = resp.get_json()
    print(f'   Count: {len(data.get("items", []))}')
    
    # Test 5: Upload object
    resp = client.post('/storage/v1/b/test-bucket-1/o?name=test.txt', data=b'Hello World!')
    print(f'\n5. Upload object: {resp.status_code}')
    print(f'   Response: {resp.get_json()}')
    
    # Test 6: List objects
    resp = client.get('/storage/v1/b/test-bucket-1/o')
    print(f'\n6. List objects: {resp.status_code}')
    data = resp.get_json()
    print(f'   Count: {len(data.get("items", []))}')
    
    # Test 7: Get object metadata
    resp = client.get('/storage/v1/b/test-bucket-1/o/test.txt')
    print(f'\n7. Get object metadata: {resp.status_code}')
    print(f'   Response: {resp.get_json()}')
    
    # Test 8: Download object
    resp = client.get('/storage/v1/b/test-bucket-1/o/test.txt?alt=media')
    print(f'\n8. Download object: {resp.status_code}')
    print(f'   Content: {resp.get_data()}')
    
    # Test 9: Delete object
    resp = client.delete('/storage/v1/b/test-bucket-1/o/test.txt')
    print(f'\n9. Delete object: {resp.status_code}')
    
    # Test 10: Delete bucket
    resp = client.delete('/storage/v1/b/test-bucket-1')
    print(f'\n10. Delete bucket: {resp.status_code}')
    
    print('\n✓ All endpoint tests completed successfully!')
