"""
Migration: Fix bucket uniqueness constraint and add new features

Changes:
1. Remove unique constraint on buckets.name
2. Add composite unique constraint on (project_id, name)
3. Add cors column to buckets table
4. Add notification_configs column to buckets table
5. Add lifecycle_config column to buckets table
"""
from app.factory import db
from sqlalchemy import text


def upgrade():
    """Apply migration changes"""
    with db.engine.connect() as conn:
        # 1. Drop existing unique constraint on buckets.name
        conn.execute(text("""
            ALTER TABLE buckets 
            DROP CONSTRAINT IF EXISTS buckets_name_key
        """))
        conn.commit()
        
        # 2. Add composite unique constraint on (project_id, name)
        conn.execute(text("""
            ALTER TABLE buckets 
            ADD CONSTRAINT buckets_project_name_unique 
            UNIQUE (project_id, name)
        """))
        conn.commit()
        
        # 3. Add CORS configuration column (JSON array of rules)
        conn.execute(text("""
            ALTER TABLE buckets 
            ADD COLUMN IF NOT EXISTS cors TEXT DEFAULT NULL
        """))
        conn.commit()
        
        # 4. Add notification configurations column (JSON array)
        conn.execute(text("""
            ALTER TABLE buckets 
            ADD COLUMN IF NOT EXISTS notification_configs TEXT DEFAULT NULL
        """))
        conn.commit()
        
        # 5. Add lifecycle configuration column (JSON object)
        conn.execute(text("""
            ALTER TABLE buckets 
            ADD COLUMN IF NOT EXISTS lifecycle_config TEXT DEFAULT NULL
        """))
        conn.commit()
        
        print("✓ Migration 004 completed successfully")
        print("  - Fixed bucket uniqueness to (project_id, name)")
        print("  - Added cors column")
        print("  - Added notification_configs column")
        print("  - Added lifecycle_config column")


def downgrade():
    """Revert migration changes"""
    with db.engine.connect() as conn:
        # Remove new columns
        conn.execute(text("""
            ALTER TABLE buckets 
            DROP COLUMN IF EXISTS lifecycle_config
        """))
        conn.execute(text("""
            ALTER TABLE buckets 
            DROP COLUMN IF EXISTS notification_configs
        """))
        conn.execute(text("""
            ALTER TABLE buckets 
            DROP COLUMN IF EXISTS cors
        """))
        conn.commit()
        
        # Remove composite constraint
        conn.execute(text("""
            ALTER TABLE buckets 
            DROP CONSTRAINT IF EXISTS buckets_project_name_unique
        """))
        conn.commit()
        
        # Re-add unique constraint on name (may fail if duplicates exist)
        try:
            conn.execute(text("""
                ALTER TABLE buckets 
                ADD CONSTRAINT buckets_name_key UNIQUE (name)
            """))
            conn.commit()
        except Exception as e:
            print(f"Warning: Could not restore unique constraint on name: {e}")
        
        print("✓ Migration 004 downgrade completed")


if __name__ == "__main__":
    import sys
    from app.factory import create_app
    
    app = create_app()
    with app.app_context():
        if len(sys.argv) > 1 and sys.argv[1] == "downgrade":
            downgrade()
        else:
            upgrade()
