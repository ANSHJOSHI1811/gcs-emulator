"""
Migration: Fix operation.id to be BigInteger for gcloud CLI compatibility

Changes:
- Drop existing operations table
- Recreate with id as BigInteger instead of UUID
- This ensures gcloud CLI receives numeric operation IDs as expected
"""

import os
import sys

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.factory import create_app, db
from sqlalchemy import text

def run_migration():
    """Run the migration"""
    app = create_app()
    
    with app.app_context():
        print("Starting migration: Fix operation.id for gcloud CLI compatibility")
        
        try:
            # Drop and recreate operations table with correct schema
            print("Dropping operations table...")
            db.session.execute(text("DROP TABLE IF EXISTS operations CASCADE;"))
            
            print("Creating operations table with BigInteger id...")
            db.session.execute(text("""
                CREATE TABLE operations (
                    id BIGINT PRIMARY KEY,
                    name VARCHAR(255) NOT NULL UNIQUE,
                    operation_type VARCHAR(50) NOT NULL,
                    status VARCHAR(20) DEFAULT 'DONE',
                    progress INTEGER DEFAULT 100,
                    target_link TEXT,
                    target_id VARCHAR(255),
                    project_id VARCHAR(255) NOT NULL,
                    region VARCHAR(50),
                    zone VARCHAR(50),
                    error_message TEXT,
                    insert_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    start_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    end_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                );
            """))
            
            db.session.commit()
            print("✅ Migration completed successfully!")
            print("✅ Operations table now uses BigInteger for id (gcloud CLI compatible)")
            
        except Exception as e:
            db.session.rollback()
            print(f"❌ Migration failed: {e}")
            raise

if __name__ == "__main__":
    run_migration()
