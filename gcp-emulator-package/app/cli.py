"""
CLI commands for Flask application
"""
import click
from flask import Flask


def cli(app: Flask):
    """Register CLI commands"""
    
    @app.cli.command("init-db")
    def init_db():
        """Initialize the database"""
        from app.factory import db
        db.create_all()
        click.echo("Database initialized.")
    
    # Register IAM CLI commands
    try:
        from app.cli_commands.iam_commands import register_iam_commands
        register_iam_commands(app)
    except ImportError:
        # IAM commands not available
        pass
