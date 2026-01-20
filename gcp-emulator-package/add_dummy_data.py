"""
Script to add dummy data to the GCS Emulator for testing and demonstration
"""
import os
import sys
import uuid
from datetime import datetime
from app.factory import create_app, db
from app.models.project import Project
from app.models.bucket import Bucket
from app.models.object import Object, ObjectVersion
import json

def add_dummy_data():
    """Add sample buckets and objects to the emulator"""
    
    print("=" * 80)
    print("Adding Dummy Data to GCS Emulator")
    print("=" * 80)
    
    app = create_app()
    
    with app.app_context():
        # Skip cleanup due to permissions - just add new data
        print("\n[1/5] Skipping cleanup (adding new data)...")
        
        # Create Projects
        print("\n[2/5] Creating projects...")
        projects = [
            Project(id='demo-project', name='Demo Project'),
            Project(id='test-project', name='Test Project'),
            Project(id='production-project', name='Production Project')
        ]
        for project in projects:
            db.session.add(project)
            print(f"  + Created project: {project.id}")
        db.session.commit()
        print("✓ Created 3 projects")
        
        # Create Buckets
        print("\n[3/5] Creating buckets...")
        buckets_data = [
            {
                'project_id': 'demo-project',
                'name': 'demo-images',
                'location': 'US',
                'storage_class': 'STANDARD',
                'versioning_enabled': True,
                'acl': 'private',
                'meta': json.dumps({'purpose': 'Image storage', 'environment': 'demo'})
            },
            {
                'project_id': 'demo-project',
                'name': 'demo-documents',
                'location': 'US',
                'storage_class': 'STANDARD',
                'versioning_enabled': False,
                'acl': 'publicRead',
                'meta': json.dumps({'purpose': 'Document storage', 'environment': 'demo'})
            },
            {
                'project_id': 'test-project',
                'name': 'test-data',
                'location': 'EU',
                'storage_class': 'COLDLINE',
                'versioning_enabled': True,
                'acl': 'private',
                'meta': json.dumps({'purpose': 'Test data', 'environment': 'test'})
            },
            {
                'project_id': 'production-project',
                'name': 'prod-backups',
                'location': 'ASIA',
                'storage_class': 'ARCHIVE',
                'versioning_enabled': True,
                'acl': 'private',
                'meta': json.dumps({'purpose': 'Backups', 'environment': 'production'})
            },
            {
                'project_id': 'demo-project',
                'name': 'demo-logs',
                'location': 'US',
                'storage_class': 'NEARLINE',
                'versioning_enabled': False,
                'acl': 'private',
                'meta': json.dumps({'purpose': 'Application logs', 'environment': 'demo'})
            }
        ]
        
        buckets = []
        for bucket_data in buckets_data:
            # Generate unique bucket ID
            bucket_id = f"{bucket_data['name']}-{uuid.uuid4().hex[:8]}"
            bucket = Bucket(id=bucket_id, **bucket_data)
            db.session.add(bucket)
            buckets.append(bucket)
            print(f"  + Created bucket: {bucket.name} in {bucket.location}")
        db.session.commit()
        print(f"✓ Created {len(buckets)} buckets")
        
        # Create Objects
        print("\n[4/5] Creating objects...")
        
        # Helper function to create storage file
        def create_storage_file(bucket_id, object_name, content):
            storage_dir = os.path.join(app.config.get('STORAGE_ROOT', 'storage'), bucket_id)
            os.makedirs(storage_dir, exist_ok=True)
            file_path = os.path.join(storage_dir, object_name.replace('/', '_'))
            with open(file_path, 'w') as f:
                f.write(content)
            return file_path
        
        objects_data = [
            {
                'bucket': buckets[0],  # demo-images
                'objects': [
                    {'name': 'photos/vacation/beach.jpg', 'content_type': 'image/jpeg', 'content': 'Fake image content - beach photo', 'size': 102400},
                    {'name': 'photos/vacation/sunset.jpg', 'content_type': 'image/jpeg', 'content': 'Fake image content - sunset photo', 'size': 156789},
                    {'name': 'photos/family/birthday.jpg', 'content_type': 'image/jpeg', 'content': 'Fake image content - birthday photo', 'size': 89012},
                    {'name': 'icons/logo.png', 'content_type': 'image/png', 'content': 'Fake PNG logo content', 'size': 45678},
                ]
            },
            {
                'bucket': buckets[1],  # demo-documents
                'objects': [
                    {'name': 'reports/2025/q4-summary.pdf', 'content_type': 'application/pdf', 'content': 'Q4 2025 Summary Report...', 'size': 234567},
                    {'name': 'reports/2026/q1-summary.pdf', 'content_type': 'application/pdf', 'content': 'Q1 2026 Summary Report...', 'size': 245678},
                    {'name': 'contracts/vendor-agreement.docx', 'content_type': 'application/vnd.openxmlformats-officedocument.wordprocessingml.document', 'content': 'Vendor Agreement Document...', 'size': 67890},
                    {'name': 'presentations/company-overview.pptx', 'content_type': 'application/vnd.openxmlformats-officedocument.presentationml.presentation', 'content': 'Company Overview Slides...', 'size': 345678},
                ]
            },
            {
                'bucket': buckets[2],  # test-data
                'objects': [
                    {'name': 'datasets/users.csv', 'content_type': 'text/csv', 'content': 'id,name,email\n1,John Doe,john@example.com\n2,Jane Smith,jane@example.com', 'size': 1024},
                    {'name': 'datasets/transactions.json', 'content_type': 'application/json', 'content': '{"transactions": [{"id": 1, "amount": 100}, {"id": 2, "amount": 200}]}', 'size': 2048},
                    {'name': 'configs/test-config.yaml', 'content_type': 'application/x-yaml', 'content': 'environment: test\napi_url: https://api.test.com', 'size': 512},
                ]
            },
            {
                'bucket': buckets[3],  # prod-backups
                'objects': [
                    {'name': 'database/backup-2026-01-09.sql.gz', 'content_type': 'application/gzip', 'content': 'Compressed SQL backup...', 'size': 1048576},
                    {'name': 'database/backup-2026-01-08.sql.gz', 'content_type': 'application/gzip', 'content': 'Compressed SQL backup...', 'size': 1024000},
                    {'name': 'files/backup-2026-01-09.tar.gz', 'content_type': 'application/gzip', 'content': 'Compressed file backup...', 'size': 2097152},
                ]
            },
            {
                'bucket': buckets[4],  # demo-logs
                'objects': [
                    {'name': 'app/2026-01-10.log', 'content_type': 'text/plain', 'content': '[2026-01-10 12:00:00] INFO: Application started\n[2026-01-10 12:05:00] INFO: Request processed', 'size': 4096},
                    {'name': 'app/2026-01-09.log', 'content_type': 'text/plain', 'content': '[2026-01-09 12:00:00] INFO: Application started\n[2026-01-09 18:00:00] INFO: Application stopped', 'size': 8192},
                    {'name': 'nginx/access.log', 'content_type': 'text/plain', 'content': '192.168.1.1 - - [10/Jan/2026:12:00:00] "GET /api/health HTTP/1.1" 200', 'size': 512},
                ]
            }
        ]
        
        total_objects = 0
        for bucket_objects in objects_data:
            bucket = bucket_objects['bucket']
            for obj_data in bucket_objects['objects']:
                # Create storage file
                storage_path = create_storage_file(bucket.id, obj_data['name'], obj_data['content'])
                
                # Create Object record
                obj = Object(
                    id=f"{bucket.id}/{obj_data['name']}",
                    bucket_id=bucket.id,
                    name=obj_data['name'],
                    size=obj_data['size'],
                    content_type=obj_data['content_type'],
                    md5_hash='d41d8cd98f00b204e9800998ecf8427e',  # Placeholder MD5
                    crc32c_hash='AAAAAA==',  # Placeholder CRC32C
                    storage_class=bucket.storage_class,
                    generation=1,
                    metageneration=1,
                    file_path=storage_path,
                    is_latest=True,
                    deleted=False
                )
                db.session.add(obj)
                
                # Create ObjectVersion record
                obj_version = ObjectVersion(
                    id=f"{bucket.id}/{obj_data['name']}/1",
                    object_id=f"{bucket.id}/{obj_data['name']}",
                    bucket_id=bucket.id,
                    name=obj_data['name'],
                    generation=1,
                    size=obj_data['size'],
                    content_type=obj_data['content_type'],
                    md5_hash='d41d8cd98f00b204e9800998ecf8427e',
                    crc32c_hash='AAAAAA==',
                    file_path=storage_path
                )
                db.session.add(obj_version)
                
                total_objects += 1
                print(f"  + Created object: {bucket.name}/{obj_data['name']} ({obj_data['size']} bytes)")
        
        db.session.commit()
        print(f"✓ Created {total_objects} objects across {len(buckets)} buckets")
        
        # Summary
        print("\n[5/5] Summary:")
        print(f"  • Projects: {Project.query.count()}")
        print(f"  • Buckets: {Bucket.query.count()}")
        print(f"  • Objects: {Object.query.count()}")
        print(f"  • Object Versions: {ObjectVersion.query.count()}")
        
        print("\n" + "=" * 80)
        print("✓ Dummy data successfully added!")
        print("=" * 80)
        print("\nYou can now:")
        print("  1. View buckets: curl http://127.0.0.1:8080/storage/v1/b")
        print("  2. List objects: curl 'http://127.0.0.1:8080/storage/v1/b/demo-images/o'")
        print("  3. Access the UI: http://localhost:3000")
        print("=" * 80)

if __name__ == '__main__':
    add_dummy_data()
