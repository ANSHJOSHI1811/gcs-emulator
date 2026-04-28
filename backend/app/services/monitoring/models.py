"""
Cloud Monitoring data models.

Defines MetricDescriptor, TimeSeries, AlertPolicy, and related classes
for GCP Monitoring service simulator.
"""

from dataclasses import dataclass, field, asdict
from datetime import datetime, timezone
from enum import Enum
from typing import Optional, List, Dict, Any
import uuid


class MetricKind(str, Enum):
    """Type of metric (GAUGE, DELTA, CUMULATIVE)."""
    GAUGE = "GAUGE"                    # Instantaneous value
    DELTA = "DELTA"                    # Accumulated change
    CUMULATIVE = "CUMULATIVE"          # Monotonically increasing


class ValueType(str, Enum):
    """Data type of metric values."""
    DOUBLE = "DOUBLE"
    INT64 = "INT64"
    BOOL = "BOOL"
    STRING = "STRING"
    DISTRIBUTION = "DISTRIBUTION"


class Aligner(str, Enum):
    """Alignment functions for time series aggregation."""
    ALIGN_NONE = "ALIGN_NONE"
    ALIGN_DELTA = "ALIGN_DELTA"
    ALIGN_RATE = "ALIGN_RATE"
    ALIGN_MEAN = "ALIGN_MEAN"
    ALIGN_SUM = "ALIGN_SUM"
    ALIGN_MIN = "ALIGN_MIN"
    ALIGN_MAX = "ALIGN_MAX"
    ALIGN_COUNT = "ALIGN_COUNT"
    ALIGN_COUNT_TRUE = "ALIGN_COUNT_TRUE"
    ALIGN_PERCENT_CHANGE = "ALIGN_PERCENT_CHANGE"


class CrossSeriesReducer(str, Enum):
    """Reduce function to combine multiple time series."""
    REDUCE_NONE = "REDUCE_NONE"
    REDUCE_SUM = "REDUCE_SUM"
    REDUCE_MEAN = "REDUCE_MEAN"
    REDUCE_MIN = "REDUCE_MIN"
    REDUCE_MAX = "REDUCE_MAX"
    REDUCE_COUNT = "REDUCE_COUNT"
    REDUCE_COUNT_TRUE = "REDUCE_COUNT_TRUE"
    REDUCE_PERCENT_CHANGE = "REDUCE_PERCENT_CHANGE"


class ComparisonType(str, Enum):
    """Threshold comparison operators."""
    COMPARISON_GT = "COMPARISON_GT"    # >
    COMPARISON_GE = "COMPARISON_GE"    # >=
    COMPARISON_LT = "COMPARISON_LT"    # <
    COMPARISON_LE = "COMPARISON_LE"    # <=
    COMPARISON_EQ = "COMPARISON_EQ"    # ==
    COMPARISON_NE = "COMPARISON_NE"    # !=


class AlertState(str, Enum):
    """Alert policy state."""
    OK = "OK"
    ALARM = "ALARM"
    INSUFFICIENT_DATA = "INSUFFICIENT_DATA"


@dataclass
class LabelDescriptor:
    """Defines a label in metric descriptor."""
    key: str
    value_type: str                    # STRING, INT64, BOOL
    description: Optional[str] = None


@dataclass
class MetricDescriptor:
    """Defines metric structure, labels, and properties."""
    name: str                          # projects/{project}/metricDescriptors/{type}
    type: str                          # custom.googleapis.com/cpu
    metric_kind: MetricKind
    value_type: ValueType
    unit: str                          # %, s, By, etc.
    description: str
    display_name: str
    labels: List[LabelDescriptor] = field(default_factory=list)
    monitored_resource_types: List[str] = field(default_factory=list)
    created_at: datetime = field(default_factory=datetime.utcnow)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to JSON-serializable dict."""
        return {
            "name": self.name,
            "type": self.type,
            "metricKind": self.metric_kind.value,
            "valueType": self.value_type.value,
            "unit": self.unit,
            "description": self.description,
            "displayName": self.display_name,
            "labels": [asdict(l) for l in self.labels],
            "monitoredResourceTypes": self.monitored_resource_types,
            "createdAt": self.created_at.isoformat(),
        }


@dataclass
class Point:
    """Single time series data point."""
    interval: Dict[str, str]           # {"startTime": "ISO8601", "endTime": "ISO8601"}
    value: Dict[str, Any]              # {"doubleValue": 75.5} or {"int64Value": 100}

    def to_dict(self) -> Dict[str, Any]:
        """Convert to JSON-serializable dict."""
        return {
            "interval": self.interval,
            "value": self.value,
        }


@dataclass
class TimeSeries:
    """Complete time series for a metric."""
    metric: Dict[str, Any]             # {"type": "...", "labels": {...}}
    resource: Dict[str, Any]           # {"type": "gce_instance", "labels": {...}}
    metric_kind: Optional[MetricKind] = None
    value_type: Optional[ValueType] = None
    points: List[Point] = field(default_factory=list)
    metadata: Optional[Dict] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert to JSON-serializable dict."""
        return {
            "metric": self.metric,
            "resource": self.resource,
            "metricKind": self.metric_kind.value if self.metric_kind else None,
            "valueType": self.value_type.value if self.value_type else None,
            "points": [p.to_dict() for p in self.points],
            "metadata": self.metadata,
        }


@dataclass
class Aggregation:
    """How to aggregate/align time series."""
    alignment_period: str              # "60s", "300s", "3600s"
    per_series_aligner: Aligner
    cross_series_reducer: Optional[CrossSeriesReducer] = None
    group_by_fields: Optional[List[str]] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert to JSON-serializable dict."""
        return {
            "alignmentPeriod": self.alignment_period,
            "perSeriesAligner": self.per_series_aligner.value,
            "crossSeriesReducer": self.cross_series_reducer.value if self.cross_series_reducer else None,
            "groupByFields": self.group_by_fields,
        }


@dataclass
class ConditionThreshold:
    """Threshold-based alert condition."""
    filter: str                        # metric.type="..."
    comparison: ComparisonType
    threshold_value: float
    duration: str                      # "300s", "600s"
    aggregations: List[Aggregation] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to JSON-serializable dict."""
        return {
            "filter": self.filter,
            "comparison": self.comparison.value,
            "thresholdValue": self.threshold_value,
            "duration": self.duration,
            "aggregations": [a.to_dict() for a in self.aggregations],
        }


@dataclass
class Condition:
    """Alert policy condition."""
    display_name: str
    condition_threshold: ConditionThreshold

    def to_dict(self) -> Dict[str, Any]:
        """Convert to JSON-serializable dict."""
        return {
            "displayName": self.display_name,
            "conditionThreshold": self.condition_threshold.to_dict(),
        }


@dataclass
class NotificationChannel:
    """Where to send alert notifications."""
    name: str                          # projects/{project}/notificationChannels/{id}
    display_name: str
    type: str                          # email, slack, webhook, pagerduty, sms
    labels: Dict[str, str]             # {"emailAddress": "..."}, {"url": "..."}
    enabled: bool = True
    created_at: datetime = field(default_factory=datetime.utcnow)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to JSON-serializable dict."""
        return {
            "name": self.name,
            "displayName": self.display_name,
            "type": self.type,
            "labels": self.labels,
            "enabled": self.enabled,
            "createdAt": self.created_at.isoformat(),
        }


@dataclass
class AlertPolicy:
    """Alert policy with conditions and notification channels."""
    name: str                          # projects/{project}/alertPolicies/{id}
    display_name: str
    conditions: List[Condition]
    notification_channels: List[str]   # Channel names/ARNs
    enabled: bool = True
    documentation: Optional[Dict] = None
    state: AlertState = AlertState.OK
    state_updated_at: datetime = field(default_factory=datetime.utcnow)
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to JSON-serializable dict."""
        return {
            "name": self.name,
            "displayName": self.display_name,
            "conditions": [c.to_dict() for c in self.conditions],
            "notificationChannels": self.notification_channels,
            "enabled": self.enabled,
            "documentation": self.documentation,
            "state": self.state.value,
            "stateUpdatedAt": self.state_updated_at.isoformat(),
            "createdAt": self.created_at.isoformat(),
            "updatedAt": self.updated_at.isoformat(),
        }


@dataclass
class NotificationHistory:
    """Record of notifications sent."""
    id: str
    policy_name: str
    channel_name: str
    state: str                         # FIRING, RESOLVED
    message: str
    sent_at: datetime = field(default_factory=datetime.utcnow)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to JSON-serializable dict."""
        return {
            "id": self.id,
            "policyName": self.policy_name,
            "channelName": self.channel_name,
            "state": self.state,
            "message": self.message,
            "sentAt": self.sent_at.isoformat(),
        }
