"""Initial database schema - Projects, Buckets, Objects

Revision ID: 001_initial_schema
Revises: 
Create Date: 2025-11-20 17:45:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '001_initial_schema'
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Create projects table
    op.create_table(
        'projects',
        sa.Column('id', sa.String(63), nullable=False),
        sa.Column('name', sa.String(255), nullable=False),
        sa.Column('location', sa.String(50), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.func.current_timestamp()),
        sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.func.current_timestamp()),
        sa.Column('meta', postgresql.JSON(), nullable=True),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('name')
    )
    
    # Create buckets table
    op.create_table(
        'buckets',
        sa.Column('id', sa.String(63), nullable=False),
        sa.Column('project_id', sa.String(63), nullable=False),
        sa.Column('name', sa.String(63), nullable=False),
        sa.Column('location', sa.String(50), nullable=True),
        sa.Column('storage_class', sa.String(50), nullable=True),
        sa.Column('versioning_enabled', sa.Boolean(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.func.current_timestamp()),
        sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.func.current_timestamp()),
        sa.Column('meta', postgresql.JSON(), nullable=True),
        sa.ForeignKeyConstraint(['project_id'], ['projects.id'], ),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('name')
    )
    
    # Create index on buckets.project_id
    op.create_index('idx_buckets_project', 'buckets', ['project_id'], unique=False)
    
    # Create objects table
    op.create_table(
        'objects',
        sa.Column('id', sa.String(255), nullable=False),
        sa.Column('bucket_id', sa.String(63), nullable=False),
        sa.Column('name', sa.String(1024), nullable=False),
        sa.Column('size', sa.BigInteger(), nullable=True),
        sa.Column('content_type', sa.String(255), nullable=True),
        sa.Column('md5_hash', sa.String(32), nullable=True),
        sa.Column('crc32c_hash', sa.String(44), nullable=True),
        sa.Column('file_path', sa.String(1024), nullable=True),
        sa.Column('metageneration', sa.BigInteger(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.func.current_timestamp()),
        sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.func.current_timestamp()),
        sa.Column('meta', postgresql.JSON(), nullable=True),
        sa.ForeignKeyConstraint(['bucket_id'], ['buckets.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    
    # Create indexes on objects table
    op.create_index('idx_objects_bucket', 'objects', ['bucket_id'], unique=False)
    op.create_index('idx_objects_name', 'objects', ['name'], unique=False)


def downgrade() -> None:
    # Drop objects table and indexes
    op.drop_index('idx_objects_name', table_name='objects')
    op.drop_index('idx_objects_bucket', table_name='objects')
    op.drop_table('objects')
    
    # Drop buckets table and indexes
    op.drop_index('idx_buckets_project', table_name='buckets')
    op.drop_table('buckets')
    
    # Drop projects table
    op.drop_table('projects')
