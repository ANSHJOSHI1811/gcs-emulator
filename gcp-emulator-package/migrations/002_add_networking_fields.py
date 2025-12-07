"""
Migration: Add networking fields to compute instances
Phase 5: Networking system

Adds:
1. internal_ip, external_ip, firewall_rules to compute_instances table
2. network_allocations table for IP counter tracking
3. firewall_rules table for firewall rule management
"""

import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.factory import db
from app import create_app


def upgrade():
    """Apply migration"""
    # Add networking fields to compute_instances
    with db.engine.connect() as conn:
        # Add internal_ip column
        conn.execute(db.text("""
            ALTER TABLE compute_instances 
            ADD COLUMN IF NOT EXISTS internal_ip VARCHAR(15);
        """))
        
        # Add external_ip column
        conn.execute(db.text("""
            ALTER TABLE compute_instances 
            ADD COLUMN IF NOT EXISTS external_ip VARCHAR(15);
        """))
        
        # Add firewall_rules column (JSON)
        conn.execute(db.text("""
            ALTER TABLE compute_instances 
            ADD COLUMN IF NOT EXISTS firewall_rules JSON DEFAULT '[]';
        """))
        
        conn.commit()
    
    # Create network_allocations table
    db.session.execute(db.text("""
        CREATE TABLE IF NOT EXISTS network_allocations (
            id SERIAL PRIMARY KEY,
            project_id VARCHAR(63) NOT NULL UNIQUE REFERENCES projects(id) ON DELETE CASCADE,
            internal_counter INTEGER NOT NULL DEFAULT 1,
            external_counter INTEGER NOT NULL DEFAULT 10,
            allocated_internal_ips JSON DEFAULT '[]',
            allocated_external_ips JSON DEFAULT '[]'
        );
    """))
    
    # Create firewall_rules table
    db.session.execute(db.text("""
        CREATE TABLE IF NOT EXISTS firewall_rules (
            id VARCHAR(36) PRIMARY KEY,
            name VARCHAR(63) NOT NULL,
            project_id VARCHAR(63) NOT NULL REFERENCES projects(id) ON DELETE CASCADE,
            direction VARCHAR(10) NOT NULL,
            protocol VARCHAR(10) NOT NULL,
            port INTEGER,
            action VARCHAR(10) NOT NULL DEFAULT 'ALLOW',
            priority INTEGER NOT NULL DEFAULT 1000,
            source_ranges JSON DEFAULT '["0.0.0.0/0"]',
            destination_ranges JSON DEFAULT '["0.0.0.0/0"]',
            target_tags JSON DEFAULT '[]',
            description VARCHAR(255),
            creation_timestamp TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
            UNIQUE(project_id, name)
        );
    """))
    
    # Create indexes
    db.session.execute(db.text("""
        CREATE INDEX IF NOT EXISTS idx_firewall_project ON firewall_rules(project_id);
    """))
    
    db.session.commit()
    print("✓ Migration 002_add_networking_fields applied successfully")


def downgrade():
    """Rollback migration"""
    with db.engine.connect() as conn:
        # Remove columns from compute_instances
        conn.execute(db.text("""
            ALTER TABLE compute_instances 
            DROP COLUMN IF EXISTS internal_ip,
            DROP COLUMN IF EXISTS external_ip,
            DROP COLUMN IF EXISTS firewall_rules;
        """))
        
        conn.commit()
    
    # Drop tables
    db.session.execute(db.text("DROP TABLE IF EXISTS firewall_rules CASCADE;"))
    db.session.execute(db.text("DROP TABLE IF EXISTS network_allocations CASCADE;"))
    
    db.session.commit()
    print("✓ Migration 002_add_networking_fields rolled back successfully")


if __name__ == "__main__":
    app = create_app()
    with app.app_context():
        if len(sys.argv) > 1 and sys.argv[1] == "down":
            downgrade()
        else:
            upgrade()
