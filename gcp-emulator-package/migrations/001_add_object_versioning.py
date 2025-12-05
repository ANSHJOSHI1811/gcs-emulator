"""
Migration: Add Object Versioning Support
Date: 2025-12-02
Description: Adds generation, versioning support, and object_versions table
"""

from sqlalchemy import text


def upgrade(db, app):
    """
    Apply migration - add versioning columns and object_versions table
    
    Args:
        db: SQLAlchemy database instance
        app: Flask application
    """
    with app.app_context():
        connection = db.engine.connect()
        trans = connection.begin()
        
        try:
            # Step 1: Add new columns to objects table
            print("Adding generation column to objects table...")
            connection.execute(text("""
                ALTER TABLE objects 
                ADD COLUMN IF NOT EXISTS generation BIGINT DEFAULT 1
            """))
            
            print("Adding is_latest column to objects table...")
            connection.execute(text("""
                ALTER TABLE objects 
                ADD COLUMN IF NOT EXISTS is_latest BOOLEAN DEFAULT TRUE
            """))
            
            print("Adding deleted column to objects table...")
            connection.execute(text("""
                ALTER TABLE objects 
                ADD COLUMN IF NOT EXISTS deleted BOOLEAN DEFAULT FALSE
            """))
            
            print("Adding time_created column to objects table...")
            connection.execute(text("""
                ALTER TABLE objects 
                ADD COLUMN IF NOT EXISTS time_created TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            """))
            
            # Step 2: Update existing rows to have generation=1 and time_created
            print("Setting default values for existing objects...")
            connection.execute(text("""
                UPDATE objects 
                SET generation = 1, 
                    is_latest = TRUE, 
                    deleted = FALSE,
                    time_created = created_at
                WHERE generation IS NULL
            """))
            
            # Step 3: Create object_versions table
            print("Creating object_versions table...")
            connection.execute(text("""
                CREATE TABLE IF NOT EXISTS object_versions (
                    id VARCHAR(255) PRIMARY KEY,
                    object_id VARCHAR(255) NOT NULL,
                    bucket_id VARCHAR(63) NOT NULL,
                    name VARCHAR(1024) NOT NULL,
                    generation BIGINT NOT NULL,
                    metageneration BIGINT DEFAULT 1,
                    size BIGINT DEFAULT 0,
                    content_type VARCHAR(255) DEFAULT 'application/octet-stream',
                    md5_hash VARCHAR(32),
                    crc32c_hash VARCHAR(44),
                    file_path VARCHAR(1024),
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    deleted BOOLEAN DEFAULT FALSE,
                    meta JSON,
                    FOREIGN KEY (bucket_id) REFERENCES buckets(id) ON DELETE CASCADE
                )
            """))
            
            # Step 4: Create indexes for object_versions
            print("Creating indexes on object_versions...")
            connection.execute(text("""
                CREATE INDEX IF NOT EXISTS idx_object_versions_bucket 
                ON object_versions(bucket_id)
            """))
            
            connection.execute(text("""
                CREATE INDEX IF NOT EXISTS idx_object_versions_name 
                ON object_versions(name)
            """))
            
            connection.execute(text("""
                CREATE INDEX IF NOT EXISTS idx_object_versions_generation 
                ON object_versions(bucket_id, name, generation)
            """))
            
            connection.execute(text("""
                CREATE INDEX IF NOT EXISTS idx_object_versions_object_id 
                ON object_versions(object_id)
            """))
            
            # Step 5: Create unique constraint on bucket + name + generation
            print("Creating unique constraint on bucket_id + name + generation...")
            connection.execute(text("""
                CREATE UNIQUE INDEX IF NOT EXISTS idx_object_versions_unique 
                ON object_versions(bucket_id, name, generation)
            """))
            
            # Step 6: Migrate existing objects to object_versions
            print("Migrating existing objects to object_versions table...")
            connection.execute(text("""
                INSERT INTO object_versions (
                    id, object_id, bucket_id, name, generation, metageneration,
                    size, content_type, md5_hash, crc32c_hash, file_path,
                    created_at, updated_at, deleted, meta
                )
                SELECT 
                    id || '-v1' as id,
                    id as object_id,
                    bucket_id,
                    name,
                    1 as generation,
                    metageneration,
                    size,
                    content_type,
                    md5_hash,
                    crc32c_hash,
                    file_path,
                    created_at,
                    updated_at,
                    FALSE as deleted,
                    meta
                FROM objects
                WHERE NOT EXISTS (
                    SELECT 1 FROM object_versions 
                    WHERE object_versions.object_id = objects.id
                )
            """))
            
            trans.commit()
            print("✅ Migration completed successfully!")
            
        except Exception as e:
            trans.rollback()
            print(f"❌ Migration failed: {e}")
            raise
        finally:
            connection.close()


def downgrade(db, app):
    """
    Rollback migration - remove versioning support
    
    Args:
        db: SQLAlchemy database instance
        app: Flask application
    """
    with app.app_context():
        connection = db.engine.connect()
        trans = connection.begin()
        
        try:
            print("Rolling back object versioning migration...")
            
            # Drop object_versions table
            connection.execute(text("DROP TABLE IF EXISTS object_versions CASCADE"))
            
            # Remove columns from objects table
            connection.execute(text("ALTER TABLE objects DROP COLUMN IF EXISTS generation"))
            connection.execute(text("ALTER TABLE objects DROP COLUMN IF EXISTS is_latest"))
            connection.execute(text("ALTER TABLE objects DROP COLUMN IF EXISTS deleted"))
            connection.execute(text("ALTER TABLE objects DROP COLUMN IF EXISTS time_created"))
            
            trans.commit()
            print("✅ Rollback completed successfully!")
            
        except Exception as e:
            trans.rollback()
            print(f"❌ Rollback failed: {e}")
            raise
        finally:
            connection.close()


if __name__ == "__main__":
    """Run migration directly"""
    from app.factory import create_app, db
    
    app = create_app()
    
    print("=" * 60)
    print("Running Object Versioning Migration")
    print("=" * 60)
    
    upgrade(db, app)
