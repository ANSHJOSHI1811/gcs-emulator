"""
Migration 007: Increase field lengths for URL-based values
"""
from sqlalchemy import text

def migrate():
    """Increase field lengths to accommodate full GCP URLs"""
    from app.factory import create_app, db
    app = create_app()
    
    with app.app_context():
        print("Migration 007: Increasing field lengths for GCP URL compatibility")
        
        # Increase machine_type length (URL format)
        db.session.execute(text("""
            ALTER TABLE instances 
            ALTER COLUMN machine_type TYPE VARCHAR(500);
        """))
        
        # Increase zone length (URL format)
        db.session.execute(text("""
            ALTER TABLE instances 
            ALTER COLUMN zone TYPE VARCHAR(500);
        """))
        
        # Increase source_image length (URL format)
        db.session.execute(text("""
            ALTER TABLE instances 
            ALTER COLUMN source_image TYPE VARCHAR(500);
        """))
        
        db.session.commit()
        print("✅ Migration 007 complete: Increased field lengths for URL compatibility")

if __name__ == "__main__":
    migrate()
