"""
Migration 008: Create VPC Networking Tables

Creates tables for:
- Networks (VPC networks)
- Subnetworks (subnets within networks)
- Firewall Rules (ingress/egress rules)
- Firewall Allowed/Denied Protocols
- Routes (static routes)
"""

from app.factory import create_app, db
from sqlalchemy import text


def upgrade():
    """Create VPC networking tables"""
    app = create_app()
    
    with app.app_context():
        print("Creating VPC networking tables...")
        
        # Table 1: Networks (VPC Networks)
        db.session.execute(text("""
        CREATE TABLE IF NOT EXISTS networks (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            name VARCHAR(63) NOT NULL,
            project_id VARCHAR(255) NOT NULL,
            description TEXT,
            auto_create_subnetworks BOOLEAN DEFAULT FALSE,
            routing_mode VARCHAR(20) DEFAULT 'REGIONAL',
            mtu INTEGER DEFAULT 1460,
            self_link TEXT,
            creation_timestamp TIMESTAMP DEFAULT NOW(),
            UNIQUE(project_id, name),
            FOREIGN KEY (project_id) REFERENCES projects(id) ON DELETE CASCADE
        )
    """))
        
        # Table 2: Subnetworks (Subnets)
        db.session.execute(text("""
        CREATE TABLE IF NOT EXISTS subnetworks (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            name VARCHAR(63) NOT NULL,
            network_id UUID NOT NULL,
            region VARCHAR(50) NOT NULL,
            ip_cidr_range VARCHAR(50) NOT NULL,
            gateway_address VARCHAR(50),
            private_ip_google_access BOOLEAN DEFAULT FALSE,
            enable_flow_logs BOOLEAN DEFAULT FALSE,
            secondary_ip_ranges JSONB,
            self_link TEXT,
            creation_timestamp TIMESTAMP DEFAULT NOW(),
            UNIQUE(network_id, name),
            FOREIGN KEY (network_id) REFERENCES networks(id) ON DELETE CASCADE
        )
    """))
        
        # Table 3: Firewall Rules
        db.session.execute(text("""
        CREATE TABLE IF NOT EXISTS firewall_rules (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            name VARCHAR(63) NOT NULL,
            network_id UUID NOT NULL,
            description TEXT,
            priority INTEGER DEFAULT 1000,
            direction VARCHAR(10) DEFAULT 'INGRESS',
            action VARCHAR(10) DEFAULT 'ALLOW',
            disabled BOOLEAN DEFAULT FALSE,
            source_ranges TEXT[],
            destination_ranges TEXT[],
            source_tags TEXT[],
            target_tags TEXT[],
            source_service_accounts TEXT[],
            target_service_accounts TEXT[],
            self_link TEXT,
            creation_timestamp TIMESTAMP DEFAULT NOW(),
            UNIQUE(network_id, name),
            FOREIGN KEY (network_id) REFERENCES networks(id) ON DELETE CASCADE,
            CHECK (direction IN ('INGRESS', 'EGRESS')),
            CHECK (action IN ('ALLOW', 'DENY')),
            CHECK (priority >= 0 AND priority <= 65535)
        )
    """))
        
        # Table 4: Firewall Allowed/Denied Protocols
        db.session.execute(text("""
        CREATE TABLE IF NOT EXISTS firewall_allowed_denied (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            firewall_rule_id UUID NOT NULL,
            type VARCHAR(10) NOT NULL,
            ip_protocol VARCHAR(20) NOT NULL,
            ports TEXT[],
            FOREIGN KEY (firewall_rule_id) REFERENCES firewall_rules(id) ON DELETE CASCADE,
            CHECK (type IN ('allowed', 'denied')),
            CHECK (ip_protocol IN ('tcp', 'udp', 'icmp', 'esp', 'ah', 'sctp', 'ipip', 'all'))
        )
    """))
        
        # Table 5: Routes
        db.session.execute(text("""
        CREATE TABLE IF NOT EXISTS routes (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            name VARCHAR(63) NOT NULL,
            network_id UUID NOT NULL,
            description TEXT,
            dest_range VARCHAR(50) NOT NULL,
            priority INTEGER DEFAULT 1000,
            next_hop_type VARCHAR(30),
            next_hop_value TEXT,
            tags TEXT[],
            self_link TEXT,
            creation_timestamp TIMESTAMP DEFAULT NOW(),
            UNIQUE(network_id, name),
            FOREIGN KEY (network_id) REFERENCES networks(id) ON DELETE CASCADE,
            CHECK (priority >= 0 AND priority <= 65535),
            CHECK (next_hop_type IN ('gateway', 'instance', 'ip', 'vpn_tunnel', 'interconnect'))
        )
    """))
        
        # Create indexes for performance
        db.session.execute(text("""
            CREATE INDEX IF NOT EXISTS idx_networks_project ON networks(project_id);
        """))
        
        db.session.execute(text("""
            CREATE INDEX IF NOT EXISTS idx_subnetworks_network ON subnetworks(network_id);
        """))
        
        db.session.execute(text("""
            CREATE INDEX IF NOT EXISTS idx_subnetworks_region ON subnetworks(region);
        """))
        
        db.session.execute(text("""
            CREATE INDEX IF NOT EXISTS idx_firewall_network ON firewall_rules(network_id);
        """))
        
        db.session.execute(text("""
            CREATE INDEX IF NOT EXISTS idx_firewall_priority ON firewall_rules(priority);
        """))
        
        db.session.execute(text("""
            CREATE INDEX IF NOT EXISTS idx_routes_network ON routes(network_id);
        """))
        
        db.session.commit()
        print("✅ Migration 008: VPC tables created successfully")


def downgrade():
    """Drop VPC networking tables"""
    db.session.execute(text("DROP TABLE IF EXISTS firewall_allowed_denied CASCADE"))
    db.session.execute(text("DROP TABLE IF EXISTS routes CASCADE"))
    db.session.execute(text("DROP TABLE IF EXISTS firewall_rules CASCADE"))
    db.session.execute(text("DROP TABLE IF EXISTS subnetworks CASCADE"))
    db.session.execute(text("DROP TABLE IF EXISTS networks CASCADE"))
    db.session.commit()
    print("✅ Migration 008: VPC tables dropped successfully")


if __name__ == '__main__':
    print("Running migration 008: Create VPC tables")
    upgrade()
