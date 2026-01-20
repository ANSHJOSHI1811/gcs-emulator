#!/usr/bin/env python3
"""
Migration 014: Add addresses table for external IP addresses

Creates the addresses table to support:
- Static external IP reservation
- Ephemeral external IP tracking
- Regional and global IP addresses
- IP address status tracking (RESERVED, IN_USE)
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
        print("Creating addresses table...")
        
        # Create addresses table
        cur.execute("""
            CREATE TABLE IF NOT EXISTS addresses (
                id UUID PRIMARY KEY,
                name VARCHAR(63) NOT NULL,
                project_id VARCHAR(255) NOT NULL REFERENCES projects(id) ON DELETE CASCADE,
                region VARCHAR(50) NOT NULL,
                address VARCHAR(50) NOT NULL,
                address_type VARCHAR(20) DEFAULT 'EXTERNAL',
                status VARCHAR(20) DEFAULT 'RESERVED',
                network_tier VARCHAR(20) DEFAULT 'PREMIUM',
                purpose VARCHAR(50),
                description TEXT,
                user_instance_id VARCHAR(255),
                user_network_interface_id UUID,
                creation_timestamp TIMESTAMP DEFAULT NOW(),
                CONSTRAINT uq_address_project_region_name UNIQUE(project_id, region, name),
                CONSTRAINT uq_address_ip UNIQUE(address)
            );
        """)
        
        # Create indexes for performance
        print("Creating indexes...")
        
        cur.execute("""
            CREATE INDEX IF NOT EXISTS idx_addresses_project 
            ON addresses(project_id);
        """)
        
        cur.execute("""
            CREATE INDEX IF NOT EXISTS idx_addresses_region 
            ON addresses(region);
        """)
        
        cur.execute("""
            CREATE INDEX IF NOT EXISTS idx_addresses_status 
            ON addresses(status);
        """)
        
        cur.execute("""
            CREATE INDEX IF NOT EXISTS idx_addresses_instance 
            ON addresses(user_instance_id);
        """)
        
        conn.commit()
        print("✅ Migration 014 completed successfully!")
        
    except Exception as e:
        conn.rollback()
        print(f"❌ Migration 014 failed: {e}")
        raise
    finally:
        cur.close()
        conn.close()


if __name__ == '__main__':
    run_migration()
