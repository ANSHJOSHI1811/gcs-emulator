"""
Migration: Add Docker network integration fields to networks table

This migration adds docker_network_id and docker_network_name fields 
to enable VPC networks to be mapped to Docker networks for container networking.

Date: 2026-01-14
"""

import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app.factory import create_app, db


def upgrade():
    """Add Docker network fields to networks table"""
    app = create_app()
    with app.app_context():
        # Add docker_network_id column
        db.session.execute(db.text("""
            ALTER TABLE networks 
            ADD COLUMN IF NOT EXISTS docker_network_id VARCHAR(255);
        """))
        
        # Add docker_network_name column
        db.session.execute(db.text("""
            ALTER TABLE networks 
            ADD COLUMN IF NOT EXISTS docker_network_name VARCHAR(255);
        """))
        
        db.session.commit()
        print("✓ Added docker_network_id and docker_network_name columns to networks table")


def downgrade():
    """Remove Docker network fields from networks table"""
    app = create_app()
    with app.app_context():
        db.session.execute(db.text("""
            ALTER TABLE networks 
            DROP COLUMN IF EXISTS docker_network_id;
        """))
        
        db.session.execute(db.text("""
            ALTER TABLE networks 
            DROP COLUMN IF EXISTS docker_network_name;
        """))
        
        db.session.commit()
        print("✓ Removed docker_network_id and docker_network_name columns from networks table")


if __name__ == '__main__':
    print("Running migration: 005_add_docker_network_fields")
    print("-" * 60)
    upgrade()
    print("-" * 60)
    print("Migration completed successfully!")
