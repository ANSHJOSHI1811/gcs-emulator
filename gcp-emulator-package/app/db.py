"""
Database initialization and seeding utilities
"""
import os
from sqlalchemy import text


def init_db(app, db):
    """
    Initialize database with tables and seed data
    
    Args:
        app: Flask application
        db: SQLAlchemy database instance
    """
    with app.app_context():
        # Create all tables
        db.create_all()
        
        # Seed default project if it doesn't exist
        seed_default_project(app, db)


def seed_default_project(app, db):
    """
    Seed the default project into the database
    
    Args:
        app: Flask application
        db: SQLAlchemy database instance
    """
    from app.models import Project
    
    with app.app_context():
        # Check if default project exists
        default_project = Project.query.filter_by(id="default_project").first()
        
        if default_project:
            app.logger.info("Default project already exists")
            return
        
        # Create default project
        project = Project(
            id="default_project",
            name="Default Project",
            location="US"
        )
        
        db.session.add(project)
        db.session.commit()
        
        app.logger.info("✅ Default project created successfully")


def run_migrations(app):
    """
    Run Alembic migrations
    
    Args:
        app: Flask application
    """
    from alembic.config import Config
    from alembic.command import upgrade
    
    # Get the directory where this script is located
    basedir = os.path.dirname(os.path.dirname(__file__))
    alembic_cfg = Config(os.path.join(basedir, "migrations", "alembic.ini"))
    alembic_cfg.set_main_option("sqlalchemy.url", app.config["SQLALCHEMY_DATABASE_URI"])
    
    with app.app_context():
        upgrade(alembic_cfg, "head")
        app.logger.info("✅ Database migrations completed")
