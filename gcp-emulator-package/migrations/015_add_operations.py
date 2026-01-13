#!/usr/bin/env python3
"""
Migration 015: Add operations table

Creates the operations table to support GCP-style operation polling.
Required for Terraform compatibility.
"""

import psycopg2
import os


def get_db_connection():
    """Get database connection from environment"""
    database_url = os.getenv('DATABASE_URL', 'postgresql://postgres:postgres@localhost:5432/gcs_emulator')
    return psycopg2.connect(database_url)


def run_migration():
    """Run the migration"""
    conn = get_db_connection()
    cur = conn.cursor()
    
    try:
        print("Creating operations table...")
        
        # Create operations table
        cur.execute("""
            CREATE TABLE IF NOT EXISTS operations (
                id UUID PRIMARY KEY,
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
                insert_time TIMESTAMP DEFAULT NOW(),
                start_time TIMESTAMP DEFAULT NOW(),
                end_time TIMESTAMP DEFAULT NOW()
            );
        """)
        
        # Create indexes for performance
        print("Creating indexes...")
        
        cur.execute("""
            CREATE INDEX IF NOT EXISTS idx_operations_project 
            ON operations(project_id);
        """)
        
        cur.execute("""
            CREATE INDEX IF NOT EXISTS idx_operations_name 
            ON operations(name);
        """)
        
        cur.execute("""
            CREATE INDEX IF NOT EXISTS idx_operations_status 
            ON operations(status);
        """)
        
        cur.execute("""
            CREATE INDEX IF NOT EXISTS idx_operations_zone 
            ON operations(zone);
        """)
        
        cur.execute("""
            CREATE INDEX IF NOT EXISTS idx_operations_region 
            ON operations(region);
        """)
        
        conn.commit()
        print("✅ Migration 015 completed successfully!")
        
    except Exception as e:
        conn.rollback()
        print(f"❌ Migration 015 failed: {e}")
        raise
    finally:
        cur.close()
        conn.close()


if __name__ == '__main__':
    run_migration()
