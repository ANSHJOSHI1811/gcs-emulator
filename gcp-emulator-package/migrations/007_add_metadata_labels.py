"""
Migration 007: Add metadata and labels support to instances table
Adds JSON columns for storing instance metadata and labels per GCP API spec
"""
import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app.factory import create_app, db
from sqlalchemy import text, inspect

def run_migration():
    """Add metadata_items and labels columns to instances table"""
    app = create_app()
    
    with app.app_context():
        inspector = inspect(db.engine)
        columns = [col['name'] for col in inspector.get_columns('instances')]
        
        print("Running migration 007: Add metadata_items and labels...")
        
        # Add metadata_items column (JSON)
        if 'metadata_items' not in columns:
            db.session.execute(text('''
                ALTER TABLE instances 
                ADD COLUMN metadata_items TEXT DEFAULT '{}';
            '''))
            db.session.commit()
            print("✓ Added metadata_items column (JSON/TEXT)")
        else:
            print("- metadata_items column already exists")
        
        # Add labels column (JSON)
        if 'labels' not in columns:
            db.session.execute(text('''
                ALTER TABLE instances 
                ADD COLUMN labels TEXT DEFAULT '{}';
            '''))
            db.session.commit()
            print("✓ Added labels column (JSON/TEXT)")
        else:
            print("- labels column already exists")
        
        # Add description column (optional but useful)
        if 'description' not in columns:
            db.session.execute(text('''
                ALTER TABLE instances 
                ADD COLUMN description TEXT;
            '''))
            db.session.commit()
            print("✓ Added description column")
        else:
            print("- description column already exists")
        
        print("✓ Migration 007 complete")

if __name__ == '__main__':
    run_migration()
