"""
Cloud Monitoring API routes.

Implements GCP Cloud Monitoring REST API v3 endpoints for:
- MetricDescriptors (CRUD)
- TimeSeries (write/query)
- AlertPolicies (CRUD)
- NotificationChannels (CRUD)
"""

import uuid
from datetime import datetime, timedelta, timezone
from typing import Optional, Dict, Any, List

from fastapi import APIRouter, HTTPException, Query, Path
from fastapi.responses import JSONResponse

from .models import (
    MetricDescriptor,
    MetricKind,
    ValueType,
    TimeSeries,
    Point,
    AlertPolicy,
    Condition,
    ConditionThreshold,
    NotificationChannel,
    Aggregation,
    Aligner,
    CrossSeriesReducer,
    ComparisonType,
)
from .storage import MonitoringStorage

# Global storage instance (shared across all requests)
storage = MonitoringStorage()

router = APIRouter()


# ============================================================================
# METRIC DESCRIPTORS - CRUD Operations
# ============================================================================


@router.post("/projects/{project}/metricDescriptors")
async def create_metric_descriptor(project: str, request: Dict[str, Any]) -> Dict[str, Any]:
    """
    Create a metric descriptor.

    Defines what a metric is: its type, value type, unit, and labels.
    """
    try:
        # Parse request
        metric_type = request.get("type")
        if not metric_type:
            raise ValueError("metric type is required")

        metric_kind_str = request.get("metricKind", "GAUGE")
        value_type_str = request.get("valueType", "DOUBLE")

        # Create descriptor
        descriptor = MetricDescriptor(
            name=f"projects/{project}/metricDescriptors/{metric_type}",
            type=metric_type,
            metric_kind=MetricKind(metric_kind_str),
            value_type=ValueType(value_type_str),
            unit=request.get("unit", "1"),
            description=request.get("description", ""),
            display_name=request.get("displayName", metric_type),
            labels=[],  # TODO: Parse labels from request
            monitored_resource_types=request.get("monitoredResourceTypes", []),
        )

        # Store
        storage.put_metric_descriptor(project, descriptor)

        print(f"[Monitoring] Created metric descriptor: {metric_type}")
        return descriptor.to_dict()

    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/projects/{project}/metricDescriptors")
async def list_metric_descriptors(
    project: str,
    filter: Optional[str] = Query(None),
    page_size: int = Query(100),
) -> Dict[str, Any]:
    """List metric descriptors with optional filtering."""
    try:
        descriptors = storage.list_metric_descriptors(project, filter)

        return {
            "metricDescriptors": [d.to_dict() for d in descriptors],
            "nextPageToken": None,
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/projects/{project}/metricDescriptors/{metric_type:path}")
async def get_metric_descriptor(project: str, metric_type: str) -> Dict[str, Any]:
    """Get a specific metric descriptor by type."""
    try:
        descriptor = storage.get_metric_descriptor(project, metric_type)
        if not descriptor:
            raise HTTPException(status_code=404, detail="Metric descriptor not found")
        return descriptor.to_dict()
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/projects/{project}/metricDescriptors/{metric_type:path}")
async def delete_metric_descriptor(project: str, metric_type: str) -> Dict[str, Any]:
    """Delete a metric descriptor."""
    try:
        storage.delete_metric_descriptor(project, metric_type)
        return {}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================================
# TIME SERIES - Write and Query Metrics
# ============================================================================


@router.post("/projects/{project}/timeSeries")
async def write_time_series(project: str, request: Dict[str, Any]) -> Dict[str, Any]:
    """
    Write time series data (ingest metrics).

    Receives metric data points and stores them.
    """
    try:
        time_series_list = request.get("timeSeries", [])

        if not time_series_list:
            return {}

        for ts_data in time_series_list:
            # Validate metric descriptor exists
            metric_type = ts_data.get("metric", {}).get("type")
            if metric_type:
                descriptor = storage.get_metric_descriptor(project, metric_type)
                if not descriptor:
                    # Auto-create descriptor for custom metrics
                    if metric_type.startswith("custom.googleapis.com/"):
                        auto_descriptor = MetricDescriptor(
                            name=f"projects/{project}/metricDescriptors/{metric_type}",
                            type=metric_type,
                            metric_kind=MetricKind.GAUGE,
                            value_type=ValueType.DOUBLE,
                            unit="1",
                            description="Auto-created custom metric",
                            display_name=metric_type,
                        )
                        storage.put_metric_descriptor(project, auto_descriptor)

            # Convert to dict format for storage
            ts_dict = {
                "metric": ts_data.get("metric", {}),
                "resource": ts_data.get("resource", {}),
                "metricKind": ts_data.get("metricKind"),
                "valueType": ts_data.get("valueType"),
                "points": ts_data.get("points", []),
                "metadata": ts_data.get("metadata"),
            }

            storage.put_time_series(project, ts_dict)

        print(f"[Monitoring] Wrote {len(time_series_list)} time series for project {project}")
        return {}

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/projects/{project}/timeSeries")
async def list_time_series(
    project: str,
    filter: Optional[str] = Query(None),
    interval_start_time: Optional[str] = Query(None),
    interval_end_time: Optional[str] = Query(None),
    aggregate_by: Optional[List[str]] = Query(None),
    view: str = Query("FULL"),
) -> Dict[str, Any]:
    """
    Query time series with filter and optional aggregation.

    Filter format: 'metric.type="..." AND resource.type="..."'
    """
    try:
        # Parse time range
        start_time = None
        end_time = None

        if interval_start_time:
            start_time = datetime.fromisoformat(interval_start_time.replace("Z", "+00:00"))
        if interval_end_time:
            end_time = datetime.fromisoformat(interval_end_time.replace("Z", "+00:00"))

        # Default to last 1 hour if not specified
        if not end_time:
            end_time = datetime.now(timezone.utc)
        if not start_time:
            start_time = end_time - timedelta(hours=1)

        # Retrieve matching time series
        # If no filter provided, return all time series
        filter_to_use = filter if filter else ""
        time_series_list = storage.list_time_series(
            project=project,
            filter_str=filter_to_use,
            start_time=start_time,
            end_time=end_time,
        )

        # TODO: Handle optional aggregation (cross-series reduction)
        if aggregate_by:
            print(f"[Monitoring] Aggregation requested but not yet implemented: {aggregate_by}")

        return {
            "timeSeries": [ts for ts in time_series_list],
            "nextPageToken": None,
        }

    except ValueError as e:
        raise HTTPException(status_code=400, detail=f"Invalid time format: {str(e)}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/projects/{project}/timeSeries:query")
async def query_time_series_mql(project: str, request: Dict[str, Any]) -> Dict[str, Any]:
    """
    Query time series using MQL (Monitoring Query Language).

    MQL is a text-based query language for advanced querying.
    This is a simplified implementation.
    """
    try:
        mql_query = request.get("query", "")
        print(f"[Monitoring] MQL query (not fully implemented): {mql_query}")

        # TODO: Implement full MQL parsing and execution
        # For now, return empty results
        return {
            "timeSeriesData": [],
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================================
# ALERT POLICIES - CRUD Operations
# ============================================================================


@router.post("/projects/{project}/alertPolicies")
async def create_alert_policy(project: str, request: Dict[str, Any]) -> Dict[str, Any]:
    """
    Create an alert policy.

    Defines conditions that trigger alerts and notification channels.
    """
    try:
        # Parse conditions
        conditions = []
        for cond_data in request.get("conditions", []):
            threshold_data = cond_data.get("conditionThreshold", {})

            # Parse aggregations
            aggs = []
            for agg_data in threshold_data.get("aggregations", []):
                agg = Aggregation(
                    alignment_period=agg_data.get("alignmentPeriod", "60s"),
                    per_series_aligner=Aligner(
                        agg_data.get("perSeriesAligner", "ALIGN_MEAN")
                    ),
                    cross_series_reducer=CrossSeriesReducer(
                        agg_data.get("crossSeriesReducer", "REDUCE_NONE")
                    )
                    if agg_data.get("crossSeriesReducer")
                    else None,
                    group_by_fields=agg_data.get("groupByFields"),
                )
                aggs.append(agg)

            # Create condition
            threshold = ConditionThreshold(
                filter=threshold_data.get("filter", ""),
                comparison=ComparisonType(
                    threshold_data.get("comparison", "COMPARISON_GT")
                ),
                threshold_value=float(threshold_data.get("thresholdValue", 0)),
                duration=threshold_data.get("duration", "300s"),
                aggregations=aggs,
            )

            condition = Condition(
                display_name=cond_data.get("displayName", ""),
                condition_threshold=threshold,
            )
            conditions.append(condition)

        # Create policy
        policy = AlertPolicy(
            name=f"projects/{project}/alertPolicies/{uuid.uuid4().hex[:12]}",
            display_name=request.get("displayName", ""),
            conditions=conditions,
            notification_channels=request.get("notificationChannels", []),
            enabled=request.get("enabled", True),
            documentation=request.get("documentation"),
        )

        # Store
        storage.put_alert_policy(project, policy)

        print(f"[Monitoring] Created alert policy: {policy.display_name}")
        return policy.to_dict()

    except (ValueError, KeyError) as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/projects/{project}/alertPolicies")
async def list_alert_policies(project: str, page_size: int = Query(100)) -> Dict[str, Any]:
    """List alert policies for a project."""
    try:
        policies = storage.list_alert_policies(project)
        return {
            "alertPolicies": [p.to_dict() for p in policies],
            "nextPageToken": None,
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/projects/{project}/alertPolicies/{policy_id}")
async def get_alert_policy(project: str, policy_id: str) -> Dict[str, Any]:
    """Get a specific alert policy."""
    try:
        policy = storage.get_alert_policy(project, policy_id)
        if not policy:
            raise HTTPException(status_code=404, detail="Alert policy not found")
        return policy.to_dict()
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.patch("/projects/{project}/alertPolicies/{policy_id}")
async def update_alert_policy(
    project: str, policy_id: str, request: Dict[str, Any]
) -> Dict[str, Any]:
    """Update an alert policy."""
    try:
        policy = storage.get_alert_policy(project, policy_id)
        if not policy:
            raise HTTPException(status_code=404, detail="Alert policy not found")

        # Update fields
        if "displayName" in request:
            policy.display_name = request["displayName"]
        if "enabled" in request:
            policy.enabled = request["enabled"]
        if "conditions" in request:
            # Parse new conditions
            conditions = []
            for cond_data in request.get("conditions", []):
                threshold_data = cond_data.get("conditionThreshold", {})
                threshold = ConditionThreshold(
                    filter=threshold_data.get("filter", ""),
                    comparison=ComparisonType(
                        threshold_data.get("comparison", "COMPARISON_GT")
                    ),
                    threshold_value=float(threshold_data.get("thresholdValue", 0)),
                    duration=threshold_data.get("duration", "300s"),
                )
                condition = Condition(
                    display_name=cond_data.get("displayName", ""),
                    condition_threshold=threshold,
                )
                conditions.append(condition)
            policy.conditions = conditions

        if "notificationChannels" in request:
            policy.notification_channels = request["notificationChannels"]

        policy.updated_at = datetime.now(timezone.utc)
        storage.update_alert_policy(project, policy)

        print(f"[Monitoring] Updated alert policy: {policy.display_name}")
        return policy.to_dict()

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/projects/{project}/alertPolicies/{policy_id}")
async def delete_alert_policy(project: str, policy_id: str) -> Dict[str, Any]:
    """Delete an alert policy."""
    try:
        storage.delete_alert_policy(project, policy_id)
        return {}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================================
# NOTIFICATION CHANNELS - CRUD Operations
# ============================================================================


@router.post("/projects/{project}/notificationChannels")
async def create_notification_channel(
    project: str, request: Dict[str, Any]
) -> Dict[str, Any]:
    """Create a notification channel (email, webhook, slack, etc.)."""
    try:
        channel = NotificationChannel(
            name=f"projects/{project}/notificationChannels/{uuid.uuid4().hex[:12]}",
            display_name=request.get("displayName", ""),
            type=request.get("type", "email"),
            labels=request.get("labels", {}),
            enabled=request.get("enabled", True),
        )

        storage.put_notification_channel(project, channel)

        print(f"[Monitoring] Created notification channel: {channel.type}")
        return channel.to_dict()

    except (ValueError, KeyError) as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/projects/{project}/notificationChannels")
async def list_notification_channels(project: str) -> Dict[str, Any]:
    """List notification channels for a project."""
    try:
        channels = storage.list_notification_channels(project)
        return {
            "notificationChannels": [c.to_dict() for c in channels],
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/projects/{project}/notificationChannels/{channel_id}")
async def delete_notification_channel(project: str, channel_id: str) -> Dict[str, Any]:
    """Delete a notification channel."""
    try:
        storage.delete_notification_channel(project, channel_id)
        return {}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================================
# MONITORING SERVICE ENDPOINTS
# ============================================================================


@router.get("/projects/{project}/notificationHistory")
async def get_notification_history(project: str) -> Dict[str, Any]:
    """
    Get history of all notifications sent (simulator feature).

    Useful for testing and verifying alerts fired.
    """
    try:
        policy_prefix = f"projects/{project}/"
        notifications = storage.list_notifications(project, policy_prefix)

        return {
            "notifications": [n.to_dict() for n in notifications],
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/monitoring/health")
async def health_check() -> Dict[str, Any]:
    """Health check endpoint with storage statistics."""
    try:
        stats = storage.health_check()
        return {
            "status": "healthy",
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "storage": stats,
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
