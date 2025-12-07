"""Quick script to create test project"""
from app import create_app
from app.factory import db
from app.models.project import Project

app = create_app()

with app.app_context():
    proj = Project.query.filter_by(id='test-project').first()
    if not proj:
        proj = Project(id='test-project', name='Test Project')
        db.session.add(proj)
        db.session.commit()
        print("✓ Created project 'test-project'")
    else:
        print("✓ Project 'test-project' already exists")
