"""
Migration 017: Add VPC Peering support

Creates vpc_peerings table for network peering connections.
"""

from app.factory import create_app, db
from sqlalchemy import text


def upgrade():
    """Create vpc_peerings table"""
    connection = db.engine.connect()
    trans = connection.begin()
    
    try:
        # Create vpc_peerings table
        connection.execute(text("""
            CREATE TABLE IF NOT EXISTS vpc_peerings (
                id VARCHAR(36) PRIMARY KEY,
                name VARCHAR(63) NOT NULL,
                network_id VARCHAR(36) REFERENCES networks(id) ON DELETE CASCADE,
                peer_network VARCHAR(255) NOT NULL,
                peer_project_id VARCHAR(255),
                peer_network_name VARCHAR(63),
                state VARCHAR(20) DEFAULT 'ACTIVE',
                state_details TEXT,
                auto_create_routes BOOLEAN DEFAULT TRUE,
                exchange_subnet_routes BOOLEAN DEFAULT TRUE,
                export_custom_routes BOOLEAN DEFAULT FALSE,
                import_custom_routes BOOLEAN DEFAULT FALSE,
                export_subnet_routes_with_public_ip BOOLEAN DEFAULT TRUE,
                import_subnet_routes_with_public_ip BOOLEAN DEFAULT FALSE,
                creation_timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(network_id, name)
            )
        """))
        
        # Create index on network_id
        connection.execute(text("""
            CREATE INDEX IF NOT EXISTS idx_vpc_peerings_network_id 
            ON vpc_peerings(network_id)
        """))
        
        # Create index on peer_network for reverse lookups
        connection.execute(text("""
            CREATE INDEX IF NOT EXISTS idx_vpc_peerings_peer_network 
            ON vpc_peerings(peer_network)
        """))
        
        trans.commit()
        print("✅ Migration 017: VPC Peerings table created successfully")
        
    except Exception as e:
        trans.rollback()
        print(f"❌ Migration 017 failed: {str(e)}")
        raise


def downgrade():
    """Drop vpc_peerings table"""
    connection = db.engine.connect()
    trans = connection.begin()
    
    try:
        connection.execute(text("DROP TABLE IF EXISTS vpc_peerings CASCADE"))
        trans.commit()
        print("✅ Migration 017: VPC Peerings table dropped")
        
    except Exception as e:
        trans.rollback()
        print(f"❌ Migration 017 downgrade failed: {str(e)}")
        raise


if __name__ == "__main__":
    print("Running Migration 017: Add VPC Peering...")
    app = create_app()
    with app.app_context():
        upgrade()
