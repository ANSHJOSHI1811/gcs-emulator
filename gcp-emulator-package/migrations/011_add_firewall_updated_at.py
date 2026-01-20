"""
Migration 011: Add updated_at to firewall_rules

This migration adds:
- updated_at column to firewall_rules table
"""

from app.factory import db
from sqlalchemy import text


def upgrade():
    """Apply migration"""
    print("Running migration 011: Add updated_at to firewall_rules")
    
    # Add updated_at column
    db.session.execute(text("""
        ALTER TABLE firewall_rules 
        ADD COLUMN IF NOT EXISTS updated_at TIMESTAMP DEFAULT NOW()
    """))
    
    db.session.commit()
    print("✓ Migration 011 completed successfully")


def downgrade():
    """Revert migration"""
    print("Reverting migration 011")
    
    db.session.execute(text("ALTER TABLE firewall_rules DROP COLUMN IF EXISTS updated_at"))
    
    db.session.commit()
    print("✓ Migration 011 reverted")


if __name__ == "__main__":
    from app.factory import create_app
    app = create_app()
    with app.app_context():
        upgrade()
