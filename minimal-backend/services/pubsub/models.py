"""
Cloud Pub/Sub data models.

Defines Topic, Subscription, Message, and related classes
for GCP Pub/Sub service simulator.
"""

from dataclasses import dataclass, field, asdict
from datetime import datetime, timezone
from enum import Enum
from typing import Optional, List, Dict, Any
import uuid


class DeliveryType(str, Enum):
    """Subscription delivery type."""
    PULL = "PULL"                      # Pull-based delivery
    PUSH = "PUSH"                      # Push-based delivery


class DeadLetterPolicy(Enum):
    """Dead letter policy for failed messages."""
    DEFAULT = "DEFAULT"                # Move to DLQ after max retries
    DISCARD = "DISCARD"                # Discard failed messages
    RETRY = "RETRY"                    # Keep retrying indefinitely


@dataclass
class Topic:
    """Cloud Pub/Sub Topic."""
    name: str                           # projects/{project}/topics/{topic_id}
    labels: Dict[str, str] = field(default_factory=dict)
    message_retention_duration: str = "604800s"  # Default 7 days
    kms_key_name: Optional[str] = None
    created_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    updated_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "name": self.name,
            "labels": self.labels,
            "messageRetentionDuration": self.message_retention_duration,
            "kmsKeyName": self.kms_key_name,
        }


@dataclass
class PubsubMessage:
    """A Pub/Sub message."""
    data: str                           # Base64-encoded message data
    attributes: Dict[str, str] = field(default_factory=dict)
    message_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    publish_time: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "data": self.data,
            "attributes": self.attributes,
            "messageId": self.message_id,
            "publishTime": self.publish_time,
        }


@dataclass
class PullResponse:
    """Response from pull RPC."""
    message_id: str
    ack_id: str                         # Used to acknowledge message
    message: Dict[str, Any]             # {data, attributes, messageId, publishTime}

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "ackId": self.ack_id,
            "message": self.message,
        }


@dataclass
class Subscription:
    """Cloud Pub/Sub Subscription."""
    name: str                           # projects/{project}/subscriptions/{sub_id}
    topic: str                          # projects/{project}/topics/{topic_id}
    labels: Dict[str, str] = field(default_factory=dict)
    delivery_type: DeliveryType = DeliveryType.PULL
    push_config: Optional[Dict[str, Any]] = None
    ack_deadline_seconds: int = 60
    message_retention_duration: str = "604800s"  # 7 days
    dead_letter_policy: Optional[Dict[str, Any]] = None
    enable_message_ordering: bool = False
    filter_str: Optional[str] = None    # Message filtering expression
    created_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    
    # Runtime state
    messages: List[Dict[str, Any]] = field(default_factory=list)
    pending_acks: Dict[str, Dict[str, Any]] = field(default_factory=dict)  # {ack_id: message}

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "name": self.name,
            "topic": self.topic,
            "labels": self.labels,
            "deliveryType": self.delivery_type.value,
            "pushConfig": self.push_config,
            "ackDeadlineSeconds": self.ack_deadline_seconds,
            "messageRetentionDuration": self.message_retention_duration,
            "deadLetterPolicy": self.dead_letter_policy,
            "enableMessageOrdering": self.enable_message_ordering,
            "filter": self.filter_str,
        }


@dataclass
class PublishRequest:
    """Request to publish messages to a topic."""
    messages: List[Dict[str, str]]      # [{data, attributes}, ...]


@dataclass
class PublishResponse:
    """Response from publish RPC."""
    message_ids: List[str]              # Published message IDs

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "messageIds": self.message_ids,
        }


@dataclass
class PullRequest:
    """Request to pull messages from a subscription."""
    max_messages: int = 100
    return_immediately: bool = False

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "maxMessages": self.max_messages,
            "returnImmediately": self.return_immediately,
        }


@dataclass
class PullResponse_Message:
    """Single message in pull response."""
    ack_id: str
    message: Dict[str, Any]

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "ackId": self.ack_id,
            "message": self.message,
        }


@dataclass
class PullResponse_Full:
    """Response from pull RPC with messages."""
    received_messages: List[Dict[str, Any]] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "receivedMessages": self.received_messages,
        }


@dataclass
class AcknowledgeRequest:
    """Request to acknowledge messages."""
    ack_ids: List[str]

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "ackIds": self.ack_ids,
        }
