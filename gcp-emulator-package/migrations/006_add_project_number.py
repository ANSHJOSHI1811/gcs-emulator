"""
Migration 006: Add project_number field to projects table
"""
from sqlalchemy import text
from app.factory import create_app, db

def migrate():
    """Add project_number column to projects table"""
    app = create_app()
    
    with app.app_context():
        print("Migration 006: Adding project_number to projects table")
        
        # Add project_number column
        db.session.execute(text("""
            ALTER TABLE projects 
            ADD COLUMN IF NOT EXISTS project_number BIGINT;
        """))
        
        # Generate project numbers for existing projects
        db.session.execute(text("""
            UPDATE projects 
            SET project_number = ABS(HASHTEXT(id)::BIGINT) % 1000000000000
            WHERE project_number IS NULL;
        """))
        
        db.session.commit()
        print("✅ Migration 006 complete: Added project_number field")

if __name__ == "__main__":
    migrate()
