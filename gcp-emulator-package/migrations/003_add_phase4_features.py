"""
Migration: Add Phase 4 tables and columns

Phase 4 Features:
1. object_events table - Event notification system
2. ACL columns - Minimal ACL simulation (private/publicRead)
3. lifecycle_rules table - Basic lifecycle management
"""
from app.factory import db
from sqlalchemy import text


def upgrade():
    """Create Phase 4 tables and add ACL columns"""
    with db.engine.connect() as conn:
        # 1. Object Events Table
        conn.execute(text("""
            CREATE TABLE IF NOT EXISTS object_events (
                event_id VARCHAR(255) PRIMARY KEY,
                bucket_name VARCHAR(63) NOT NULL,
                object_name VARCHAR(1024) NOT NULL,
                event_type VARCHAR(50) NOT NULL,
                generation BIGINT,
                timestamp TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
                metadata_json TEXT,
                delivered BOOLEAN DEFAULT FALSE
            )
        """))
        
        conn.execute(text("""
            CREATE INDEX IF NOT EXISTS idx_object_events_bucket 
            ON object_events(bucket_name)
        """))
        
        conn.execute(text("""
            CREATE INDEX IF NOT EXISTS idx_object_events_timestamp 
            ON object_events(timestamp)
        """))
        
        conn.execute(text("""
            CREATE INDEX IF NOT EXISTS idx_object_events_delivered 
            ON object_events(delivered)
        """))
        
        # 2. ACL Columns (add to buckets and objects)
        conn.execute(text("""
            ALTER TABLE buckets 
            ADD COLUMN IF NOT EXISTS acl VARCHAR(20) DEFAULT 'private'
        """))
        
        conn.execute(text("""
            ALTER TABLE objects 
            ADD COLUMN IF NOT EXISTS acl VARCHAR(20) DEFAULT 'private'
        """))
        
        # 3. Storage Class Column (for lifecycle Archive action)
        conn.execute(text("""
            ALTER TABLE objects 
            ADD COLUMN IF NOT EXISTS storage_class VARCHAR(50) DEFAULT 'STANDARD'
        """))
        
        # 4. Lifecycle Rules Table
        conn.execute(text("""
            CREATE TABLE IF NOT EXISTS lifecycle_rules (
                rule_id VARCHAR(255) PRIMARY KEY,
                bucket_name VARCHAR(63) NOT NULL,
                action VARCHAR(20) NOT NULL,
                age_days INTEGER NOT NULL,
                created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (bucket_name) REFERENCES buckets(id) ON DELETE CASCADE
            )
        """))
        
        conn.execute(text("""
            CREATE INDEX IF NOT EXISTS idx_lifecycle_rules_bucket 
            ON lifecycle_rules(bucket_name)
        """))
        
        conn.commit()


def downgrade():
    """Drop Phase 4 tables and columns"""
    with db.engine.connect() as conn:
        conn.execute(text("DROP TABLE IF EXISTS object_events"))
        conn.execute(text("DROP TABLE IF EXISTS lifecycle_rules"))
        conn.execute(text("ALTER TABLE buckets DROP COLUMN IF EXISTS acl"))
        conn.execute(text("ALTER TABLE objects DROP COLUMN IF EXISTS acl"))
        conn.execute(text("ALTER TABLE objects DROP COLUMN IF EXISTS storage_class"))
        conn.commit()


if __name__ == "__main__":
    from app.factory import create_app
    app = create_app()
    with app.app_context():
        upgrade()
        print("Migration 003: Phase 4 tables created successfully")
