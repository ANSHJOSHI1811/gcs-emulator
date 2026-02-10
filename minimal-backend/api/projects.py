"""Project Management API"""
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session
from datetime import datetime
from database import get_db, Project
import random

router = APIRouter()

class ProjectCreate(BaseModel):
    projectId: str
    name: str = None

@router.get("/projects")
def list_projects(db: Session = Depends(get_db)):
    """List all projects"""
    projects = db.query(Project).all()
    return {
        "projects": [{
            "projectId": p.id,
            "name": p.name,
            "projectNumber": str(p.project_number) if p.project_number else "0",
            "lifecycleState": "ACTIVE"
        } for p in projects]
    }

@router.post("/projects")
def create_project(project_data: ProjectCreate, db: Session = Depends(get_db)):
    """Create a new project"""
    # Check if project already exists
    existing = db.query(Project).filter_by(id=project_data.projectId).first()
    if existing:
        raise HTTPException(status_code=409, detail=f"Project {project_data.projectId} already exists")
    
    # Create new project
    project = Project(
        id=project_data.projectId,
        name=project_data.name or project_data.projectId,
        project_number=random.randint(100000, 999999),
        location="us-central1",
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow(),
        compute_api_enabled=True
    )
    db.add(project)
    db.commit()
    db.refresh(project)
    
    # Create default network for the project
    from api.vpc import ensure_default_network
    try:
        ensure_default_network(db, project.id)
    except Exception as e:
        print(f"⚠️  Failed to create default network for {project.id}: {e}")
    
    return {
        "projectId": project.id,
        "name": project.name,
        "projectNumber": str(project.project_number),
        "lifecycleState": "ACTIVE"
    }
