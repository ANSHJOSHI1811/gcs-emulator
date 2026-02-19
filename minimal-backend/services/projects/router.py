"""Project Management API"""
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session
from datetime import datetime
from core.database import get_db, Project
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

@router.delete("/projects/{project_id}")
def delete_project(project_id: str, db: Session = Depends(get_db)):
    """Delete a project and all its resources"""
    from core.database import Network, Instance, Firewall, Route
    
    # Find project
    project = db.query(Project).filter_by(id=project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail=f"Project {project_id} not found")
    
    # Delete all instances
    instances = db.query(Instance).filter_by(project_id=project_id).all()
    for instance in instances:
        db.delete(instance)
    
    # Delete all networks
    networks = db.query(Network).filter_by(project_id=project_id).all()
    for network in networks:
        db.delete(network)
    
    # Delete all firewalls
    firewalls = db.query(Firewall).filter_by(project_id=project_id).all()
    for firewall in firewalls:
        db.delete(firewall)
    
    # Delete all routes
    routes = db.query(Route).filter_by(project_id=project_id).all()
    for route in routes:
        db.delete(route)
    
    # Delete project
    db.delete(project)
    db.commit()
    
    return {"message": f"Project {project_id} deleted successfully"}
