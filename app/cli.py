"""
Flask CLI commands for database management
"""
import click
from flask import current_app
from flask.cli import with_appcontext
from app.factory import db


@click.group()
def cli():
    """Database management commands"""
    pass


@cli.command()
@with_appcontext
def init():
    """Initialize database with tables"""
    try:
        db.create_all()
        click.echo("✅ Database initialized successfully")
        
        # Seed default project
        from app.models import Project
        default_project = Project.query.filter_by(id="default_project").first()
        if not default_project:
            project = Project(
                id="default_project",
                name="Default Project",
                location="US",
                metadata={}
            )
            db.session.add(project)
            db.session.commit()
            click.echo("✅ Default project created")
    except Exception as e:
        click.echo(f"❌ Error initializing database: {str(e)}", err=True)


@cli.command()
@with_appcontext
def seed():
    """Seed default project"""
    try:
        from app.models import Project
        
        default_project = Project.query.filter_by(id="default_project").first()
        if default_project:
            click.echo("ℹ️  Default project already exists")
            return
        
        project = Project(
            id="default_project",
            name="Default Project",
            location="US",
            meta={}
        )
        db.session.add(project)
        db.session.commit()
        click.echo("✅ Default project seeded successfully")
    except Exception as e:
        click.echo(f"❌ Error seeding data: {str(e)}", err=True)


@cli.command()
@with_appcontext
def drop():
    """Drop all tables (WARNING: This will delete all data!)"""
    if click.confirm("⚠️  This will delete all data! Are you sure?"):
        try:
            db.drop_all()
            click.echo("✅ All tables dropped")
        except Exception as e:
            click.echo(f"❌ Error dropping tables: {str(e)}", err=True)


@cli.command()
@with_appcontext
def reset():
    """Reset database (drop and recreate)"""
    if click.confirm("⚠️  This will reset all data! Are you sure?"):
        try:
            db.drop_all()
            click.echo("✅ Tables dropped")
            
            db.create_all()
            click.echo("✅ Tables recreated")
            
            from app.models import Project
            project = Project(
                id="default_project",
                name="Default Project",
                location="US",
                metadata={}
            )
            db.session.add(project)
            db.session.commit()
            click.echo("✅ Default project created")
            
            click.echo("✅ Database reset successfully")
        except Exception as e:
            click.echo(f"❌ Error resetting database: {str(e)}", err=True)
