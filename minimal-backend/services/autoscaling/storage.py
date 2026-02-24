"""
Compute Engine Auto-Scaling storage layer.

Handles in-memory storage of autoscaling policies and actions.
"""

from typing import Dict, List, Optional
from datetime import datetime, timezone
import uuid

from .models import (
    AutoscalingPolicy,
    ScalingRule,
    ScalingAction,
    AutoscalerStatus,
    ScalingMetricType,
)


class AutoscalingStorage:
    """In-memory storage for autoscaling policies."""

    def __init__(self):
        """Initialize storage containers."""
        # Structure: {project_id: {zone: {policy_id: AutoscalingPolicy}}}
        self.policies: Dict[str, Dict[str, Dict[str, AutoscalingPolicy]]] = {}

        # Scaling action history: {project_id: [ScalingAction]}
        self.scaling_actions: Dict[str, List[ScalingAction]] = {}

        # Autoscaler status cache: {project_id: {zone: {policy_id: AutoscalerStatus}}}
        self.status_cache: Dict[str, Dict[str, Dict[str, AutoscalerStatus]]] = {}

    # ========== POLICIES ==========

    def create_policy(
        self,
        project: str,
        zone: str,
        policy_id: str,
        target: str,
        min_replicas: int = 1,
        max_replicas: int = 10,
        description: str = None,
        scaling_rules: List[Dict] = None,
    ) -> AutoscalingPolicy:
        """Create a new autoscaling policy."""
        if project not in self.policies:
            self.policies[project] = {}
        if zone not in self.policies[project]:
            self.policies[project][zone] = {}

        # Convert rule dicts to ScalingRule objects
        rules = []
        if scaling_rules:
            for rule_data in scaling_rules:
                rule = ScalingRule(
                    metric_type=ScalingMetricType(rule_data.get("metricType", "CPU_UTILIZATION")),
                    target_value=rule_data.get("targetValue", 70.0),
                    metric_name=rule_data.get("metricName"),
                    scale_up_threshold=rule_data.get("scaleUpThreshold", 80.0),
                    scale_down_threshold=rule_data.get("scaleDownThreshold", 20.0),
                    cooldown_seconds=rule_data.get("cooldownSeconds", 300),
                )
                rules.append(rule)

        # Default to CPU utilization rule if none specified
        if not rules:
            rules.append(ScalingRule(
                metric_type=ScalingMetricType.CPU_UTILIZATION,
                target_value=70.0,
                scale_up_threshold=80.0,
                scale_down_threshold=20.0,
            ))

        policy_name = f"projects/{project}/zones/{zone}/autoscalers/{policy_id}"
        policy = AutoscalingPolicy(
            name=policy_name,
            description=description,
            target=target,
            min_replicas=min_replicas,
            max_replicas=max_replicas,
            scaling_rules=rules,
            current_size=min_replicas,
            target_size=min_replicas,
        )

        self.policies[project][zone][policy_id] = policy

        # Initialize scaling history
        if project not in self.scaling_actions:
            self.scaling_actions[project] = []

        return policy

    def get_policy(self, project: str, zone: str, policy_id: str) -> Optional[AutoscalingPolicy]:
        """Retrieve a policy."""
        return self.policies.get(project, {}).get(zone, {}).get(policy_id)

    def list_policies(self, project: str, zone: Optional[str] = None) -> List[AutoscalingPolicy]:
        """List autoscaling policies."""
        policies = []
        if zone:
            policies = list(self.policies.get(project, {}).get(zone, {}).values())
        else:
            for zones in self.policies.get(project, {}).values():
                policies.extend(list(zones.values()))
        return policies

    def update_policy(
        self,
        project: str,
        zone: str,
        policy_id: str,
        min_replicas: Optional[int] = None,
        max_replicas: Optional[int] = None,
        scaling_rules: Optional[List[Dict]] = None,
        enabled: Optional[bool] = None,
    ) -> Optional[AutoscalingPolicy]:
        """Update a policy."""
        policy = self.get_policy(project, zone, policy_id)
        if not policy:
            return None

        if min_replicas is not None:
            policy.min_replicas = min_replicas
        if max_replicas is not None:
            policy.max_replicas = max_replicas
        if scaling_rules is not None:
            # Rebuild rules
            rules = []
            for rule_data in scaling_rules:
                rule = ScalingRule(
                    metric_type=ScalingMetricType(rule_data.get("metricType", "CPU_UTILIZATION")),
                    target_value=rule_data.get("targetValue", 70.0),
                    metric_name=rule_data.get("metricName"),
                    scale_up_threshold=rule_data.get("scaleUpThreshold", 80.0),
                    scale_down_threshold=rule_data.get("scaleDownThreshold", 20.0),
                )
                rules.append(rule)
            policy.scaling_rules = rules
        if enabled is not None:
            policy.enabled = enabled

        policy.updated_at = datetime.now(timezone.utc).isoformat()
        return policy

    def delete_policy(self, project: str, zone: str, policy_id: str) -> None:
        """Delete a policy."""
        if project in self.policies and zone in self.policies[project]:
            self.policies[project][zone].pop(policy_id, None)

    def policy_exists(self, project: str, zone: str, policy_id: str) -> bool:
        """Check if policy exists."""
        return policy_id in self.policies.get(project, {}).get(zone, {})

    # ========== SCALING ACTIONS ==========

    def record_action(
        self,
        project: str,
        policy_name: str,
        action: str,
        old_size: int,
        new_size: int,
        reason: str,
        metric_value: float,
    ) -> ScalingAction:
        """Record a scaling action."""
        if project not in self.scaling_actions:
            self.scaling_actions[project] = []

        scaling_action = ScalingAction(
            timestamp=datetime.now(timezone.utc).isoformat(),
            policy_name=policy_name,
            action=action,
            old_size=old_size,
            new_size=new_size,
            reason=reason,
            metric_value=metric_value,
        )

        self.scaling_actions[project].append(scaling_action)
        return scaling_action

    def get_scaling_actions(
        self,
        project: str,
        policy_id: Optional[str] = None,
        limit: int = 100,
    ) -> List[ScalingAction]:
        """Get scaling actions history."""
        actions = self.scaling_actions.get(project, [])
        if policy_id:
            actions = [a for a in actions if policy_id in a.policy_name]
        return actions[-limit:]

    # ========== STATUS ==========

    def update_status(
        self,
        project: str,
        zone: str,
        policy_id: str,
        current_replicas: int,
        desired_replicas: int,
        current_metric_value: Optional[float] = None,
        status_message: str = "OK",
    ) -> AutoscalerStatus:
        """Update or create autoscaler status."""
        if project not in self.status_cache:
            self.status_cache[project] = {}
        if zone not in self.status_cache[project]:
            self.status_cache[project][zone] = {}

        status = AutoscalerStatus(
            policy_name=f"projects/{project}/zones/{zone}/autoscalers/{policy_id}",
            current_replicas=current_replicas,
            desired_replicas=desired_replicas,
            current_metric_value=current_metric_value,
            status_message=status_message,
        )

        self.status_cache[project][zone][policy_id] = status
        return status

    def get_status(self, project: str, zone: str, policy_id: str) -> Optional[AutoscalerStatus]:
        """Get autoscaler status."""
        return self.status_cache.get(project, {}).get(zone, {}).get(policy_id)

    def get_all_statuses(self, project: str, zone: Optional[str] = None) -> List[AutoscalerStatus]:
        """Get all autoscaler statuses."""
        statuses = []
        if zone:
            statuses = list(self.status_cache.get(project, {}).get(zone, {}).values())
        else:
            for zones in self.status_cache.get(project, {}).values():
                statuses.extend(list(zones.values()))
        return statuses

    # ========== HEALTH CHECK ==========

    def health_check(self) -> Dict[str, int]:
        """Return storage statistics."""
        total_policies = sum(
            len(zones)
            for zones in self.policies.get(project, {}).values()
            for project in self.policies
        )
        total_actions = sum(len(actions) for actions in self.scaling_actions.values())
        total_statuses = sum(
            len(zones)
            for zones in self.status_cache.get(project, {}).values()
            for project in self.status_cache
        )

        return {
            "policies": total_policies,
            "scaling_actions": total_actions,
            "statuses": total_statuses,
        }
