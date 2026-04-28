"""
Cloud Monitoring storage layer.

Handles in-memory storage and retrieval of metrics, descriptors, alerts, and notifications.
"""

from typing import Dict, List, Optional, Tuple
from datetime import datetime, timedelta
import re

from .models import (
    MetricDescriptor,
    TimeSeries,
    AlertPolicy,
    NotificationChannel,
    NotificationHistory,
    Point,
)


class MonitoringStorage:
    """In-memory storage for monitoring data."""

    def __init__(self):
        """Initialize storage containers."""
        # Structure: {project_id: {metric_type: MetricDescriptor}}
        self.metric_descriptors: Dict[str, Dict[str, MetricDescriptor]] = {}

        # Structure: {project_id: [TimeSeries]}
        self.time_series: Dict[str, List[Dict]] = {}

        # Structure: {project_id: {policy_id: AlertPolicy}}
        self.alert_policies: Dict[str, Dict[str, AlertPolicy]] = {}

        # Structure: {project_id: {channel_id: NotificationChannel}}
        self.notification_channels: Dict[str, Dict[str, NotificationChannel]] = {}

        # Structure: [NotificationHistory] - all notifications sent
        self.notifications_sent: List[NotificationHistory] = []

    # ========== METRIC DESCRIPTORS ==========

    def put_metric_descriptor(self, project: str, descriptor: MetricDescriptor) -> None:
        """Store a metric descriptor."""
        if project not in self.metric_descriptors:
            self.metric_descriptors[project] = {}
        self.metric_descriptors[project][descriptor.type] = descriptor

    def get_metric_descriptor(
        self, project: str, metric_type: str
    ) -> Optional[MetricDescriptor]:
        """Retrieve a metric descriptor by type."""
        return self.metric_descriptors.get(project, {}).get(metric_type)

    def list_metric_descriptors(
        self, project: str, filter_str: Optional[str] = None
    ) -> List[MetricDescriptor]:
        """List metric descriptors with optional filter."""
        descriptors = list(self.metric_descriptors.get(project, {}).values())

        if filter_str:
            # Simple filter: metric.type=~"pattern"
            # Extract pattern from filter string
            match = re.search(r'metric\.type\s*=~\s*"([^"]*)"', filter_str)
            if match:
                pattern = match.group(1).replace("*", ".*")
                regex = re.compile(pattern)
                descriptors = [d for d in descriptors if regex.match(d.type)]

        return descriptors

    def delete_metric_descriptor(self, project: str, metric_type: str) -> None:
        """Delete a metric descriptor."""
        if project in self.metric_descriptors:
            self.metric_descriptors[project].pop(metric_type, None)

    # ========== TIME SERIES ==========

    def put_time_series(self, project: str, ts: Dict) -> None:
        """Store time series data."""
        if project not in self.time_series:
            self.time_series[project] = []
        self.time_series[project].append(ts)

    def list_time_series(
        self,
        project: str,
        filter_str: str,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None,
    ) -> List[Dict]:
        """
        Query time series with filter and optional time range.

        Filter format: 'metric.type="..." AND resource.type="..."'
        """
        all_ts = self.time_series.get(project, [])

        # Parse filter to extract metric.type and resource.type
        metric_type = self._extract_metric_type(filter_str)
        resource_type = self._extract_resource_type(filter_str)

        results = []
        for ts in all_ts:
            # Check metric type
            if metric_type and ts.get("metric", {}).get("type") != metric_type:
                continue

            # Check resource type
            if resource_type and ts.get("resource", {}).get("type") != resource_type:
                continue

            # Filter points by time range
            if start_time or end_time:
                filtered_points = self._filter_points_by_time(
                    ts.get("points", []), start_time, end_time
                )
                if filtered_points:
                    ts_copy = dict(ts)
                    ts_copy["points"] = filtered_points
                    results.append(ts_copy)
            else:
                results.append(ts)

        return results

    def _extract_metric_type(self, filter_str: str) -> Optional[str]:
        """Extract metric.type from filter string."""
        if not filter_str:
            return None
        match = re.search(r'metric\.type\s*=\s*"([^"]*)"', filter_str)
        return match.group(1) if match else None

    def _extract_resource_type(self, filter_str: str) -> Optional[str]:
        """Extract resource.type from filter string."""
        if not filter_str:
            return None
        match = re.search(r'resource\.type\s*=\s*"([^"]*)"', filter_str)
        return match.group(1) if match else None

    def _filter_points_by_time(
        self,
        points: List[Dict],
        start_time: Optional[datetime],
        end_time: Optional[datetime],
    ) -> List[Dict]:
        """Filter points to only those within time range."""
        filtered = []

        for point in points:
            try:
                interval = point.get("interval", {})
                point_end = interval.get("endTime")
                if point_end:
                    # Parse ISO 8601 timestamp
                    point_time = datetime.fromisoformat(point_end.replace("Z", "+00:00"))

                    if start_time and point_time < start_time:
                        continue
                    if end_time and point_time > end_time:
                        continue

                    filtered.append(point)
            except (ValueError, KeyError):
                # If parse fails, include the point
                filtered.append(point)

        return filtered

    # ========== ALERT POLICIES ==========

    def put_alert_policy(self, project: str, policy: AlertPolicy) -> None:
        """Store an alert policy."""
        if project not in self.alert_policies:
            self.alert_policies[project] = {}
        policy_id = policy.name.split("/")[-1]
        self.alert_policies[project][policy_id] = policy

    def get_alert_policy(self, project: str, policy_id: str) -> Optional[AlertPolicy]:
        """Retrieve an alert policy."""
        return self.alert_policies.get(project, {}).get(policy_id)

    def list_alert_policies(self, project: str) -> List[AlertPolicy]:
        """List all alert policies for a project."""
        return list(self.alert_policies.get(project, {}).values())

    def update_alert_policy(self, project: str, policy: AlertPolicy) -> None:
        """Update an existing alert policy."""
        policy_id = policy.name.split("/")[-1]
        if project in self.alert_policies:
            self.alert_policies[project][policy_id] = policy

    def delete_alert_policy(self, project: str, policy_id: str) -> None:
        """Delete an alert policy."""
        if project in self.alert_policies:
            self.alert_policies[project].pop(policy_id, None)

    # ========== NOTIFICATION CHANNELS ==========

    def put_notification_channel(
        self, project: str, channel: NotificationChannel
    ) -> None:
        """Store a notification channel."""
        if project not in self.notification_channels:
            self.notification_channels[project] = {}
        channel_id = channel.name.split("/")[-1]
        self.notification_channels[project][channel_id] = channel

    def get_notification_channel(
        self, project: str, channel_id: str
    ) -> Optional[NotificationChannel]:
        """Retrieve a notification channel."""
        return self.notification_channels.get(project, {}).get(channel_id)

    def list_notification_channels(self, project: str) -> List[NotificationChannel]:
        """List all notification channels for a project."""
        return list(self.notification_channels.get(project, {}).values())

    def delete_notification_channel(self, project: str, channel_id: str) -> None:
        """Delete a notification channel."""
        if project in self.notification_channels:
            self.notification_channels[project].pop(channel_id, None)

    # ========== NOTIFICATION HISTORY ==========

    def record_notification(self, notification: NotificationHistory) -> None:
        """Record a sent notification in history."""
        self.notifications_sent.append(notification)

    def list_notifications(
        self, project: str, policy_name_prefix: Optional[str] = None
    ) -> List[NotificationHistory]:
        """List all sent notifications, optionally filtered by policy."""
        if policy_name_prefix:
            return [
                n
                for n in self.notifications_sent
                if n.policy_name.startswith(policy_name_prefix)
            ]
        return self.notifications_sent

    # ========== UTILITY METHODS ==========

    def clear_old_time_series(self, project: str, retention_days: int = 30) -> None:
        """Remove time series older than retention period."""
        cutoff_date = datetime.utcnow() - timedelta(days=retention_days)

        if project not in self.time_series:
            return

        all_ts = self.time_series[project]
        for ts in all_ts:
            points = ts.get("points", [])
            # Remove old points
            ts["points"] = [
                p
                for p in points
                if not self._is_point_older_than(p, cutoff_date)
            ]

    def _is_point_older_than(self, point: Dict, cutoff_date: datetime) -> bool:
        """Check if a point is older than cutoff date."""
        try:
            interval = point.get("interval", {})
            end_time_str = interval.get("endTime")
            if end_time_str:
                point_time = datetime.fromisoformat(
                    end_time_str.replace("Z", "+00:00")
                )
                return point_time < cutoff_date
        except (ValueError, KeyError):
            pass
        return False

    def health_check(self) -> Dict[str, int]:
        """Return storage statistics for health checking."""
        total_descriptors = sum(len(d) for d in self.metric_descriptors.values())
        total_ts = sum(len(ts) for ts in self.time_series.values())
        total_policies = sum(len(p) for p in self.alert_policies.values())
        total_channels = sum(len(c) for c in self.notification_channels.values())
        total_points = sum(
            len(ts.get("points", []))
            for ts_list in self.time_series.values()
            for ts in ts_list
        )

        return {
            "metric_descriptors": total_descriptors,
            "time_series": total_ts,
            "time_series_points": total_points,
            "alert_policies": total_policies,
            "notification_channels": total_channels,
            "notifications_sent": len(self.notifications_sent),
        }
