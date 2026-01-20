"""
IAM Repository - Data access layer for IAM operations
"""
from typing import List, Optional
from sqlalchemy.exc import IntegrityError
from app.factory import db
from app.models.service_account import ServiceAccount, ServiceAccountKey
from app.models.iam_policy import IAMPolicy, IAMBinding, Role


class ServiceAccountRepository:
    """Repository for ServiceAccount operations"""
    
    @staticmethod
    def create(service_account: ServiceAccount) -> ServiceAccount:
        """Create a new service account"""
        db.session.add(service_account)
        db.session.commit()
        db.session.refresh(service_account)
        return service_account
    
    @staticmethod
    def get_by_email(email: str) -> Optional[ServiceAccount]:
        """Get service account by email"""
        return ServiceAccount.query.filter_by(email=email).first()
    
    @staticmethod
    def get_by_project(project_id: str) -> List[ServiceAccount]:
        """Get all service accounts for a project"""
        return ServiceAccount.query.filter_by(project_id=project_id).all()
    
    @staticmethod
    def update(service_account: ServiceAccount) -> ServiceAccount:
        """Update a service account"""
        db.session.commit()
        db.session.refresh(service_account)
        return service_account
    
    @staticmethod
    def delete(service_account: ServiceAccount) -> None:
        """Delete a service account"""
        db.session.delete(service_account)
        db.session.commit()
    
    @staticmethod
    def exists(email: str) -> bool:
        """Check if service account exists"""
        return db.session.query(
            ServiceAccount.query.filter_by(email=email).exists()
        ).scalar()


class ServiceAccountKeyRepository:
    """Repository for ServiceAccountKey operations"""
    
    @staticmethod
    def create(key: ServiceAccountKey) -> ServiceAccountKey:
        """Create a new service account key"""
        db.session.add(key)
        db.session.commit()
        db.session.refresh(key)
        return key
    
    @staticmethod
    def get_by_id(key_id: str) -> Optional[ServiceAccountKey]:
        """Get service account key by ID"""
        return ServiceAccountKey.query.filter_by(id=key_id).first()
    
    @staticmethod
    def get_by_service_account(email: str) -> List[ServiceAccountKey]:
        """Get all keys for a service account"""
        return ServiceAccountKey.query.filter_by(service_account_email=email).all()
    
    @staticmethod
    def delete(key: ServiceAccountKey) -> None:
        """Delete a service account key"""
        db.session.delete(key)
        db.session.commit()


class IAMPolicyRepository:
    """Repository for IAMPolicy operations"""
    
    @staticmethod
    def create(policy: IAMPolicy) -> IAMPolicy:
        """Create a new IAM policy"""
        db.session.add(policy)
        db.session.commit()
        db.session.refresh(policy)
        return policy
    
    @staticmethod
    def get_by_resource(resource_name: str) -> Optional[IAMPolicy]:
        """Get IAM policy by resource name"""
        return IAMPolicy.query.filter_by(resource_name=resource_name).first()
    
    @staticmethod
    def update(policy: IAMPolicy) -> IAMPolicy:
        """Update an IAM policy"""
        policy.etag = policy._compute_etag()
        db.session.commit()
        db.session.refresh(policy)
        return policy
    
    @staticmethod
    def delete(policy: IAMPolicy) -> None:
        """Delete an IAM policy"""
        db.session.delete(policy)
        db.session.commit()
    
    @staticmethod
    def get_or_create(resource_name: str, resource_type: str) -> IAMPolicy:
        """Get existing policy or create a new one"""
        policy = IAMPolicyRepository.get_by_resource(resource_name)
        if not policy:
            policy = IAMPolicy(
                resource_name=resource_name,
                resource_type=resource_type,
                version=1
            )
            db.session.add(policy)
            db.session.commit()
            db.session.refresh(policy)
        return policy


class IAMBindingRepository:
    """Repository for IAMBinding operations"""
    
    @staticmethod
    def create(binding: IAMBinding) -> IAMBinding:
        """Create a new IAM binding"""
        db.session.add(binding)
        db.session.commit()
        db.session.refresh(binding)
        return binding
    
    @staticmethod
    def get_by_policy(policy_id: int) -> List[IAMBinding]:
        """Get all bindings for a policy"""
        return IAMBinding.query.filter_by(policy_id=policy_id).all()
    
    @staticmethod
    def get_by_policy_and_role(policy_id: int, role: str) -> Optional[IAMBinding]:
        """Get binding by policy and role"""
        return IAMBinding.query.filter_by(policy_id=policy_id, role=role).first()
    
    @staticmethod
    def delete(binding: IAMBinding) -> None:
        """Delete an IAM binding"""
        db.session.delete(binding)
        db.session.commit()
    
    @staticmethod
    def delete_all_for_policy(policy_id: int) -> None:
        """Delete all bindings for a policy"""
        IAMBinding.query.filter_by(policy_id=policy_id).delete()
        db.session.commit()


class RoleRepository:
    """Repository for Role operations"""
    
    @staticmethod
    def create(role: Role) -> Role:
        """Create a new role"""
        db.session.add(role)
        db.session.commit()
        db.session.refresh(role)
        return role
    
    @staticmethod
    def get_by_name(name: str) -> Optional[Role]:
        """Get role by name"""
        return Role.query.filter_by(name=name, deleted=False).first()
    
    @staticmethod
    def get_by_project(project_id: str) -> List[Role]:
        """Get all custom roles for a project"""
        return Role.query.filter_by(project_id=project_id, is_custom=True, deleted=False).all()
    
    @staticmethod
    def get_predefined_roles() -> List[Role]:
        """Get all predefined (non-custom) roles"""
        return Role.query.filter_by(is_custom=False, deleted=False).all()
    
    @staticmethod
    def update(role: Role) -> Role:
        """Update a role"""
        role.etag = role._compute_etag()
        db.session.commit()
        db.session.refresh(role)
        return role
    
    @staticmethod
    def soft_delete(role: Role) -> Role:
        """Soft delete a role"""
        role.deleted = True
        db.session.commit()
        db.session.refresh(role)
        return role
    
    @staticmethod
    def undelete(role: Role) -> Role:
        """Undelete a role"""
        role.deleted = False
        db.session.commit()
        db.session.refresh(role)
        return role
    
    @staticmethod
    def exists(name: str) -> bool:
        """Check if role exists"""
        return db.session.query(
            Role.query.filter_by(name=name).exists()
        ).scalar()
