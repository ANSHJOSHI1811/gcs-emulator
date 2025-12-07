"""
Migration: Add Compute Engine tables
Phase 1: Instance metadata and state management
"""
from sqlalchemy import Column, String, DateTime, ForeignKey, UniqueConstraint, Index
from sqlalchemy.dialects.postgresql import JSON
from datetime import datetime


def upgrade(db):
    """Create compute_instances table"""
    
    # Create compute_instances table
    db.engine.execute("""
        CREATE TABLE IF NOT EXISTS compute_instances (
            id VARCHAR(36) PRIMARY KEY,
            name VARCHAR(63) NOT NULL,
            project_id VARCHAR(63) NOT NULL REFERENCES projects(id) ON DELETE CASCADE,
            zone VARCHAR(50) NOT NULL,
            
            machine_type VARCHAR(50) NOT NULL,
            status VARCHAR(20) NOT NULL DEFAULT 'PROVISIONING',
            status_message VARCHAR(255) DEFAULT '',
            
            container_id VARCHAR(64),
            
            creation_timestamp TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
            last_start_timestamp TIMESTAMP,
            last_stop_timestamp TIMESTAMP,
            
            instance_metadata JSONB DEFAULT '{}',
            labels JSONB DEFAULT '{}',
            tags JSONB DEFAULT '[]',
            network_interfaces JSONB DEFAULT '[]',
            disks JSONB DEFAULT '[]',
            
            CONSTRAINT unique_instance_per_zone UNIQUE (project_id, zone, name)
        );
    """)
    
    # Create indexes
    db.engine.execute("""
        CREATE INDEX IF NOT EXISTS idx_instances_project 
        ON compute_instances(project_id);
    """)
    
    db.engine.execute("""
        CREATE INDEX IF NOT EXISTS idx_instances_zone 
        ON compute_instances(zone);
    """)
    
    db.engine.execute("""
        CREATE INDEX IF NOT EXISTS idx_instances_status 
        ON compute_instances(status);
    """)
    
    print("✓ Created compute_instances table")
    print("✓ Created indexes on project_id, zone, status")
    print("✓ Added unique constraint on (project_id, zone, name)")


def downgrade(db):
    """Drop compute_instances table"""
    db.engine.execute("DROP TABLE IF EXISTS compute_instances;")
    print("✓ Dropped compute_instances table")


if __name__ == "__main__":
    print("Migration 002: Add Compute Engine")
    print("This migration adds the compute_instances table for Phase 1")
    print("Run this migration using the Flask migration system")
