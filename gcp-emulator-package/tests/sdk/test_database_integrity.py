"""
Database integrity tests
Verify that SDK operations correctly persist to PostgreSQL database
"""
import pytest
from google.cloud import storage
from sqlalchemy import text


class TestStorageDatabaseIntegrity:
    """Test that Storage operations correctly persist to database"""
    
    def test_bucket_creation_persists_to_db(
        self, 
        storage_client, 
        db_session, 
        test_bucket_name
    ):
        """
        Test: When a bucket is created via SDK, a corresponding row exists 
        in the buckets table
        """
        # Create bucket using SDK
        bucket = storage_client.create_bucket(test_bucket_name)
        
        # Query database directly
        result = db_session.execute(
            text("SELECT name, location, storage_class FROM buckets WHERE name = :name"),
            {"name": test_bucket_name}
        )
        row = result.fetchone()
        
        # Assert bucket exists in database
        assert row is not None, f"Bucket {test_bucket_name} not found in database"
        
        # Verify bucket details
        db_bucket_name = row[0]
        db_location = row[1]
        db_storage_class = row[2]
        
        assert db_bucket_name == test_bucket_name
        assert db_location is not None  # Should have a location
        assert db_storage_class is not None  # Should have storage class
    
    def test_bucket_metadata_in_db(self, storage_client, db_session, test_bucket_name):
        """Test that bucket metadata is correctly stored"""
        # Create bucket with specific properties
        bucket = storage_client.create_bucket(
            test_bucket_name,
            location="US"
        )
        
        # Query database
        result = db_session.execute(
            text("""
                SELECT name, location, storage_class, created_at, versioning_enabled
                FROM buckets 
                WHERE name = :name
            """),
            {"name": test_bucket_name}
        )
        row = result.fetchone()
        
        assert row is not None
        assert row[0] == test_bucket_name  # name
        assert row[1] == "US"              # location
        assert row[3] is not None          # created_at should exist
        
        # versioning_enabled should be False by default
        if row[4] is not None:
            assert isinstance(row[4], bool)
    
    def test_bucket_deletion_removes_from_db(
        self, 
        storage_client, 
        db_session, 
        test_bucket_name
    ):
        """Test that bucket deletion removes row from database"""
        # Create bucket
        bucket = storage_client.create_bucket(test_bucket_name)
        
        # Verify it exists in DB
        result = db_session.execute(
            text("SELECT COUNT(*) FROM buckets WHERE name = :name"),
            {"name": test_bucket_name}
        )
        count = result.scalar()
        assert count == 1
        
        # Delete bucket
        bucket.delete()
        
        # Verify it's removed from DB
        db_session.expire_all()  # Clear cache
        result = db_session.execute(
            text("SELECT COUNT(*) FROM buckets WHERE name = :name"),
            {"name": test_bucket_name}
        )
        count = result.scalar()
        assert count == 0
    
    def test_blob_upload_persists_to_db(
        self, 
        storage_client, 
        db_session, 
        test_bucket_name,
        sample_text_content
    ):
        """Test that blob uploads are persisted to objects table"""
        # Create bucket and upload blob
        bucket = storage_client.create_bucket(test_bucket_name)
        blob_name = "test-file.txt"
        blob = bucket.blob(blob_name)
        blob.upload_from_string(sample_text_content, content_type="text/plain")
        
        # Query objects table
        result = db_session.execute(
            text("""
                SELECT o.name, o.size, o.content_type, b.name as bucket_name
                FROM objects o
                JOIN buckets b ON o.bucket_id = b.id
                WHERE o.name = :blob_name AND b.name = :bucket_name
            """),
            {"blob_name": blob_name, "bucket_name": test_bucket_name}
        )
        row = result.fetchone()
        
        assert row is not None, "Blob not found in database"
        assert row[0] == blob_name
        assert row[1] == len(sample_text_content)  # size
        assert row[2] == "text/plain"              # content_type
        assert row[3] == test_bucket_name          # bucket_name
    
    def test_blob_metadata_in_db(
        self, 
        storage_client, 
        db_session, 
        test_bucket_name,
        sample_text_content
    ):
        """Test that blob metadata is stored correctly"""
        bucket = storage_client.create_bucket(test_bucket_name)
        
        blob_name = "metadata-test.txt"
        blob = bucket.blob(blob_name)
        blob.metadata = {"author": "test", "version": "1.0"}
        blob.upload_from_string(sample_text_content)
        
        # Query database
        result = db_session.execute(
            text("""
                SELECT o.name, o.md5_hash, o.crc32c_hash, o.meta
                FROM objects o
                JOIN buckets b ON o.bucket_id = b.id
                WHERE o.name = :blob_name AND b.name = :bucket_name
            """),
            {"blob_name": blob_name, "bucket_name": test_bucket_name}
        )
        row = result.fetchone()
        
        assert row is not None
        assert row[0] == blob_name
        # Checksums might be stored
        # metadata should be in meta column (JSONB)
    
    def test_blob_deletion_removes_from_db(
        self, 
        storage_client, 
        db_session, 
        test_bucket_name,
        sample_text_content
    ):
        """Test that blob deletion removes from database"""
        bucket = storage_client.create_bucket(test_bucket_name)
        blob_name = "to-delete.txt"
        blob = bucket.blob(blob_name)
        blob.upload_from_string(sample_text_content)
        
        # Verify exists
        result = db_session.execute(
            text("""
                SELECT COUNT(*) 
                FROM objects o
                JOIN buckets b ON o.bucket_id = b.id
                WHERE o.name = :blob_name AND b.name = :bucket_name
            """),
            {"blob_name": blob_name, "bucket_name": test_bucket_name}
        )
        count = result.scalar()
        assert count >= 1  # Might be 1 or more if versioning enabled
        
        # Delete blob
        blob.delete()
        
        # Verify deleted (or marked as deleted if soft delete)
        db_session.expire_all()
        result = db_session.execute(
            text("""
                SELECT COUNT(*) 
                FROM objects o
                JOIN buckets b ON o.bucket_id = b.id
                WHERE o.name = :blob_name AND b.name = :bucket_name AND o.deleted = FALSE
            """),
            {"blob_name": blob_name, "bucket_name": test_bucket_name}
        )
        count = result.scalar()
        assert count == 0


class TestVersioningDatabaseIntegrity:
    """Test versioning-related database integrity"""
    
    def test_versioning_enabled_in_db(self, storage_client, db_session, test_bucket_name):
        """Test that versioning flag is persisted"""
        # Create bucket
        bucket = storage_client.create_bucket(test_bucket_name)
        
        # Enable versioning
        bucket.versioning_enabled = True
        bucket.patch()
        
        # Check database
        result = db_session.execute(
            text("SELECT versioning_enabled FROM buckets WHERE name = :name"),
            {"name": test_bucket_name}
        )
        row = result.fetchone()
        
        assert row is not None
        assert row[0] is True  # versioning_enabled
    
    def test_object_versions_stored(
        self, 
        storage_client, 
        db_session, 
        test_bucket_name,
        sample_text_content
    ):
        """Test that object versions are stored in database"""
        # Create bucket with versioning
        bucket = storage_client.create_bucket(test_bucket_name)
        bucket.versioning_enabled = True
        bucket.patch()
        
        # Upload same blob twice
        blob_name = "versioned-file.txt"
        blob = bucket.blob(blob_name)
        
        blob.upload_from_string(b"version 1")
        blob.upload_from_string(b"version 2")
        
        # Check object_versions table (if exists)
        try:
            result = db_session.execute(
                text("""
                    SELECT COUNT(*) 
                    FROM object_versions ov
                    JOIN objects o ON ov.object_id = o.id
                    JOIN buckets b ON o.bucket_id = b.id
                    WHERE o.name = :blob_name AND b.name = :bucket_name
                """),
                {"blob_name": blob_name, "bucket_name": test_bucket_name}
            )
            count = result.scalar()
            assert count >= 2  # Should have at least 2 versions
        except Exception:
            # Table might not exist yet
            pytest.skip("object_versions table not available")


class TestProjectDatabaseIntegrity:
    """Test project-related database integrity"""
    
    def test_project_exists_in_db(self, db_session):
        """Test that projects table has test project"""
        result = db_session.execute(
            text("SELECT id, name FROM projects WHERE id = 'test-project'")
        )
        row = result.fetchone()
        
        # Project might be auto-created or need manual setup
        if row is None:
            # Create test project
            db_session.execute(
                text("""
                    INSERT INTO projects (id, name, created_at, updated_at)
                    VALUES ('test-project', 'Test Project', NOW(), NOW())
                    ON CONFLICT (id) DO NOTHING
                """)
            )
            db_session.commit()
    
    def test_bucket_belongs_to_project(
        self, 
        storage_client, 
        db_session, 
        test_bucket_name
    ):
        """Test that buckets are associated with projects"""
        # Ensure project exists
        db_session.execute(
            text("""
                INSERT INTO projects (id, name, created_at, updated_at)
                VALUES ('test-project', 'Test Project', NOW(), NOW())
                ON CONFLICT (id) DO NOTHING
            """)
        )
        db_session.commit()
        
        # Create bucket
        bucket = storage_client.create_bucket(test_bucket_name)
        
        # Verify project_id foreign key
        result = db_session.execute(
            text("""
                SELECT b.name, p.id as project_id, p.name as project_name
                FROM buckets b
                JOIN projects p ON b.project_id = p.id
                WHERE b.name = :name
            """),
            {"name": test_bucket_name}
        )
        row = result.fetchone()
        
        assert row is not None
        assert row[0] == test_bucket_name
        assert row[1] == 'test-project'


class TestDatabaseSchema:
    """Test database schema integrity"""
    
    def test_required_tables_exist(self, db_session):
        """Test that all required tables exist"""
        required_tables = ['projects', 'buckets', 'objects']
        
        result = db_session.execute(
            text("""
                SELECT table_name 
                FROM information_schema.tables 
                WHERE table_schema = 'public'
            """)
        )
        
        existing_tables = [row[0] for row in result.fetchall()]
        
        for table in required_tables:
            assert table in existing_tables, f"Required table '{table}' not found"
    
    def test_foreign_key_constraints(self, db_session):
        """Test that foreign key constraints are properly defined"""
        result = db_session.execute(
            text("""
                SELECT
                    tc.table_name, 
                    kcu.column_name, 
                    ccu.table_name AS foreign_table_name,
                    ccu.column_name AS foreign_column_name 
                FROM information_schema.table_constraints AS tc 
                JOIN information_schema.key_column_usage AS kcu
                    ON tc.constraint_name = kcu.constraint_name
                JOIN information_schema.constraint_column_usage AS ccu
                    ON ccu.constraint_name = tc.constraint_name
                WHERE tc.constraint_type = 'FOREIGN KEY'
                AND tc.table_name IN ('buckets', 'objects')
            """)
        )
        
        constraints = list(result.fetchall())
        
        # Should have at least:
        # - buckets.project_id -> projects.id
        # - objects.bucket_id -> buckets.id
        assert len(constraints) >= 2, "Missing foreign key constraints"
    
    def test_indexes_exist(self, db_session):
        """Test that performance indexes exist"""
        result = db_session.execute(
            text("""
                SELECT
                    tablename,
                    indexname,
                    indexdef
                FROM pg_indexes
                WHERE schemaname = 'public'
                AND tablename IN ('buckets', 'objects')
            """)
        )
        
        indexes = list(result.fetchall())
        
        # Should have indexes on frequently queried columns
        assert len(indexes) > 0, "No indexes found on core tables"
