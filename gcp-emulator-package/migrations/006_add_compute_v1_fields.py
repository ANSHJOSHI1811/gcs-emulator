"""
Migration: Add GCP Compute API v1 fields to instances table
Adds zone and machine_type columns for SDK compatibility
"""
import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app.factory import db
from app.models.instance import Instance


def upgrade():
    """Add zone and machine_type columns"""
    print("Adding GCP Compute API v1 fields to instances table...")
    
    # Check if columns exist
    from sqlalchemy import inspect, text
    inspector = inspect(db.engine)
    columns = [col['name'] for col in inspector.get_columns('instances')]
    
    if 'zone' not in columns:
        db.session.execute(text('ALTER TABLE instances ADD COLUMN zone VARCHAR(100) DEFAULT \'us-central1-a\''))
        print("  ✓ Added zone column")
    else:
        print("  - zone column already exists")
    
    if 'machine_type' not in columns:
        db.session.execute(text('ALTER TABLE instances ADD COLUMN machine_type VARCHAR(100) DEFAULT \'e2-micro\''))
        print("  ✓ Added machine_type column")
    else:
        print("  - machine_type column already exists")
    
    db.session.commit()
    print("✓ Migration complete")


def downgrade():
    """Remove zone and machine_type columns"""
    print("Removing GCP Compute API v1 fields from instances table...")
    
    from sqlalchemy import text
    db.session.execute(text('ALTER TABLE instances DROP COLUMN IF EXISTS zone'))
    db.session.execute(text('ALTER TABLE instances DROP COLUMN IF EXISTS machine_type'))
    
    db.session.commit()
    print("✓ Downgrade complete")


if __name__ == '__main__':
    from app.factory import create_app
    app = create_app()
    
    with app.app_context():
        upgrade()
