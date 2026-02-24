"""
Auto-Scaling Evaluator.

Background task that continuously evaluates autoscaling policies and takes actions.
"""

import asyncio
import random
import logging
from datetime import datetime, timezone, timedelta
from typing import Optional

from .storage import AutoscalingStorage
from .models import ScalingMetricType

logger = logging.getLogger(__name__)


class AutoscalingEvaluator:
    """Evaluates autoscaling policies and scales resources."""

    def __init__(self, storage: AutoscalingStorage, monitoring_storage=None, compute_storage=None):
        """
        Initialize with autoscaling storage and optional monitoring/compute storage.
        
        Args:
            storage: AutoscalingStorage instance
            monitoring_storage: MonitoringStorage for reading metrics
            compute_storage: Compute storage for updating instance counts
        """
        self.storage = storage
        self.monitoring_storage = monitoring_storage
        self.compute_storage = compute_storage
        self.running = False
        self.evaluation_interval = 30  # Evaluate every 30 seconds

    async def start(self):
        """Start the evaluator background task."""
        self.running = True
        logger.info("[AutoscalingEvaluator] Started evaluator")
        try:
            while self.running:
                await self._evaluate_all_policies()
                await asyncio.sleep(self.evaluation_interval)
        except Exception as e:
            logger.error(f"[AutoscalingEvaluator] Error in evaluator loop: {e}")

    async def stop(self):
        """Stop the evaluator."""
        self.running = False
        logger.info("[AutoscalingEvaluator] Stopped evaluator")

    async def _evaluate_all_policies(self):
        """Evaluate all autoscaling policies across all projects and zones."""
        try:
            # Get all policies
            all_policies_by_project = self.storage.policies
            
            for project, zones in all_policies_by_project.items():
                for zone, policies in zones.items():
                    for policy_id, policy in policies.items():
                        await self._evaluate_policy(project, zone, policy_id, policy)

        except Exception as e:
            logger.error(f"[AutoscalingEvaluator] Error evaluating policies: {e}")

    async def _evaluate_policy(self, project: str, zone: str, policy_id: str, policy) -> None:
        """Evaluate a single policy and take scaling action if needed."""
        try:
            if not policy.enabled:
                return

            # Get current metric value
            metric_value = await self._get_metric_value(project, policy)
            if metric_value is None:
                logger.debug(f"[AutoscalingEvaluator] No metric data for {policy_id}")
                # Use simulated metric if no real data
                metric_value = 50 + random.random() * 40  # 50-90%

            # Determine desired size
            desired_size = await self._get_desired_size(policy, metric_value)

            # Update status
            self.storage.update_status(
                project,
                zone,
                policy_id,
                current_replicas=policy.current_size,
                desired_replicas=desired_size,
                current_metric_value=metric_value,
                status_message="OK" if desired_size == policy.current_size else f"Scaling to {desired_size}"
            )

            # Check if scaling is needed
            if desired_size != policy.current_size:
                await self._perform_scaling(project, zone, policy_id, policy, desired_size, metric_value)

        except Exception as e:
            logger.error(f"[AutoscalingEvaluator] Error evaluating policy {policy_id}: {e}")

    async def _get_metric_value(self, project: str, policy) -> Optional[float]:
        """Get the current metric value for a policy."""
        try:
            if not self.monitoring_storage:
                return None

            # Get the primary scaling rule
            if not policy.scaling_rules:
                return None

            rule = policy.scaling_rules[0]

            # Build metric filter
            if rule.metric_type == ScalingMetricType.CPU_UTILIZATION:
                metric_type = "compute.googleapis.com/instance/cpu/utilization"
            elif rule.metric_type == ScalingMetricType.MEMORY_UTILIZATION:
                metric_type = "compute.googleapis.com/instance/memory/utilization"
            elif rule.metric_type == ScalingMetricType.CUSTOM_METRIC and rule.metric_name:
                metric_type = rule.metric_name
            else:
                return None

            # Query monitoring storage for metrics
            filter_str = f'metric.type="{metric_type}"'
            end_time = datetime.now(timezone.utc)
            start_time = end_time - timedelta(minutes=5)

            time_series = self.monitoring_storage.list_time_series(
                project,
                filter_str,
                start_time,
                end_time,
            )

            if not time_series:
                return None

            # Average the metric values from all data points
            all_values = []
            for ts in time_series:
                for point in ts.get("points", []):
                    value = point.get("value", {})
                    if "doubleValue" in value:
                        all_values.append(value["doubleValue"])
                    elif "int64Value" in value:
                        all_values.append(float(value["int64Value"]))

            if all_values:
                return sum(all_values) / len(all_values)

            return None

        except Exception as e:
            logger.debug(f"[AutoscalingEvaluator] Error getting metric: {e}")
            return None

    async def _get_desired_size(self, policy, metric_value: float) -> int:
        """Calculate desired size based on metric value."""
        if not policy.scaling_rules:
            return policy.current_size

        rule = policy.scaling_rules[0]

        # Determine scaling decision
        if metric_value >= rule.scale_up_threshold:
            # Scale up
            desired = min(policy.current_size + 1, policy.max_replicas)
        elif metric_value <= rule.scale_down_threshold:
            # Scale down
            desired = max(policy.current_size - 1, policy.min_replicas)
        else:
            # Stay at current size
            desired = policy.current_size

        # Clamp to min/max
        desired = max(policy.min_replicas, min(desired, policy.max_replicas))

        return desired

    async def _perform_scaling(
        self,
        project: str,
        zone: str,
        policy_id: str,
        policy,
        desired_size: int,
        metric_value: float,
    ) -> None:
        """Perform the actual scaling operation."""
        try:
            old_size = policy.current_size

            # Update policy
            policy.target_size = desired_size
            policy.current_size = desired_size
            policy.last_scaling_time = datetime.now(timezone.utc).isoformat()

            # Determine action
            if desired_size > old_size:
                action = "SCALE_UP"
                reason = f"Metric {metric_value:.1f}% >= threshold {policy.scaling_rules[0].scale_up_threshold:.1f}%"
                policy.last_action = "SCALED_UP"
            else:
                action = "SCALE_DOWN"
                reason = f"Metric {metric_value:.1f}% <= threshold {policy.scaling_rules[0].scale_down_threshold:.1f}%"
                policy.last_action = "SCALED_DOWN"

            # Record the action
            self.storage.record_action(
                project,
                policy.name,
                action,
                old_size,
                desired_size,
                reason,
                metric_value,
            )

            logger.info(
                f"[AutoscalingEvaluator] {action}: {policy_id} "
                f"from {old_size} to {desired_size} instances"
            )

        except Exception as e:
            logger.error(f"[AutoscalingEvaluator] Error performing scaling: {e}")
