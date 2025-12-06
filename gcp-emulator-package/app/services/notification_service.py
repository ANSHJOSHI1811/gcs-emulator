"""
Notification/Event Delivery service
Handles webhook delivery for bucket notifications
"""
import json
import requests
from typing import Optional
from app.logging import log_service_stage


class NotificationService:
    """Service for delivering event notifications to webhooks"""
    
    @staticmethod
    def deliver_event(
        bucket_name: str,
        object_name: str,
        event_type: str,
        webhook_url: str,
        metadata: dict = None,
        generation: int = None
    ) -> bool:
        """
        Deliver an event notification to a webhook URL
        
        Args:
            bucket_name: The bucket name
            object_name: The object name
            event_type: Event type (OBJECT_FINALIZE, OBJECT_DELETE, etc.)
            webhook_url: The webhook URL to POST to
            metadata: Optional additional metadata
            generation: Optional object generation
            
        Returns:
            True if delivery successful, False otherwise
        """
        payload = {
            "kind": "storage#objectChangeNotification",
            "bucket": bucket_name,
            "object": object_name,
            "eventType": event_type,
            "generation": generation,
            "metadata": metadata or {}
        }
        
        log_service_stage(
            message="Attempting event notification delivery",
            details={
                "bucket": bucket_name,
                "object": object_name,
                "event_type": event_type,
                "webhook_url": webhook_url
            }
        )
        
        # Try delivery with one retry
        for attempt in range(2):
            try:
                response = requests.post(
                    webhook_url,
                    json=payload,
                    headers={"Content-Type": "application/json"},
                    timeout=5  # 5 second timeout
                )
                
                if response.status_code < 400:
                    log_service_stage(
                        message="Event notification delivered successfully",
                        details={
                            "bucket": bucket_name,
                            "object": object_name,
                            "status_code": response.status_code,
                            "attempt": attempt + 1
                        }
                    )
                    return True
                else:
                    log_service_stage(
                        message=f"Event notification delivery failed with HTTP {response.status_code}",
                        details={
                            "bucket": bucket_name,
                            "attempt": attempt + 1,
                            "status_code": response.status_code
                        }
                    )
            except requests.RequestException as e:
                log_service_stage(
                    message=f"Event notification delivery exception: {str(e)}",
                    details={
                        "bucket": bucket_name,
                        "attempt": attempt + 1,
                        "error": str(e)
                    }
                )
        
        # Both attempts failed
        log_service_stage(
            message="Event notification delivery failed after retries",
            details={
                "bucket": bucket_name,
                "object": object_name,
                "webhook_url": webhook_url
            }
        )
        return False
    
    @staticmethod
    def get_notification_configs(bucket_obj) -> list:
        """
        Get notification configurations for a bucket
        
        Args:
            bucket_obj: Bucket model instance
            
        Returns:
            List of notification config dictionaries
        """
        if not bucket_obj.notification_configs:
            return []
        
        try:
            return json.loads(bucket_obj.notification_configs)
        except json.JSONDecodeError:
            return []
    
    @staticmethod
    def trigger_notifications(
        bucket_obj,
        object_name: str,
        event_type: str,
        generation: int = None
    ):
        """
        Trigger all configured notifications for an event
        
        Args:
            bucket_obj: Bucket model instance
            object_name: The object name
            event_type: Event type
            generation: Optional object generation
        """
        configs = NotificationService.get_notification_configs(bucket_obj)
        
        for config in configs:
            webhook_url = config.get("webhookUrl")
            event_types = config.get("eventTypes", [])
            
            # Check if this notification applies to this event type
            if webhook_url and (not event_types or event_type in event_types):
                NotificationService.deliver_event(
                    bucket_name=bucket_obj.name,
                    object_name=object_name,
                    event_type=event_type,
                    webhook_url=webhook_url,
                    generation=generation
                )
