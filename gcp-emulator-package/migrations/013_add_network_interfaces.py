"""
Migration 013: Add network_interfaces table

Creates table for tracking instance-network attachments with IP allocation.
"""

import os
import sys

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.factory import create_app, db
from sqlalchemy import text


def upgrade():
    """Create network_interfaces table"""
    app = create_app()
    with app.app_context():
        db.session.execute(text("""
            CREATE TABLE IF NOT EXISTS network_interfaces (
                id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                instance_id VARCHAR(255) NOT NULL REFERENCES instances(id) ON DELETE CASCADE,
                network_id UUID NOT NULL REFERENCES networks(id) ON DELETE CASCADE,
                subnetwork_id UUID REFERENCES subnetworks(id) ON DELETE SET NULL,
                name VARCHAR(63) NOT NULL DEFAULT 'nic0',
                network_ip VARCHAR(50),
                network_tier VARCHAR(20) DEFAULT 'PREMIUM',
                nic_index INTEGER NOT NULL DEFAULT 0,
                creation_timestamp TIMESTAMP DEFAULT NOW(),
                UNIQUE(instance_id, nic_index)
            )
        """))
        
        # Add indexes for better query performance
        db.session.execute(text("""
            CREATE INDEX IF NOT EXISTS idx_network_interfaces_instance 
            ON network_interfaces(instance_id)
        """))
        
        db.session.execute(text("""
            CREATE INDEX IF NOT EXISTS idx_network_interfaces_network 
            ON network_interfaces(network_id)
        """))
        
        db.session.execute(text("""
            CREATE INDEX IF NOT EXISTS idx_network_interfaces_subnetwork 
            ON network_interfaces(subnetwork_id)
        """))
        
        db.session.commit()
        print("✓ Migration 013 completed successfully")


def downgrade():
    """Drop network_interfaces table"""
    app = create_app()
    with app.app_context():
        db.session.execute(text("DROP TABLE IF EXISTS network_interfaces CASCADE"))
        db.session.commit()
        print("✓ Migration 013 rolled back successfully")


if __name__ == "__main__":
    print("Running migration 013: Add network_interfaces table")
    upgrade()
