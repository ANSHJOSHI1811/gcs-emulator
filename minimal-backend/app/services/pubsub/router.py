"""
Cloud Pub/Sub REST API endpoints.

Implements pubsub.googleapis.com API v1 for topic and subscription management.
"""

from fastapi import APIRouter, HTTPException, Query
from typing import Dict, List, Any, Optional
import base64
from datetime import datetime, timezone
import logging

from .models import DeliveryType
from .storage import PubSubStorage

logger = logging.getLogger(__name__)

# Shared storage instance
storage = PubSubStorage()

router = APIRouter()


# ============================================================================
# TOPICS
# ============================================================================

@router.post("/projects/{project}/topics")
async def create_topic(
    project: str,
    request: Dict[str, Any],
) -> Dict[str, Any]:
    """Create a new topic."""
    try:
        topic_id = request.get("name", "").split("/")[-1]
        if not topic_id:
            raise ValueError("Topic name required")

        labels = request.get("labels", {})

        topic = storage.create_topic(project, topic_id, labels)
        return topic.to_dict()

    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/projects/{project}/topics/{topic}")
async def get_topic(project: str, topic: str) -> Dict[str, Any]:
    """Get a topic."""
    try:
        topic_obj = storage.get_topic(project, topic)
        if not topic_obj:
            raise HTTPException(status_code=404, detail="Topic not found")
        return topic_obj.to_dict()

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/projects/{project}/topics")
async def list_topics(project: str) -> Dict[str, List[Dict[str, Any]]]:
    """List topics in a project."""
    try:
        topics = storage.list_topics(project)
        return {
            "topics": [t.to_dict() for t in topics],
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/projects/{project}/topics/{topic}")
async def delete_topic(project: str, topic: str) -> Dict[str, Any]:
    """Delete a topic."""
    try:
        if not storage.topic_exists(project, topic):
            raise HTTPException(status_code=404, detail="Topic not found")

        storage.delete_topic(project, topic)
        return {}

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================================
# SUBSCRIPTIONS
# ============================================================================

@router.post("/projects/{project}/subscriptions")
async def create_subscription(
    project: str,
    request: Dict[str, Any],
) -> Dict[str, Any]:
    """Create a new subscription."""
    try:
        subscription_id = request.get("name", "").split("/")[-1]
        if not subscription_id:
            raise ValueError("Subscription name required")

        topic_path = request.get("topic", "")
        topic_id = topic_path.split("/")[-1]
        if not topic_id:
            raise ValueError("Topic required")

        if not storage.topic_exists(project, topic_id):
            raise HTTPException(status_code=404, detail="Topic not found")

        labels = request.get("labels", {})
        delivery_type = DeliveryType(request.get("deliveryType", "PULL"))
        push_config = request.get("pushConfig")
        ack_deadline_seconds = request.get("ackDeadlineSeconds", 60)

        subscription = storage.create_subscription(
            project,
            subscription_id,
            topic_id,
            labels=labels,
            delivery_type=delivery_type,
            push_config=push_config,
            ack_deadline_seconds=ack_deadline_seconds,
        )
        return subscription.to_dict()

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/projects/{project}/subscriptions/{subscription}")
async def get_subscription(project: str, subscription: str) -> Dict[str, Any]:
    """Get a subscription."""
    try:
        sub_obj = storage.get_subscription(project, subscription)
        if not sub_obj:
            raise HTTPException(status_code=404, detail="Subscription not found")
        return sub_obj.to_dict()

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/projects/{project}/subscriptions")
async def list_subscriptions(
    project: str,
    topic: Optional[str] = Query(None),
) -> Dict[str, List[Dict[str, Any]]]:
    """List subscriptions in a project."""
    try:
        topic_id = topic.split("/")[-1] if topic else None
        subscriptions = storage.list_subscriptions(project, topic_id)
        return {
            "subscriptions": [s.to_dict() for s in subscriptions],
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/projects/{project}/subscriptions/{subscription}")
async def delete_subscription(project: str, subscription: str) -> Dict[str, Any]:
    """Delete a subscription."""
    try:
        if not storage.subscription_exists(project, subscription):
            raise HTTPException(status_code=404, detail="Subscription not found")

        storage.delete_subscription(project, subscription)
        return {}

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================================
# MESSAGE PUBLISHING
# ============================================================================

@router.post("/projects/{project}/topics/{topic}:publish")
async def publish(
    project: str,
    topic: str,
    request: Dict[str, Any],
) -> Dict[str, List[str]]:
    """Publish messages to a topic."""
    try:
        if not storage.topic_exists(project, topic):
            raise HTTPException(status_code=404, detail="Topic not found")

        messages = request.get("messages", [])
        if not messages:
            raise ValueError("No messages provided")

        message_ids = []
        for msg in messages:
            # msg should have: data (base64), attributes (optional)
            data = msg.get("data", "")
            attributes = msg.get("attributes", {})

            msg_id = storage.publish_message(project, topic, data, attributes)
            message_ids.append(msg_id)

        logger.info(f"[PubSub] Published {len(message_ids)} messages to {topic}")
        return {"messageIds": message_ids}

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


# ============================================================================
# MESSAGE PULLING
# ============================================================================

@router.post("/projects/{project}/subscriptions/{subscription}:pull")
async def pull(
    project: str,
    subscription: str,
    request: Dict[str, Any],
) -> Dict[str, Any]:
    """Pull messages from a subscription."""
    try:
        if not storage.subscription_exists(project, subscription):
            raise HTTPException(status_code=404, detail="Subscription not found")

        max_messages = request.get("maxMessages", 100)
        return_immediately = request.get("returnImmediately", False)

        messages = storage.pull_messages(project, subscription, max_messages)

        return {
            "receivedMessages": messages,
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/projects/{project}/subscriptions/{subscription}:acknowledge")
async def acknowledge(
    project: str,
    subscription: str,
    request: Dict[str, Any],
) -> Dict[str, Any]:
    """Acknowledge messages."""
    try:
        if not storage.subscription_exists(project, subscription):
            raise HTTPException(status_code=404, detail="Subscription not found")

        ack_ids = request.get("ackIds", [])
        storage.acknowledge_messages(project, subscription, ack_ids)

        logger.debug(f"[PubSub] Acknowledged {len(ack_ids)} messages in {subscription}")
        return {}

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/projects/{project}/subscriptions/{subscription}:nack")
async def nack(
    project: str,
    subscription: str,
    request: Dict[str, Any],
) -> Dict[str, Any]:
    """Nack (negative acknowledge) messages."""
    try:
        if not storage.subscription_exists(project, subscription):
            raise HTTPException(status_code=404, detail="Subscription not found")

        ack_ids = request.get("ackIds", [])
        storage.nack_messages(project, subscription, ack_ids)

        logger.debug(f"[PubSub] Nacked {len(ack_ids)} messages in {subscription}")
        return {}

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


# ============================================================================
# HEALTH CHECK
# ============================================================================

@router.get("/pubsub/health")
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
