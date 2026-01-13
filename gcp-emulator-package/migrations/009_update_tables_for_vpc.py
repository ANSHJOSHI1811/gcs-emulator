"""
Migration 009: Update Existing Tables for VPC Integration

Updates:
- instances table: Add network_url, subnetwork_url, network_tier
- projects table: Add compute_api_enabled
- zones table: Add region mapping
"""

from app.factory import create_app, db
from sqlalchemy import text


def upgrade():
    """Update existing tables for VPC integration"""
    app = create_app()
    
    with app.app_context():
        print("Updating existing tables for VPC integration...")
        
        # Update instances table - Add VPC networking fields
        print("Updating instances table...")
        db.session.execute(text("""
            ALTER TABLE instances 
            ADD COLUMN IF NOT EXISTS network_url VARCHAR(500),
            ADD COLUMN IF NOT EXISTS subnetwork_url VARCHAR(500),
            ADD COLUMN IF NOT EXISTS network_tier VARCHAR(20) DEFAULT 'PREMIUM'
        """))
        
        # Update projects table - Add API enablement tracking
        print("Updating projects table...")
        db.session.execute(text("""
            ALTER TABLE projects 
            ADD COLUMN IF NOT EXISTS compute_api_enabled BOOLEAN DEFAULT TRUE
        """))
        
        # Update zones table - Add region mapping
        print("Updating zones table...")
        db.session.execute(text("""
            ALTER TABLE zones 
            ADD COLUMN IF NOT EXISTS region VARCHAR(50)
        """))
        
        # Populate region from zone name (e.g., us-central1-a -> us-central1)
        db.session.execute(text("""
            UPDATE zones 
            SET region = SUBSTRING(name FROM '^([a-z]+-[a-z]+[0-9]+)')
            WHERE region IS NULL
        """))
        
        # Set default network for existing instances (if any)
        db.session.execute(text("""
            UPDATE instances 
            SET network_url = 'https://www.googleapis.com/compute/v1/projects/' || 
                              (SELECT project_id FROM instances i2 WHERE i2.id = instances.id) || 
                              '/global/networks/default',
                network_tier = 'PREMIUM'
            WHERE network_url IS NULL
        """))
        
        db.session.commit()
        print("✅ Migration 009: Tables updated for VPC integration")


def downgrade():
    """Revert VPC integration changes"""
    db.session.execute(text("ALTER TABLE instances DROP COLUMN IF EXISTS network_url"))
    db.session.execute(text("ALTER TABLE instances DROP COLUMN IF EXISTS subnetwork_url"))
    db.session.execute(text("ALTER TABLE instances DROP COLUMN IF EXISTS network_tier"))
    db.session.execute(text("ALTER TABLE projects DROP COLUMN IF EXISTS compute_api_enabled"))
    db.session.execute(text("ALTER TABLE zones DROP COLUMN IF EXISTS region"))
    db.session.commit()
    print("✅ Migration 009: VPC integration changes reverted")


if __name__ == '__main__':
    print("Running migration 009: Update tables for VPC")
    upgrade()
