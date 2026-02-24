"""
Cloud Monitoring alert evaluation engine.

Background task that periodically evaluates alert policies and sends notifications.
"""

import asyncio
import uuid
from datetime import datetime, timedelta
from typing import Dict, List, Optional

from .models import (
    AlertPolicy,
    AlertState,
    NotificationHistory,
    ComparisonType,
)
from .storage import MonitoringStorage


class AlertPolicyEvaluator:
    """Background task that evaluates alert policies periodically."""

    def __init__(self, storage: MonitoringStorage):
        """Initialize evaluator with storage reference."""
        self.storage = storage
        self.active_tasks = {}  # {project_id: asyncio.Task}
        self.policy_states = {}  # {policy_name: (state, last_update_time)}

    async def start(self) -> None:
        """Start the evaluation loop."""
        print("[AlertEvaluator] Starting evaluation loop...")
        while True:
            try:
                await self._evaluate_all_policies()
            except Exception as e:
                print(f"[AlertEvaluator] Error during evaluation: {e}")

            # Evaluate every 60 seconds
            await asyncio.sleep(60)

    async def _evaluate_all_policies(self) -> None:
        """Evaluate all alert policies across all projects."""
        for project in list(self.storage.alert_policies.keys()):
            for policy in self.storage.list_alert_policies(project):
                await self._evaluate_policy(project, policy)

    async def _evaluate_policy(self, project: str, policy: AlertPolicy) -> None:
        """Evaluate whether an alert policy should transition states."""
        if not policy.enabled:
            return

        try:
            # Evaluate all conditions (AND logic)
            all_conditions_met = True
            for condition in policy.conditions:
                is_breaching = await self._evaluate_condition(project, condition)
                if not is_breaching:
                    all_conditions_met = False
                    break

            # Determine new state
            new_state = AlertState.ALARM if all_conditions_met else AlertState.OK

            # Check if state changed
            if new_state != policy.state:
                old_state = policy.state
                policy.state = new_state
                policy.state_updated_at = datetime.utcnow()
                self.storage.update_alert_policy(project, policy)

                print(
                    f"[AlertEvaluator] Policy '{policy.display_name}' "
                    f"transitioned: {old_state.value} → {new_state.value}"
                )

                # Send notifications on state change
                self._send_notifications(project, policy, new_state.value)

        except Exception as e:
            print(f"[AlertEvaluator] Error evaluating policy {policy.name}: {e}")

    async def _evaluate_condition(self, project: str, condition) -> bool:
        """Evaluate whether a single condition is breaching."""
        try:
            threshold_config = condition.condition_threshold

            filter_str = threshold_config.filter
            comparison = threshold_config.comparison
            threshold_value = threshold_config.threshold_value
            duration_str = threshold_config.duration  # e.g., "300s"
            aggregations = threshold_config.aggregations

            # Parse duration (e.g., "300s" → 300 seconds)
            duration_seconds = int(duration_str.rstrip("s"))

            # Get time series matching filter
            start_time = datetime.utcnow() - timedelta(seconds=duration_seconds)
            end_time = datetime.utcnow()

            time_series_list = self.storage.list_time_series(
                project=project,
                filter_str=filter_str,
                start_time=start_time,
                end_time=end_time,
            )

            if not time_series_list:
                # No data = condition not breaching
                return False

            # Apply aggregations and collect values
            aligned_values = []

            for ts in time_series_list:
                points = ts.get("points", [])
                if not points:
                    continue

                # Apply alignment (grouping by alignment period)
                if aggregations:
                    for agg in aggregations:
                        alignment_seconds = int(agg.alignment_period.rstrip("s"))
                        aligner = agg.per_series_aligner

                        aligned = self._align_time_series(points, alignment_seconds, aligner)
                        aligned_values.extend(aligned)
                else:
                    # No aggregation, use raw values
                    for point in points:
                        try:
                            value = self._extract_value(point.get("value", {}))
                            if value is not None:
                                aligned_values.append(value)
                        except (ValueError, KeyError):
                            pass

            if not aligned_values:
                return False

            # Compare all values to threshold
            breaching_count = 0
            for value in aligned_values:
                if self._compare_value(value, threshold_value, comparison):
                    breaching_count += 1

            # Determine if ALL values breach (entire duration must breach)
            total_expected = len(aligned_values)
            is_breaching = breaching_count == total_expected

            return is_breaching

        except Exception as e:
            print(f"[AlertEvaluator] Error evaluating condition: {e}")
            return False

    def _align_time_series(self, points: List[Dict], alignment_seconds: int, aligner: str) -> List[float]:
        """
        Align time series points to alignment periods.

        Groups points by alignment period and applies aligner function.
        """
        if not points:
            return []

        # Group points into buckets by time
        buckets = {}

        for point in points:
            try:
                interval = point.get("interval", {})
                end_time_str = interval.get("endTime")

                if end_time_str:
                    # Parse ISO 8601 timestamp
                    end_time = datetime.fromisoformat(end_time_str.replace("Z", "+00:00"))
                    bucket_idx = int(end_time.timestamp() // alignment_seconds)

                    if bucket_idx not in buckets:
                        buckets[bucket_idx] = []

                    value = self._extract_value(point.get("value", {}))
                    if value is not None:
                        buckets[bucket_idx].append(value)
            except (ValueError, KeyError, AttributeError):
                pass

        # Apply aligner to each bucket
        return self._apply_aligner(buckets, aligner)

    def _apply_aligner(self, buckets: Dict[int, List[float]], aligner: str) -> List[float]:
        """Apply alignment function to bucketed values."""
        aligned = []

        for bucket_values in buckets.values():
            if not bucket_values:
                continue

            if aligner == "ALIGN_MEAN":
                aligned.append(sum(bucket_values) / len(bucket_values))
            elif aligner == "ALIGN_SUM":
                aligned.append(sum(bucket_values))
            elif aligner == "ALIGN_MAX":
                aligned.append(max(bucket_values))
            elif aligner == "ALIGN_MIN":
                aligned.append(min(bucket_values))
            elif aligner == "ALIGN_COUNT":
                aligned.append(float(len(bucket_values)))
            elif aligner == "ALIGN_COUNT_TRUE":
                # Count how many are non-zero/true
                true_count = sum(1 for v in bucket_values if v)
                aligned.append(float(true_count))
            elif aligner == "ALIGN_DELTA":
                # Change over period
                if len(bucket_values) >= 2:
                    delta = bucket_values[-1] - bucket_values[0]
                    aligned.append(delta)
            elif aligner == "ALIGN_RATE":
                # Change per second
                if len(bucket_values) >= 2 and bucket_values:
                    delta = bucket_values[-1] - bucket_values[0]
                    rate = delta / len(bucket_values)
                    aligned.append(rate)
            else:
                # Default: use first value
                aligned.append(bucket_values[0])

        return aligned

    def _extract_value(self, value_dict: Dict) -> Optional[float]:
        """Extract numeric value from value dict."""
        if "doubleValue" in value_dict:
            return float(value_dict["doubleValue"])
        elif "int64Value" in value_dict:
            return float(value_dict["int64Value"])
        elif "boolValue" in value_dict:
            return 1.0 if value_dict["boolValue"] else 0.0
        return None

    def _compare_value(self, value: float, threshold: float, comparison: ComparisonType) -> bool:
        """Compare value to threshold using comparison operator."""
        if comparison == ComparisonType.COMPARISON_GT:
            return value > threshold
        elif comparison == ComparisonType.COMPARISON_GE:
            return value >= threshold
        elif comparison == ComparisonType.COMPARISON_LT:
            return value < threshold
        elif comparison == ComparisonType.COMPARISON_LE:
            return value <= threshold
        elif comparison == ComparisonType.COMPARISON_EQ:
            return value == threshold
        elif comparison == ComparisonType.COMPARISON_NE:
            return value != threshold
        return False

    def _send_notifications(self, project: str, policy: AlertPolicy, state: str) -> None:
        """Send notifications to all enabled channels."""
        for channel_name in policy.notification_channels:
            try:
                # Extract channel ID from full name
                channel_id = channel_name.split("/")[-1]
                channel = self.storage.get_notification_channel(project, channel_id)

                if not channel or not channel.enabled:
                    continue

                # Create notification record
                message = f"Alert: {policy.display_name} is now {state}"

                notification = NotificationHistory(
                    id=uuid.uuid4().hex[:12],
                    policy_name=policy.name,
                    channel_name=channel_name,
                    state=state,
                    message=message,
                )

                # Store notification in history
                self.storage.record_notification(notification)

                # Log notification (simulates sending)
                self._log_notification(channel, message, state)

            except Exception as e:
                print(f"[AlertEvaluator] Error sending notification: {e}")

    def _log_notification(self, channel, message: str, state: str) -> None:
        """Log notification (simulates sending to actual channel)."""
        if channel.type == "email":
            email = channel.labels.get("emailAddress", "unknown")
            print(f"[NOTIFICATION] Email → {email}")
            print(f"  Subject: {message}")
            print(f"  State: {state}")

        elif channel.type == "webhook":
            url = channel.labels.get("url", "unknown")
            print(f"[NOTIFICATION] Webhook → {url}")
            print(f"  Payload: {{message: '{message}', state: '{state}'}}")

        elif channel.type == "slack":
            channel_id = channel.labels.get("channel", "unknown")
            print(f"[NOTIFICATION] Slack → #{channel_id}")
            print(f"  Message: {message}")

        elif channel.type == "pagerduty":
            service_key = channel.labels.get("serviceKey", "unknown")
            print(f"[NOTIFICATION] PagerDuty → {service_key}")
            print(f"  Incident: {message}")

        elif channel.type == "sms":
            number = channel.labels.get("number", "unknown")
            print(f"[NOTIFICATION] SMS → {number}")
            print(f"  Message: {message}")

        else:
            print(f"[NOTIFICATION] Unknown channel type: {channel.type}")
            print(f"  Message: {message}")
