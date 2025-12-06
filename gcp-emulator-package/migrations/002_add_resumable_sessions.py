"""
Migration: Add resumable_sessions table for Phase 3 resumable uploads

This table tracks active upload sessions with their state.
"""
from app.factory import db
from sqlalchemy import text


def upgrade():
    """Create resumable_sessions table"""
    with db.engine.connect() as conn:
        conn.execute(text("""
            CREATE TABLE IF NOT EXISTS resumable_sessions (
                session_id VARCHAR(255) PRIMARY KEY,
                bucket_id VARCHAR(63) NOT NULL,
                object_name VARCHAR(1024) NOT NULL,
                metadata_json TEXT,
                current_offset BIGINT DEFAULT 0,
                total_size BIGINT,
                temp_path VARCHAR(1024),
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (bucket_id) REFERENCES buckets(id) ON DELETE CASCADE
            )
        """))
        
        conn.execute(text("""
            CREATE INDEX IF NOT EXISTS idx_resumable_sessions_bucket 
            ON resumable_sessions(bucket_id)
        """))
        
        conn.execute(text("""
            CREATE INDEX IF NOT EXISTS idx_resumable_sessions_created 
            ON resumable_sessions(created_at)
        """))
        
        conn.commit()


def downgrade():
    """Drop resumable_sessions table"""
    with db.engine.connect() as conn:
        conn.execute(text("DROP TABLE IF EXISTS resumable_sessions"))
        conn.commit()


if __name__ == "__main__":
    from app.factory import create_app
    app = create_app()
    with app.app_context():
        upgrade()
        print("Migration 002: resumable_sessions table created")
