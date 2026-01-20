"""
Migration 012: Remove type column from firewall_allowed_denied

This migration removes:
- type column from firewall_allowed_denied table (we use action in firewall_rules instead)
"""

from app.factory import db
from sqlalchemy import text


def upgrade():
    """Apply migration"""
    print("Running migration 012: Remove type from firewall_allowed_denied")
    
    # Remove type column
    db.session.execute(text("""
        ALTER TABLE firewall_allowed_denied 
        DROP COLUMN IF EXISTS type
    """))
    
    db.session.commit()
    print("✓ Migration 012 completed successfully")


def downgrade():
    """Revert migration"""
    print("Reverting migration 012")
    
    db.session.execute(text("""
        ALTER TABLE firewall_allowed_denied 
        ADD COLUMN IF NOT EXISTS type VARCHAR(10) NOT NULL DEFAULT 'allowed'
    """))
    
    db.session.commit()
    print("✓ Migration 012 reverted")


if __name__ == "__main__":
    from app.factory import create_app
    app = create_app()
    with app.app_context():
        upgrade()
