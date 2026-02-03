"""IAM & Admin API endpoints"""
from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from sqlalchemy.orm import Session
from typing import Dict, Any, Optional, List
from datetime import datetime
import random

from database import get_db, ServiceAccount as DBServiceAccount

router = APIRouter()


class ServiceAccountCreate(BaseModel):
    displayName: Optional[str] = None
    description: Optional[str] = None


class ServiceAccountRequest(BaseModel):
    accountId: str
    serviceAccount: Optional[ServiceAccountCreate] = None


@router.get("/projects/{project}/serviceAccounts")
def list_service_accounts(project: str, db: Session = Depends(get_db)) -> Dict[str, Any]:
    """List service accounts for a project"""
    accounts = db.query(DBServiceAccount).filter(
        DBServiceAccount.project_id == project
    ).all()
    
    items = []
    for account in accounts:
        items.append({
            "name": f"projects/{project}/serviceAccounts/{account.id}",
            "email": account.id,
            "displayName": account.display_name or "",
            "uniqueId": account.unique_id,
            "projectId": account.project_id,
            "disabled": account.disabled,
            "description": account.description or ""
        })
    
    return {"accounts": items}


@router.post("/projects/{project}/serviceAccounts")
def create_service_account(
    project: str,
    payload: ServiceAccountRequest,
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """Create a new service account"""
    
    # Generate email
    email = f"{payload.accountId}@{project}.iam.gserviceaccount.com"
    
    # Check if service account already exists
    existing = db.query(DBServiceAccount).filter(DBServiceAccount.id == email).first()
    if existing:
        raise HTTPException(status_code=409, detail="Service account already exists")
    
    # Generate unique numeric ID
    unique_id = str(random.randint(100000000000000000000, 999999999999999999999))
    
    # Create service account
    now = datetime.utcnow()
    service_account = DBServiceAccount(
        id=email,
        project_id=project,
        email=email,
        display_name=payload.serviceAccount.displayName if payload.serviceAccount else None,
        description=payload.serviceAccount.description if payload.serviceAccount else None,
        unique_id=unique_id,
        disabled=False,
        created_at=now,
        updated_at=now
    )
    
    db.add(service_account)
    db.commit()
    db.refresh(service_account)
    
    return {
        "name": f"projects/{project}/serviceAccounts/{email}",
        "email": email,
        "displayName": service_account.display_name or "",
        "uniqueId": unique_id,
        "projectId": project,
        "disabled": False,
        "description": service_account.description or ""
    }


@router.get("/projects/{project}/serviceAccounts/{email}")
def get_service_account(
    project: str,
    email: str,
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """Get a service account by email"""
    
    account = db.query(DBServiceAccount).filter(
        DBServiceAccount.id == email,
        DBServiceAccount.project_id == project
    ).first()
    
    if not account:
        raise HTTPException(status_code=404, detail="Service account not found")
    
    return {
        "name": f"projects/{project}/serviceAccounts/{email}",
        "email": account.id,
        "displayName": account.display_name or "",
        "uniqueId": account.unique_id,
        "projectId": account.project_id,
        "disabled": account.disabled,
        "description": account.description or ""
    }


@router.delete("/projects/{project}/serviceAccounts/{email}")
def delete_service_account(
    project: str,
    email: str,
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """Delete a service account"""
    
    account = db.query(DBServiceAccount).filter(
        DBServiceAccount.id == email,
        DBServiceAccount.project_id == project
    ).first()
    
    if not account:
        raise HTTPException(status_code=404, detail="Service account not found")
    
    db.delete(account)
    db.commit()
    
    return {"message": "Service account deleted"}


@router.get("/projects/{project}/serviceAccounts/{email}/keys")
def list_service_account_keys(
    project: str,
    email: str,
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """List keys for a service account (placeholder)"""
    
    account = db.query(DBServiceAccount).filter(
        DBServiceAccount.id == email,
        DBServiceAccount.project_id == project
    ).first()
    
    if not account:
        raise HTTPException(status_code=404, detail="Service account not found")
    
    # Return empty list - key management not implemented yet
    return {"keys": []}
