"""
Migration: Add IAM tables
Creates tables for IAM functionality including:
- Service Accounts
- Service Account Keys  
- IAM Policies
- IAM Bindings
- IAM Roles
"""
from app.factory import db


def upgrade():
    """Create IAM tables"""
    
    # Create service_accounts table
    db.session.execute("""
        CREATE TABLE IF NOT EXISTS service_accounts (
            email VARCHAR(255) PRIMARY KEY,
            project_id VARCHAR(63) NOT NULL REFERENCES projects(id) ON DELETE CASCADE,
            name VARCHAR(255) NOT NULL,
            display_name VARCHAR(100),
            description TEXT,
            unique_id VARCHAR(21) UNIQUE NOT NULL,
            oauth2_client_id VARCHAR(21),
            disabled BOOLEAN DEFAULT FALSE NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP NOT NULL,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            meta JSONB DEFAULT '{}'::jsonb
        )
    """)
    
    # Create service_account_keys table
    db.session.execute("""
        CREATE TABLE IF NOT EXISTS service_account_keys (
            id VARCHAR(255) PRIMARY KEY,
            service_account_email VARCHAR(255) NOT NULL REFERENCES service_accounts(email) ON DELETE CASCADE,
            key_algorithm VARCHAR(50) DEFAULT 'KEY_ALG_RSA_2048',
            key_origin VARCHAR(50) DEFAULT 'GOOGLE_PROVIDED',
            key_type VARCHAR(50) DEFAULT 'USER_MANAGED',
            private_key_data TEXT,
            public_key_data TEXT,
            disabled BOOLEAN DEFAULT FALSE NOT NULL,
            valid_after_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            valid_before_time TIMESTAMP,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP NOT NULL
        )
    """)
    
    # Create iam_policies table
    db.session.execute("""
        CREATE TABLE IF NOT EXISTS iam_policies (
            id SERIAL PRIMARY KEY,
            resource_name VARCHAR(500) UNIQUE NOT NULL,
            resource_type VARCHAR(50) NOT NULL,
            version INTEGER DEFAULT 1,
            etag VARCHAR(64),
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP NOT NULL,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    
    # Create iam_bindings table
    db.session.execute("""
        CREATE TABLE IF NOT EXISTS iam_bindings (
            id SERIAL PRIMARY KEY,
            policy_id INTEGER NOT NULL REFERENCES iam_policies(id) ON DELETE CASCADE,
            role VARCHAR(255) NOT NULL,
            members TEXT[] DEFAULT ARRAY[]::TEXT[] NOT NULL,
            condition JSONB,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP NOT NULL,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    
    # Create iam_roles table
    db.session.execute("""
        CREATE TABLE IF NOT EXISTS iam_roles (
            id SERIAL PRIMARY KEY,
            name VARCHAR(255) UNIQUE NOT NULL,
            title VARCHAR(255) NOT NULL,
            description TEXT,
            stage VARCHAR(50) DEFAULT 'GA',
            is_custom BOOLEAN DEFAULT FALSE NOT NULL,
            project_id VARCHAR(63) REFERENCES projects(id) ON DELETE CASCADE,
            included_permissions TEXT[] DEFAULT ARRAY[]::TEXT[] NOT NULL,
            deleted BOOLEAN DEFAULT FALSE NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP NOT NULL,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            etag VARCHAR(64)
        )
    """)
    
    # Create indexes
    db.session.execute("CREATE INDEX IF NOT EXISTS idx_service_accounts_project ON service_accounts(project_id)")
    db.session.execute("CREATE INDEX IF NOT EXISTS idx_service_account_keys_email ON service_account_keys(service_account_email)")
    db.session.execute("CREATE INDEX IF NOT EXISTS idx_iam_policies_resource ON iam_policies(resource_name)")
    db.session.execute("CREATE INDEX IF NOT EXISTS idx_iam_bindings_policy ON iam_bindings(policy_id)")
    db.session.execute("CREATE INDEX IF NOT EXISTS idx_iam_roles_name ON iam_roles(name)")
    db.session.execute("CREATE INDEX IF NOT EXISTS idx_iam_roles_project ON iam_roles(project_id)")
    
    db.session.commit()
    print("✅ IAM tables created successfully")


def downgrade():
    """Drop IAM tables"""
    db.session.execute("DROP TABLE IF EXISTS service_account_keys CASCADE")
    db.session.execute("DROP TABLE IF EXISTS service_accounts CASCADE")
    db.session.execute("DROP TABLE IF EXISTS iam_bindings CASCADE")
    db.session.execute("DROP TABLE IF EXISTS iam_policies CASCADE")
    db.session.execute("DROP TABLE IF EXISTS iam_roles CASCADE")
    db.session.commit()
    print("✅ IAM tables dropped successfully")


if __name__ == "__main__":
    from app import create_app
    
    app = create_app()
    with app.app_context():
        upgrade()
