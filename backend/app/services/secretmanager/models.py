"""
Secret Manager data models for secret storage and versioning.

Represents secrets, versions, and replication configuration.
"""

from dataclasses import dataclass, field, asdict
from datetime import datetime, timezone
from typing import Optional, Dict, List, Any
import secrets
import string

# ============================================================================
# ENUMS
# ============================================================================

class ReplicationPolicy:
    """Secret replication strategies."""
    AUTOMATIC = "AUTOMATIC"
    USER_MANAGED = "USER_MANAGED"


class SecretVersionState:
    """Secret version lifecycle states."""
    ENABLED = "ENABLED"
    DISABLED = "DISABLED"
    DESTROYED = "DESTROYED"


# ============================================================================
# DATA MODELS
# ============================================================================

@dataclass
class Replication:
    """Replication configuration for secrets."""
    policy: str = ReplicationPolicy.AUTOMATIC  # AUTOMATIC or USER_MANAGED
    locations: List[str] = field(default_factory=list)  # For USER_MANAGED

    def to_dict(self) -> Dict[str, Any]:
        data = {
            'automatic': {} if self.policy == ReplicationPolicy.AUTOMATIC else None,
        }
        if self.policy == ReplicationPolicy.USER_MANAGED:
            data['userManaged'] = {
                'replicas': [{'location': loc} for loc in self.locations]
            }
        return {k: v for k, v in data.items() if v is not None}


@dataclass
class SecretVersion:
    """Represents a version of a secret."""
    secret_id: str                           # Reference to parent secret
    project_id: str                          # GCP project
    version_id: str                          # Version identifier (numeric)
    state: str = SecretVersionState.ENABLED  # ENABLED, DISABLED, DESTROYED
    payload: bytes = field(default_factory=bytes)  # Secret data (encrypted in real GCP)
    create_time: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    destroy_time: Optional[datetime] = None

    @property
    def name(self) -> str:
        """Full resource name."""
        return f"projects/{self.project_id}/secrets/{self.secret_id}/versions/{self.version_id}"

    def to_dict(self) -> Dict[str, Any]:
        data = {
            'name': self.name,
            'createTime': self.create_time.isoformat() + 'Z',
            'state': self.state,
        }
        if self.destroy_time:
            data['destroyTime'] = self.destroy_time.isoformat() + 'Z'
        return data


@dataclass
class Secret:
    """Represents a secret with metadata and versions."""
    secret_id: str                           # Secret name
    project_id: str                          # GCP project
    labels: Dict[str, str] = field(default_factory=dict)
    description: str = ""
    replication: Optional[Replication] = None
    created_time: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    updated_time: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    
    # Internal tracking
    next_version_id: int = 1  # For generating version IDs
    versions: Dict[str, SecretVersion] = field(default_factory=dict)  # version_id -> SecretVersion
    current_version_id: Optional[str] = None  # Latest enabled version

    @property
    def name(self) -> str:
        """Full resource name."""
        return f"projects/{self.project_id}/secrets/{self.secret_id}"

    def to_dict(self) -> Dict[str, Any]:
        replication_dict = self.replication.to_dict() if self.replication else {}
        
        return {
            'name': self.name,
            'replication': replication_dict,
            'createTime': self.created_time.isoformat() + 'Z',
            'labels': self.labels,
            'description': self.description,
        }

    def add_version(self, payload: bytes) -> SecretVersion:
        """Add a new version to this secret."""
        version_id = str(self.next_version_id)
        self.next_version_id += 1
        
        version = SecretVersion(
            secret_id=self.secret_id,
            project_id=self.project_id,
            version_id=version_id,
            payload=payload,
            state=SecretVersionState.ENABLED
        )
        
        self.versions[version_id] = version
        self.current_version_id = version_id
        self.updated_time = datetime.now(timezone.utc)
        
        return version

    def get_latest_version(self) -> Optional[SecretVersion]:
        """Get the latest enabled version."""
        if not self.current_version_id:
            return None
        version = self.versions.get(self.current_version_id)
        if version and version.state == SecretVersionState.ENABLED:
            return version
        return None


# ============================================================================
# REQUEST/RESPONSE MODELS
# ============================================================================

@dataclass
class CreateSecretRequest:
    """Request to create a new secret."""
    secret_id: str                           # Secret name
    replication: Optional[Dict[str, Any]] = None
    labels: Dict[str, str] = field(default_factory=dict)
    description: str = ""


@dataclass
class AddSecretVersionRequest:
    """Request to add a version to an existing secret."""
    payload: bytes  # Secret data


@dataclass
class AccessSecretVersionRequest:
    """Request to access (read) a secret version."""
    version: str = "latest"  # Version ID or "latest"


@dataclass
class SecretVersionResponse:
    """Response containing secret version data."""
    name: str                       # Full resource name
    version: str                    # Version ID
    payload: bytes                  # Secret data


# ============================================================================
# UTILITY FUNCTIONS
# ============================================================================

def generate_random_password(
    length: int = 32,
    include_uppercase: bool = True,
    include_lowercase: bool = True,
    include_digits: bool = True,
    include_symbols: bool = True,
    exclude_ambiguous: bool = True
) -> str:
    """
    Generate a random password with complexity options.
    
    Args:
        length: Password length (default 32)
        include_uppercase: Include A-Z
        include_lowercase: Include a-z
        include_digits: Include 0-9
        include_symbols: Include !@#$%^&*
        exclude_ambiguous: Exclude ambiguous chars (0, O, l, 1, etc)
    
    Returns:
        Generated password string
    """
    
    charset = ""
    
    if include_uppercase:
        chars = string.ascii_uppercase
        if exclude_ambiguous:
            chars = chars.replace('O', '').replace('I', '')
        charset += chars
    
    if include_lowercase:
        chars = string.ascii_lowercase
        if exclude_ambiguous:
            chars = chars.replace('l', '').replace('o', '')
        charset += chars
    
    if include_digits:
        chars = string.digits
        if exclude_ambiguous:
            chars = chars.replace('0', '').replace('1', '')
        charset += chars
    
    if include_symbols:
        charset += "!@#$%^&*"
    
    if not charset:
        charset = string.ascii_letters + string.digits
    
    # Generate password ensuring at least one char from each category
    password_chars = []
    
    if include_uppercase:
        chars = string.ascii_uppercase
        if exclude_ambiguous:
            chars = chars.replace('O', '').replace('I', '')
        password_chars.append(secrets.choice(chars))
    
    if include_lowercase:
        chars = string.ascii_lowercase
        if exclude_ambiguous:
            chars = chars.replace('l', '').replace('o', '')
        password_chars.append(secrets.choice(chars))
    
    if include_digits:
        chars = string.digits
        if exclude_ambiguous:
            chars = chars.replace('0', '').replace('1', '')
        password_chars.append(secrets.choice(chars))
    
    if include_symbols:
        password_chars.append(secrets.choice("!@#$%^&*"))
    
    # Fill remaining length with random chars from full charset
    while len(password_chars) < length:
        password_chars.append(secrets.choice(charset))
    
    # Shuffle to randomize order
    shuffled = list(password_chars)
    for i in range(len(shuffled) - 1, 0, -1):
        j = secrets.randbelow(i + 1)
        shuffled[i], shuffled[j] = shuffled[j], shuffled[i]
    
    return ''.join(shuffled)
