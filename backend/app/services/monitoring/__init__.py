"""
Cloud Monitoring service for GCP Stimulator.

Implements GCP Cloud Monitoring REST API v3 with:
- Metric Descriptors (metric definitions)
- Time Series (metric data)
- Alert Policies (alert rules)
- Notification Channels (alert destinations)
- Alert Evaluator (background task)
"""

from .router import router, storage
from .alert_evaluator import AlertPolicyEvaluator
from .models import (
    MetricDescriptor,
    TimeSeries,
    Point,
    AlertPolicy,
    NotificationChannel,
    Condition,
    MetricKind,
    ValueType,
    Aligner,
    CrossSeriesReducer,
    ComparisonType,
    AlertState,
)

__all__ = [
    "router",
    "storage",
    "AlertPolicyEvaluator",
    # Models
    "MetricDescriptor",
    "TimeSeries",
    "Point",
    "AlertPolicy",
    "NotificationChannel",
    "Condition",
    # Enums
    "MetricKind",
    "ValueType",
    "Aligner",
    "CrossSeriesReducer",
    "ComparisonType",
    "AlertState",
]
