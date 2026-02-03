"""Project Management API"""
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from database import get_db, Project

router = APIRouter()

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
