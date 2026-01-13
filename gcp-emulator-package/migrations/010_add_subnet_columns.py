"""
Migration 010: Add description and updated_at to subnetworks

This migration adds:
- description column to subnetworks table
- updated_at column to subnetworks table
"""

from app.factory import db
from sqlalchemy import text


def upgrade():
    """Apply migration"""
    print("Running migration 010: Add description and updated_at to subnetworks")
    
    # Add description column
    db.session.execute(text("""
        ALTER TABLE subnetworks 
        ADD COLUMN IF NOT EXISTS description TEXT
    """))
    
    # Add updated_at column
    db.session.execute(text("""
        ALTER TABLE subnetworks 
        ADD COLUMN IF NOT EXISTS updated_at TIMESTAMP DEFAULT NOW()
    """))
    
    db.session.commit()
    print("✓ Migration 010 completed successfully")


def downgrade():
    """Revert migration"""
    print("Reverting migration 010")
    
    # Remove columns
    db.session.execute(text("ALTER TABLE subnetworks DROP COLUMN IF EXISTS description"))
    db.session.execute(text("ALTER TABLE subnetworks DROP COLUMN IF EXISTS updated_at"))
    
    db.session.commit()
    print("✓ Migration 010 reverted")


if __name__ == "__main__":
    from app.factory import create_app
    app = create_app()
    with app.app_context():
        upgrade()
