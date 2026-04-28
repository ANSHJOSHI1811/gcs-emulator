"""
Compute Engine Auto-Scaling models.

Defines AutoscalingPolicy, ScalingRule, and related classes
for GCP Autoscaling service simulator.
"""

from dataclasses import dataclass, field, asdict
from datetime import datetime, timezone
from enum import Enum
from typing import Optional, List, Dict, Any
import uuid


class ScalingMetricType(str, Enum):
    """Type of metric to scale on."""
    CPU_UTILIZATION = "CPU_UTILIZATION"
    MEMORY_UTILIZATION = "MEMORY_UTILIZATION"
    CUSTOM_METRIC = "CUSTOM_METRIC"
    LB_SERVING_CAPACITY = "LB_SERVING_CAPACITY"
    PUBSUB_MESSAGE_BACKLOG = "PUBSUB_MESSAGE_BACKLOG"


@dataclass
class ScalingRule:
    """A single scaling rule based on metrics."""
    metric_type: ScalingMetricType
    target_value: float                 # Target metric value (e.g., 70 for 70% CPU)
    metric_name: Optional[str] = None   # For custom metrics
    scale_up_threshold: float = 80.0    # Scale up if metric > this
    scale_down_threshold: float = 20.0  # Scale down if metric < this
    cooldown_seconds: int = 300         # Wait before next scaling action

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "metricType": self.metric_type.value,
            "targetValue": self.target_value,
            "metricName": self.metric_name,
            "scaleUpThreshold": self.scale_up_threshold,
            "scaleDownThreshold": self.scale_down_threshold,
            "cooldownSeconds": self.cooldown_seconds,
        }


@dataclass
class AutoscalingPolicy:
    """Autoscaling policy for an instance group or node pool."""
    name: str                           # projects/{p}/zones/{z}/instanceGroupManagers/{igm}/autoscaler/{name}
    description: Optional[str] = None
    target: str = ""                    # Target instance group/node pool name
    min_replicas: int = 1
    max_replicas: int = 10
    target_size: Optional[int] = None   # Current target size
    current_size: int = 1               # Current number of instances
    scaling_rules: List[ScalingRule] = field(default_factory=list)
    enabled: bool = True
    created_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    updated_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    
    # Scaling history and state
    last_scaling_time: Optional[str] = None
    last_action: Optional[str] = None   # "SCALED_UP", "SCALED_DOWN", "IDLE"
    status: str = "ACTIVE"              # ACTIVE, DELETED, PENDING_CREATION

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "name": self.name,
            "description": self.description,
            "target": self.target,
            "minReplicas": self.min_replicas,
            "maxReplicas": self.max_replicas,
            "targetSize": self.target_size,
            "currentSize": self.current_size,
            "scalingRules": [r.to_dict() for r in self.scaling_rules],
            "enabled": self.enabled,
            "createdAt": self.created_at,
            "updatedAt": self.updated_at,
            "lastScalingTime": self.last_scaling_time,
            "lastAction": self.last_action,
            "status": self.status,
        }


@dataclass
class ScalingAction:
    """Record of a scaling action taken."""
    timestamp: str
    policy_name: str
    action: str                         # "SCALE_UP", "SCALE_DOWN", "IDLE"
    old_size: int
    new_size: int
    reason: str                         # Why the action was taken
    metric_value: float                 # The metric value that triggered it

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "timestamp": self.timestamp,
            "policyName": self.policy_name,
            "action": self.action,
            "oldSize": self.old_size,
            "newSize": self.new_size,
            "reason": self.reason,
            "metricValue": self.metric_value,
        }


@dataclass
class AutoscalerStatus:
    """Current status of an autoscaler."""
    policy_name: str
    current_replicas: int
    desired_replicas: int
    proposed_size: Optional[int] = None
    current_metric_value: Optional[float] = None
    status_message: str = "OK"

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "policyName": self.policy_name,
            "currentReplicas": self.current_replicas,
            "desiredReplicas": self.desired_replicas,
            "proposedSize": self.proposed_size,
            "currentMetricValue": self.current_metric_value,
            "statusMessage": self.status_message,
        }
