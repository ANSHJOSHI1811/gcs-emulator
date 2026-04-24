"""
Compute Engine Auto-Scaling service module.

Provides autoscaling policy management and evaluation functionality.
"""

from .router import router, storage
from .evaluator import AutoscalingEvaluator
from .models import (
    AutoscalingPolicy,
    ScalingRule,
    ScalingAction,
    AutoscalerStatus,
    ScalingMetricType,
)

__all__ = [
    "router",
    "storage",
    "AutoscalingEvaluator",
    "AutoscalingPolicy",
    "ScalingRule",
    "ScalingAction",
    "AutoscalerStatus",
    "ScalingMetricType",
]
