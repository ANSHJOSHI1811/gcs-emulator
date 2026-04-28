"""
Compute Engine Auto-Scaling API endpoints.

Implements autoscaling.googleapis.com API for autoscaling policy management.
"""

from fastapi import APIRouter, HTTPException, Query
from typing import Dict, List, Any, Optional
from datetime import datetime, timezone
import logging

from .models import ScalingMetricType
from .storage import AutoscalingStorage

logger = logging.getLogger(__name__)

# Shared storage instance
storage = AutoscalingStorage()

router = APIRouter()


# ============================================================================
# AUTOSCALING POLICIES
# ============================================================================

@router.post("/projects/{project}/zones/{zone}/autoscalers")
async def create_autoscaler(
    project: str,
    zone: str,
    request: Dict[str, Any],
) -> Dict[str, Any]:
    """Create a new autoscaling policy."""
    try:
        # Extract policy ID from name
        policy_name = request.get("name", "")
        policy_id = policy_name.split("/")[-1] if policy_name else f"autoscaler-{project}-{zone}"

        target = request.get("target", "")
        if not target:
            raise ValueError("target required")

        description = request.get("description")
        min_replicas = request.get("minReplicas", 1)
        max_replicas = request.get("maxReplicas", 10)
        scaling_rules = request.get("scalingRules", [])

        policy = storage.create_policy(
            project,
            zone,
            policy_id,
            target,
            min_replicas=min_replicas,
            max_replicas=max_replicas,
            description=description,
            scaling_rules=scaling_rules,
        )

        logger.info(f"[Autoscaling] Created policy {policy_id} in {zone}")
        return policy.to_dict()

    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/projects/{project}/zones/{zone}/autoscalers/{autoscaler}")
async def get_autoscaler(project: str, zone: str, autoscaler: str) -> Dict[str, Any]:
    """Get an autoscaling policy."""
    try:
        policy = storage.get_policy(project, zone, autoscaler)
        if not policy:
            raise HTTPException(status_code=404, detail="Autoscaler not found")
        return policy.to_dict()

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/projects/{project}/zones/{zone}/autoscalers")
async def list_autoscalers(project: str, zone: str) -> Dict[str, List[Dict[str, Any]]]:
    """List autoscaling policies in a zone."""
    try:
        policies = storage.list_policies(project, zone)
        return {
            "items": [p.to_dict() for p in policies],
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.patch("/projects/{project}/zones/{zone}/autoscalers/{autoscaler}")
async def update_autoscaler(
    project: str,
    zone: str,
    autoscaler: str,
    request: Dict[str, Any],
) -> Dict[str, Any]:
    """Update an autoscaling policy."""
    try:
        if not storage.policy_exists(project, zone, autoscaler):
            raise HTTPException(status_code=404, detail="Autoscaler not found")

        min_replicas = request.get("minReplicas")
        max_replicas = request.get("maxReplicas")
        scaling_rules = request.get("scalingRules")
        enabled = request.get("enabled")

        policy = storage.update_policy(
            project,
            zone,
            autoscaler,
            min_replicas=min_replicas,
            max_replicas=max_replicas,
            scaling_rules=scaling_rules,
            enabled=enabled,
        )

        logger.info(f"[Autoscaling] Updated policy {autoscaler}")
        return policy.to_dict()

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.delete("/projects/{project}/zones/{zone}/autoscalers/{autoscaler}")
async def delete_autoscaler(project: str, zone: str, autoscaler: str) -> Dict[str, Any]:
    """Delete an autoscaling policy."""
    try:
        if not storage.policy_exists(project, zone, autoscaler):
            raise HTTPException(status_code=404, detail="Autoscaler not found")

        storage.delete_policy(project, zone, autoscaler)
        logger.info(f"[Autoscaling] Deleted policy {autoscaler}")
        return {}

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================================
# AUTOSCALER STATUS
# ============================================================================

@router.get("/projects/{project}/zones/{zone}/autoscalers/{autoscaler}/status")
async def get_autoscaler_status(project: str, zone: str, autoscaler: str) -> Dict[str, Any]:
    """Get autoscaler status with current scaling information."""
    try:
        status = storage.get_status(project, zone, autoscaler)
        if not status:
            raise HTTPException(status_code=404, detail="No status found")
        return status.to_dict()

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/projects/{project}/zones/{zone}/autoscalers/status")
async def list_autoscaler_statuses(project: str, zone: str) -> Dict[str, List[Dict[str, Any]]]:
    """List autoscaler statuses for all policies in a zone."""
    try:
        statuses = storage.get_all_statuses(project, zone)
        return {
            "items": [s.to_dict() for s in statuses],
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================================
# SCALING ACTIONS HISTORY
# ============================================================================

@router.get("/projects/{project}/zones/{zone}/autoscalers/{autoscaler}/actions")
async def get_scaling_actions(
    project: str,
    zone: str,
    autoscaler: str,
    limit: int = Query(100),
) -> Dict[str, List[Dict[str, Any]]]:
    """Get scaling action history for a policy."""
    try:
        policy = storage.get_policy(project, zone, autoscaler)
        if not policy:
            raise HTTPException(status_code=404, detail="Autoscaler not found")

        actions = storage.get_scaling_actions(project, policy.name, limit)
        return {
            "items": [a.to_dict() for a in actions],
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================================
# HEALTH CHECK
# ============================================================================

@router.get("/autoscaling/health")
async def health() -> Dict[str, Any]:
    """Health check with storage statistics."""
    try:
        stats = storage.health_check()
        return {
            "status": "healthy",
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "storage": stats,
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
