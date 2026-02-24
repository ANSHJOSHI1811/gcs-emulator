"""
Cloud Pub/Sub storage layer.

Handles in-memory storage and retrieval of topics, subscriptions, and messages.
"""

from typing import Dict, List, Optional, Tuple
from datetime import datetime, timezone, timedelta
import uuid
import base64

from .models import Topic, Subscription, PubsubMessage, DeliveryType


class PubSubStorage:
    """In-memory storage for Pub/Sub data."""

    def __init__(self):
        """Initialize storage containers."""
        # Structure: {project_id: {topic_id: Topic}}
        self.topics: Dict[str, Dict[str, Topic]] = {}

        # Structure: {project_id: {subscription_id: Subscription}}
        self.subscriptions: Dict[str, Dict[str, Subscription]] = {}

        # Message queue for each topic: {project_id: {topic_id: [PubsubMessage]}}
        self.topic_messages: Dict[str, Dict[str, List[Dict]]] = {}

        # Subscription message state: tracks ack_id -> (message, ack_deadline_time)
        # {project_id: {subscription_id: {ack_id: {message, deadline_time}}}}
        self.subscription_pending: Dict[str, Dict[str, Dict[str, Tuple]]] = {}

    # ========== TOPICS ==========

    def create_topic(self, project: str, topic_id: str, labels: Dict[str, str] = None) -> Topic:
        """Create a new topic."""
        if project not in self.topics:
            self.topics[project] = {}

        topic_name = f"projects/{project}/topics/{topic_id}"
        topic = Topic(
            name=topic_name,
            labels=labels or {}
        )
        self.topics[project][topic_id] = topic

        # Initialize message queue for this topic
        if project not in self.topic_messages:
            self.topic_messages[project] = {}
        self.topic_messages[project][topic_id] = []

        return topic

    def get_topic(self, project: str, topic_id: str) -> Optional[Topic]:
        """Retrieve a topic."""
        return self.topics.get(project, {}).get(topic_id)

    def list_topics(self, project: str) -> List[Topic]:
        """List all topics in a project."""
        return list(self.topics.get(project, {}).values())

    def delete_topic(self, project: str, topic_id: str) -> None:
        """Delete a topic."""
        if project in self.topics:
            self.topics[project].pop(topic_id, None)
        if project in self.topic_messages:
            self.topic_messages[project].pop(topic_id, None)

    def topic_exists(self, project: str, topic_id: str) -> bool:
        """Check if topic exists."""
        return topic_id in self.topics.get(project, {})

    # ========== SUBSCRIPTIONS ==========

    def create_subscription(
        self,
        project: str,
        subscription_id: str,
        topic_id: str,
        labels: Dict[str, str] = None,
        delivery_type: DeliveryType = DeliveryType.PULL,
        push_config: Dict = None,
        ack_deadline_seconds: int = 60,
    ) -> Subscription:
        """Create a new subscription."""
        if project not in self.subscriptions:
            self.subscriptions[project] = {}
        if project not in self.subscription_pending:
            self.subscription_pending[project] = {}

        sub_name = f"projects/{project}/subscriptions/{subscription_id}"
        topic_name = f"projects/{project}/topics/{topic_id}"

        subscription = Subscription(
            name=sub_name,
            topic=topic_name,
            labels=labels or {},
            delivery_type=delivery_type,
            push_config=push_config,
            ack_deadline_seconds=ack_deadline_seconds,
        )

        self.subscriptions[project][subscription_id] = subscription
        self.subscription_pending[project][subscription_id] = {}

        return subscription

    def get_subscription(self, project: str, subscription_id: str) -> Optional[Subscription]:
        """Retrieve a subscription."""
        return self.subscriptions.get(project, {}).get(subscription_id)

    def list_subscriptions(self, project: str, topic_id: Optional[str] = None) -> List[Subscription]:
        """List subscriptions, optionally filtered by topic."""
        subs = list(self.subscriptions.get(project, {}).values())
        if topic_id:
            topic_name = f"projects/{project}/topics/{topic_id}"
            subs = [s for s in subs if s.topic == topic_name]
        return subs

    def delete_subscription(self, project: str, subscription_id: str) -> None:
        """Delete a subscription."""
        if project in self.subscriptions:
            self.subscriptions[project].pop(subscription_id, None)
        if project in self.subscription_pending:
            self.subscription_pending[project].pop(subscription_id, None)

    def subscription_exists(self, project: str, subscription_id: str) -> bool:
        """Check if subscription exists."""
        return subscription_id in self.subscriptions.get(project, {})

    # ========== MESSAGES ==========

    def publish_message(self, project: str, topic_id: str, data: str, attributes: Dict[str, str] = None) -> str:
        """Publish a message to a topic."""
        message = {
            "data": data,
            "attributes": attributes or {},
            "messageId": str(uuid.uuid4()),
            "publishTime": datetime.now(timezone.utc).isoformat(),
        }

        # Store in topic message queue
        if project in self.topic_messages and topic_id in self.topic_messages[project]:
            self.topic_messages[project][topic_id].append(message)

        return message["messageId"]

    def pull_messages(
        self,
        project: str,
        subscription_id: str,
        max_messages: int = 100,
    ) -> List[Tuple[str, Dict]]:
        """
        Pull messages from a subscription.

        Returns list of (ack_id, message) tuples.
        """
        subscription = self.get_subscription(project, subscription_id)
        if not subscription:
            return []

        # Extract topic_id from topic name
        topic_id = subscription.topic.split("/")[-1]

        # Get messages from topic queue
        messages_to_pull = []
        if project in self.topic_messages and topic_id in self.topic_messages[project]:
            available = self.topic_messages[project][topic_id]
            # Get up to max_messages
            for i in range(min(max_messages, len(available))):
                message = available.pop(0)
                ack_id = str(uuid.uuid4())

                # Track for acknowledgment
                if project not in self.subscription_pending:
                    self.subscription_pending[project] = {}
                if subscription_id not in self.subscription_pending[project]:
                    self.subscription_pending[project][subscription_id] = {}

                deadline = datetime.now(timezone.utc) + timedelta(seconds=subscription.ack_deadline_seconds)
                self.subscription_pending[project][subscription_id][ack_id] = {
                    "message": message,
                    "deadline": deadline,
                }

                messages_to_pull.append({
                    "ackId": ack_id,
                    "message": message,
                })

        return messages_to_pull

    def acknowledge_messages(self, project: str, subscription_id: str, ack_ids: List[str]) -> None:
        """Acknowledge messages."""
        if project not in self.subscription_pending or subscription_id not in self.subscription_pending[project]:
            return

        for ack_id in ack_ids:
            self.subscription_pending[project][subscription_id].pop(ack_id, None)

    def nack_messages(self, project: str, subscription_id: str, ack_ids: List[str]) -> None:
        """Negative acknowledge messages (return to topic queue)."""
        subscription = self.get_subscription(project, subscription_id)
        if not subscription:
            return

        topic_id = subscription.topic.split("/")[-1]

        if project not in self.subscription_pending or subscription_id not in self.subscription_pending[project]:
            return

        # Move messages back to topic queue
        for ack_id in ack_ids:
            pending = self.subscription_pending[project][subscription_id].pop(ack_id, None)
            if pending:
                message = pending["message"]
                if project not in self.topic_messages:
                    self.topic_messages[project] = {}
                if topic_id not in self.topic_messages[project]:
                    self.topic_messages[project][topic_id] = []
                # Add back to front of queue (LIFO)
                self.topic_messages[project][topic_id].insert(0, message)

    def get_message_count(self, project: str, topic_id: str) -> int:
        """Get count of messages in topic queue."""
        return len(self.topic_messages.get(project, {}).get(topic_id, []))

    def get_pending_count(self, project: str, subscription_id: str) -> int:
        """Get count of pending (acked but not delivered) messages."""
        return len(self.subscription_pending.get(project, {}).get(subscription_id, {}))

    # ========== HEALTH CHECK ==========

    def health_check(self) -> Dict[str, int]:
        """Return storage statistics."""
        total_topics = sum(len(topics) for topics in self.topics.values())
        total_subscriptions = sum(len(subs) for subs in self.subscriptions.values())
        total_messages = sum(
            len(msgs)
            for project_msgs in self.topic_messages.values()
            for msgs in project_msgs.values()
        )
        total_pending = sum(
            len(pending)
            for project_pending in self.subscription_pending.values()
            for pending in project_pending.values()
        )

        return {
            "topics": total_topics,
            "subscriptions": total_subscriptions,
            "messages": total_messages,
            "pending": total_pending,
        }
