"""
Project Routes - Cloud Resource Manager API

Maps HTTP methods and paths to project handler functions
"""

from app.handlers.project_handler import project_bp

__all__ = ['project_bp']
