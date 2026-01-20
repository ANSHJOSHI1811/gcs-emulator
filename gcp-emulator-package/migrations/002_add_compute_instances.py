"""
PHASE 1 Migration: Add Compute Instances table
Date: 2025-12-09
Description: Creates instances table for basic compute lifecycle
"""
from sqlalchemy import text


def upgrade(db, app):
    """
    Create instances table for PHASE 1
    
    Args:
        db: SQLAlchemy database instance
        app: Flask application
    """
    with app.app_context():
        connection = db.engine.connect()
        trans = connection.begin()
        
        try:
            print("Creating instances table for PHASE 1...")
            
            connection.execute(text("""
                CREATE TABLE IF NOT EXISTS instances (
                    id VARCHAR(36) PRIMARY KEY,
                    name VARCHAR(255) NOT NULL,
                    image VARCHAR(500) NOT NULL,
                    cpu INTEGER DEFAULT 1,
                    memory_mb INTEGER DEFAULT 512,
                    container_id VARCHAR(100) UNIQUE,
                    state VARCHAR(20) NOT NULL DEFAULT 'pending',
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """))
            
            print("Creating indexes on instances table...")
            
            connection.execute(text("""
                CREATE INDEX IF NOT EXISTS idx_instances_container_id 
                ON instances(container_id)
            """))
            
            connection.execute(text("""
                CREATE INDEX IF NOT EXISTS idx_instances_state 
                ON instances(state)
            """))
            
            trans.commit()
            
            # Verify table creation
            result = connection.execute(text("""
                SELECT COUNT(*) 
                FROM information_schema.tables 
                WHERE table_name = 'instances'
            """))
            count = result.scalar()
            
            if count > 0:
                print("✓ instances table created successfully (PHASE 1)")
            else:
                raise Exception("Failed to create instances table")
                
        except Exception as e:
            trans.rollback()
            print(f"✗ Migration failed: {e}")
            raise
        finally:
            connection.close()


def downgrade(db, app):
    """
    Drop instances table
    
    Args:
        db: SQLAlchemy database instance
        app: Flask application
    """
    with app.app_context():
        connection = db.engine.connect()
        trans = connection.begin()
        
        try:
            print("Dropping instances table...")
            connection.execute(text("DROP TABLE IF EXISTS instances CASCADE"))
            trans.commit()
            print("✓ instances table dropped")
        except Exception as e:
            trans.rollback()
            print(f"✗ Downgrade failed: {e}")
            raise
        finally:
            connection.close()


if __name__ == '__main__':
    from app.factory import create_app, db
    
    app = create_app('development')
    
    with app.app_context():
        print("\n=== Running Migration: 002_add_compute_instances (PHASE 1) ===\n")
        
        try:
            upgrade(db, app)
            print("\n✓ Migration completed successfully\n")
        except Exception as e:
            print(f"\n✗ Migration failed: {e}\n")
            raise
