"""
IAM Service - Business logic for IAM operations
"""
from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta
import json
import base64
from app.models.service_account import ServiceAccount, ServiceAccountKey
from app.models.iam_policy import IAMPolicy, IAMBinding, Role
from app.repositories.iam_repository import (
    ServiceAccountRepository, ServiceAccountKeyRepository,
    IAMPolicyRepository, IAMBindingRepository, RoleRepository
)


class ServiceAccountService:
    """Service for managing service accounts"""
    
    def __init__(self):
        self.repo = ServiceAccountRepository()
        self.key_repo = ServiceAccountKeyRepository()
    
    def create_service_account(
        self, 
        project_id: str, 
        account_id: str,
        display_name: Optional[str] = None,
        description: Optional[str] = None
    ) -> ServiceAccount:
        """Create a new service account"""
        # Generate email
        email = f"{account_id}@{project_id}.iam.gserviceaccount.com"
        
        # Check if already exists
        if self.repo.exists(email):
            raise ValueError(f"Service account {email} already exists")
        
        # Create service account
        service_account = ServiceAccount(
            email=email,
            project_id=project_id,
            name=account_id,
            display_name=display_name or account_id,
            description=description,
            unique_id=ServiceAccount.generate_unique_id(),
            oauth2_client_id=ServiceAccount.generate_unique_id(),
        )
        
        return self.repo.create(service_account)
    
    def get_service_account(self, email: str) -> Optional[ServiceAccount]:
        """Get service account by email"""
        return self.repo.get_by_email(email)
    
    def list_service_accounts(self, project_id: str) -> List[ServiceAccount]:
        """List all service accounts for a project"""
        return self.repo.get_by_project(project_id)
    
    def update_service_account(
        self,
        email: str,
        display_name: Optional[str] = None,
        description: Optional[str] = None
    ) -> ServiceAccount:
        """Update service account"""
        service_account = self.repo.get_by_email(email)
        if not service_account:
            raise ValueError(f"Service account {email} not found")
        
        if display_name is not None:
            service_account.display_name = display_name
        if description is not None:
            service_account.description = description
        
        return self.repo.update(service_account)
    
    def delete_service_account(self, email: str) -> None:
        """Delete a service account"""
        service_account = self.repo.get_by_email(email)
        if not service_account:
            raise ValueError(f"Service account {email} not found")
        
        self.repo.delete(service_account)
    
    def disable_service_account(self, email: str) -> ServiceAccount:
        """Disable a service account"""
        service_account = self.repo.get_by_email(email)
        if not service_account:
            raise ValueError(f"Service account {email} not found")
        
        service_account.disabled = True
        return self.repo.update(service_account)
    
    def enable_service_account(self, email: str) -> ServiceAccount:
        """Enable a service account"""
        service_account = self.repo.get_by_email(email)
        if not service_account:
            raise ValueError(f"Service account {email} not found")
        
        service_account.disabled = False
        return self.repo.update(service_account)
    
    def create_key(
        self,
        email: str,
        key_algorithm: str = "KEY_ALG_RSA_2048",
        private_key_type: str = "TYPE_GOOGLE_CREDENTIALS_FILE"
    ) -> ServiceAccountKey:
        """Create a new key for service account"""
        service_account = self.repo.get_by_email(email)
        if not service_account:
            raise ValueError(f"Service account {email} not found")
        
        # Generate key ID
        import secrets
        key_id = secrets.token_hex(20)
        key_name = f"projects/{service_account.project_id}/serviceAccounts/{email}/keys/{key_id}"
        
        # Generate mock credentials JSON
        credentials = {
            "type": "service_account",
            "project_id": service_account.project_id,
            "private_key_id": key_id,
            "private_key": "-----BEGIN PRIVATE KEY-----\\nMOCK_KEY_DATA\\n-----END PRIVATE KEY-----\\n",
            "client_email": email,
            "client_id": service_account.oauth2_client_id,
            "auth_uri": "https://accounts.google.com/o/oauth2/auth",
            "token_uri": "https://oauth2.googleapis.com/token",
            "auth_provider_x509_cert_url": "https://www.googleapis.com/oauth2/v1/certs",
            "client_x509_cert_url": f"https://www.googleapis.com/robot/v1/metadata/x509/{email}"
        }
        
        # Base64 encode credentials
        private_key_data = base64.b64encode(json.dumps(credentials).encode()).decode()
        
        # Create key
        key = ServiceAccountKey(
            id=key_name,
            service_account_email=email,
            key_algorithm=key_algorithm,
            private_key_data=private_key_data,
            valid_after_time=datetime.utcnow(),
            valid_before_time=datetime.utcnow() + timedelta(days=365)  # 1 year validity
        )
        
        return self.key_repo.create(key)
    
    def list_keys(self, email: str) -> List[ServiceAccountKey]:
        """List all keys for a service account"""
        return self.key_repo.get_by_service_account(email)
    
    def get_key(self, key_id: str) -> Optional[ServiceAccountKey]:
        """Get a service account key"""
        return self.key_repo.get_by_id(key_id)
    
    def delete_key(self, key_id: str) -> None:
        """Delete a service account key"""
        key = self.key_repo.get_by_id(key_id)
        if not key:
            raise ValueError(f"Key {key_id} not found")
        
        self.key_repo.delete(key)


class IAMPolicyService:
    """Service for managing IAM policies"""
    
    def __init__(self):
        self.policy_repo = IAMPolicyRepository()
        self.binding_repo = IAMBindingRepository()
    
    def get_iam_policy(self, resource_name: str, resource_type: str) -> IAMPolicy:
        """Get IAM policy for a resource"""
        return self.policy_repo.get_or_create(resource_name, resource_type)
    
    def set_iam_policy(
        self,
        resource_name: str,
        resource_type: str,
        bindings: List[Dict[str, Any]],
        version: int = 1,
        etag: Optional[str] = None
    ) -> IAMPolicy:
        """Set IAM policy for a resource"""
        policy = self.policy_repo.get_or_create(resource_name, resource_type)
        
        # Check etag for optimistic concurrency control
        if etag and policy.etag and policy.etag != etag:
            raise ValueError("ETag mismatch - policy was modified")
        
        # Delete existing bindings
        self.binding_repo.delete_all_for_policy(policy.id)
        
        # Create new bindings
        for binding_data in bindings:
            binding = IAMBinding(
                policy_id=policy.id,
                role=binding_data.get("role"),
                members=binding_data.get("members", []),
                condition=binding_data.get("condition")
            )
            self.binding_repo.create(binding)
        
        # Update policy version and etag
        policy.version = version
        return self.policy_repo.update(policy)
    
    def add_binding(
        self,
        resource_name: str,
        resource_type: str,
        role: str,
        member: str
    ) -> IAMPolicy:
        """Add a member to a role binding"""
        policy = self.policy_repo.get_or_create(resource_name, resource_type)
        
        # Find existing binding for role
        binding = self.binding_repo.get_by_policy_and_role(policy.id, role)
        
        if binding:
            # Add member if not already present
            if member not in binding.members:
                binding.members.append(member)
                self.policy_repo.update(policy)
        else:
            # Create new binding
            binding = IAMBinding(
                policy_id=policy.id,
                role=role,
                members=[member]
            )
            self.binding_repo.create(binding)
            self.policy_repo.update(policy)
        
        return policy
    
    def remove_binding(
        self,
        resource_name: str,
        resource_type: str,
        role: str,
        member: str
    ) -> IAMPolicy:
        """Remove a member from a role binding"""
        policy = self.policy_repo.get_by_resource(resource_name)
        if not policy:
            raise ValueError(f"Policy for {resource_name} not found")
        
        binding = self.binding_repo.get_by_policy_and_role(policy.id, role)
        if not binding:
            raise ValueError(f"Binding for role {role} not found")
        
        if member in binding.members:
            binding.members.remove(member)
            if not binding.members:
                # Delete binding if no members left
                self.binding_repo.delete(binding)
            self.policy_repo.update(policy)
        
        return policy
    
    def test_iam_permissions(
        self,
        resource_name: str,
        permissions: List[str]
    ) -> List[str]:
        """Test which permissions the caller has on a resource"""
        # In a real implementation, this would check actual permissions
        # For emulator, we return all requested permissions as granted
        return permissions


class RoleService:
    """Service for managing IAM roles"""
    
    def __init__(self):
        self.repo = RoleRepository()
    
    def create_role(
        self,
        project_id: str,
        role_id: str,
        title: str,
        description: Optional[str] = None,
        included_permissions: Optional[List[str]] = None,
        stage: str = "GA"
    ) -> Role:
        """Create a custom role"""
        # Generate role name
        role_name = f"projects/{project_id}/roles/{role_id}"
        
        # Check if already exists
        if self.repo.exists(role_name):
            raise ValueError(f"Role {role_name} already exists")
        
        role = Role(
            name=role_name,
            title=title,
            description=description,
            stage=stage,
            is_custom=True,
            project_id=project_id,
            included_permissions=included_permissions or []
        )
        
        return self.repo.create(role)
    
    def get_role(self, role_name: str) -> Optional[Role]:
        """Get a role by name"""
        return self.repo.get_by_name(role_name)
    
    def list_roles(self, project_id: Optional[str] = None) -> List[Role]:
        """List roles (custom for project or predefined)"""
        if project_id:
            return self.repo.get_by_project(project_id)
        else:
            return self.repo.get_predefined_roles()
    
    def update_role(
        self,
        role_name: str,
        title: Optional[str] = None,
        description: Optional[str] = None,
        included_permissions: Optional[List[str]] = None,
        stage: Optional[str] = None
    ) -> Role:
        """Update a custom role"""
        role = self.repo.get_by_name(role_name)
        if not role:
            raise ValueError(f"Role {role_name} not found")
        
        if not role.is_custom:
            raise ValueError("Cannot update predefined roles")
        
        if title is not None:
            role.title = title
        if description is not None:
            role.description = description
        if included_permissions is not None:
            role.included_permissions = included_permissions
        if stage is not None:
            role.stage = stage
        
        return self.repo.update(role)
    
    def delete_role(self, role_name: str) -> Role:
        """Delete (soft delete) a custom role"""
        role = self.repo.get_by_name(role_name)
        if not role:
            raise ValueError(f"Role {role_name} not found")
        
        if not role.is_custom:
            raise ValueError("Cannot delete predefined roles")
        
        return self.repo.soft_delete(role)
    
    def undelete_role(self, role_name: str) -> Role:
        """Undelete a custom role"""
        role = self.repo.get_by_name(role_name)
        if not role:
            raise ValueError(f"Role {role_name} not found")
        
        return self.repo.undelete(role)
    
    def seed_predefined_roles(self) -> None:
        """Seed predefined GCS roles"""
        predefined_roles = [
            {
                "name": "roles/storage.objectViewer",
                "title": "Storage Object Viewer",
                "description": "Grants permission to view objects and their metadata",
                "permissions": ["storage.objects.get", "storage.objects.list"]
            },
            {
                "name": "roles/storage.objectCreator",
                "title": "Storage Object Creator",
                "description": "Grants permission to create objects",
                "permissions": ["storage.objects.create"]
            },
            {
                "name": "roles/storage.objectAdmin",
                "title": "Storage Object Admin",
                "description": "Full control of GCS objects",
                "permissions": [
                    "storage.objects.get", "storage.objects.list",
                    "storage.objects.create", "storage.objects.update",
                    "storage.objects.delete"
                ]
            },
            {
                "name": "roles/storage.admin",
                "title": "Storage Admin",
                "description": "Full control of GCS resources",
                "permissions": [
                    "storage.buckets.get", "storage.buckets.list",
                    "storage.buckets.create", "storage.buckets.update",
                    "storage.buckets.delete",
                    "storage.objects.get", "storage.objects.list",
                    "storage.objects.create", "storage.objects.update",
                    "storage.objects.delete"
                ]
            },
            {
                "name": "roles/owner",
                "title": "Owner",
                "description": "Full access to all resources",
                "permissions": ["*"]
            },
            {
                "name": "roles/editor",
                "title": "Editor",
                "description": "Edit access to all resources",
                "permissions": ["*"]
            },
            {
                "name": "roles/viewer",
                "title": "Viewer",
                "description": "Read access to all resources",
                "permissions": ["*.get", "*.list"]
            }
        ]
        
        for role_data in predefined_roles:
            if not self.repo.exists(role_data["name"]):
                role = Role(
                    name=role_data["name"],
                    title=role_data["title"],
                    description=role_data["description"],
                    stage="GA",
                    is_custom=False,
                    included_permissions=role_data["permissions"]
                )
                self.repo.create(role)
