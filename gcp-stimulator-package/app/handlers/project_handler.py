"""
Project Handler - Project Management

Handles:
- List all projects
- Create new project
- Get project details
- Delete project
"""

from flask import Blueprint, jsonify, request
from app.factory import db
from app.models.project import Project
from datetime import datetime
import random

project_bp = Blueprint("projects", __name__)


@project_bp.route("/cloudresourcemanager/v1/projects", methods=["GET"])
def list_projects():
    """List all projects"""
    try:
        projects = Project.query.all()
        
        return jsonify({
            "projects": [
                {
                    "projectId": p.id,
                    "name": p.name,
                    "projectNumber": str(p.project_number) if p.project_number else str(random.randint(100000000000, 999999999999)),
                    "lifecycleState": "ACTIVE",
                    "createTime": p.created_at.isoformat() if p.created_at else datetime.utcnow().isoformat()
                }
                for p in projects
            ]
        }), 200
        
    except Exception as e:
        return jsonify({"error": {"message": str(e)}}), 500


@project_bp.route("/cloudresourcemanager/v1/projects", methods=["POST"])
def create_project():
    """Create a new project"""
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({"error": {"message": "Request body is required"}}), 400
        
        project_id = data.get("projectId")
        name = data.get("name", project_id)
        
        if not project_id:
            return jsonify({"error": {"message": "projectId is required"}}), 400
        
        # Check if project already exists
        existing = Project.query.filter_by(id=project_id).first()
        if existing:
            return jsonify({
                "error": {
                    "code": 409,
                    "message": f"Project {project_id} already exists",
                    "status": "ALREADY_EXISTS"
                }
            }), 409
        
        # Create project
        project = Project(
            id=project_id,
            name=name,
            project_number=random.randint(100000000000, 999999999999),
            created_at=datetime.utcnow(),
            compute_api_enabled=True
        )
        
        db.session.add(project)
        db.session.commit()
        
        return jsonify({
            "projectId": project.id,
            "name": project.name,
            "projectNumber": str(project.project_number),
            "lifecycleState": "ACTIVE",
            "createTime": project.created_at.isoformat()
        }), 201
        
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": {"message": str(e)}}), 500


@project_bp.route("/cloudresourcemanager/v1/projects/<project_id>", methods=["GET"])
def get_project(project_id):
    """Get project details"""
    try:
        project = Project.query.filter_by(id=project_id).first()
        
        if not project:
            return jsonify({
                "error": {
                    "code": 404,
                    "message": f"Project {project_id} not found",
                    "status": "NOT_FOUND"
                }
            }), 404
        
        return jsonify({
            "projectId": project.id,
            "name": project.name,
            "projectNumber": str(project.project_number) if project.project_number else str(random.randint(100000000000, 999999999999)),
            "lifecycleState": "ACTIVE",
            "createTime": project.created_at.isoformat() if project.created_at else datetime.utcnow().isoformat()
        }), 200
        
    except Exception as e:
        return jsonify({"error": {"message": str(e)}}), 500


@project_bp.route("/cloudresourcemanager/v1/projects/<project_id>", methods=["DELETE"])
def delete_project(project_id):
    """Delete a project"""
    try:
        project = Project.query.filter_by(id=project_id).first()
        
        if not project:
            return jsonify({
                "error": {
                    "code": 404,
                    "message": f"Project {project_id} not found",
                    "status": "NOT_FOUND"
                }
            }), 404
        
        db.session.delete(project)
        db.session.commit()
        
        return jsonify({}), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": {"message": str(e)}}), 500
