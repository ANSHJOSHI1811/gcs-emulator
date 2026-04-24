"""
Cloud Run Metric Publisher.

Auto-publishes metrics for Cloud Run services to Cloud Monitoring.
Collects: Request count, execution time, error rate, memory usage, CPU time.
"""

import asyncio
import random
import uuid
from datetime import datetime, timezone, timedelta
from typing import Dict, List, Any, Optional
import logging

logger = logging.getLogger(__name__)


class CloudRunMetricPublisher:
    """Publishes Cloud Run service metrics to Cloud Monitoring."""

    def __init__(self, storage, monitoring_storage):
        """Initialize with references to Cloud Run and monitoring storage."""
        self.storage = storage  # Cloud Run storage for services
        self.monitoring_storage = monitoring_storage  # Monitoring storage
        self.running = False
        self.publish_interval = 10  # seconds
        self.request_counter = {}  # Track cumulative requests per service

    async def start(self):
        """Start the metric publisher background task."""
        self.running = True
        logger.info("[CloudRunMetricPublisher] Started metric publisher")
        try:
            while self.running:
                await self._publish_metrics()
                await asyncio.sleep(self.publish_interval)
        except Exception as e:
            logger.error(f"[CloudRunMetricPublisher] Error in publisher loop: {e}")

    async def stop(self):
        """Stop the metric publisher."""
        self.running = False
        logger.info("[CloudRunMetricPublisher] Stopped metric publisher")

    async def _publish_metrics(self):
        """Collect and publish metrics for all Cloud Run services."""
        try:
            # Get all services from Cloud Run storage
            all_services = {}
            
            # The Cloud Run storage has structure: {project_id: {service_id: Service}}
            if hasattr(self.storage, 'services'):
                for project_id, services in self.storage.services.items():
                    for service_id, service in services.items():
                        if project_id not in all_services:
                            all_services[project_id] = []
                        all_services[project_id].append({
                            'project': project_id,
                            'service_id': service_id,
                            'service': service,
                        })

            # Publish metrics for each service
            for project_id, services in all_services.items():
                for service_data in services:
                    await self._publish_service_metrics(service_data)

        except Exception as e:
            logger.error(f"[CloudRunMetricPublisher] Error publishing metrics: {e}")

    async def _publish_service_metrics(self, service_data: Dict[str, Any]):
        """Publish metrics for a single Cloud Run service."""
        try:
            project = service_data['project']
            service_id = service_data['service_id']
            service = service_data['service']

            # Generate simulated metrics
            now = datetime.now(timezone.utc)
            point_end = now
            point_start = now - timedelta(seconds=60)

            # Initialize counter if needed
            service_key = f"{project}/{service_id}"
            if service_key not in self.request_counter:
                self.request_counter[service_key] = 0

            # Simulate invocation metrics
            new_invocations = random.randint(5, 50)  # 5-50 invocations in this period
            self.request_counter[service_key] += new_invocations
            
            # Execution time (milliseconds, 50-500ms)
            avg_execution_time = round(50 + random.random() * 450, 2)
            
            # Error rate (0-5%)
            error_rate = round(random.random() * 5, 2)
            error_count = max(0, int(new_invocations * error_rate / 100))
            
            # Memory usage (MB, 128-512)
            memory_usage = random.randint(128, 512)
            
            # CPU milliseconds in period (50-900ms per second * 60 seconds)
            cpu_time = round((50 + random.random() * 850) * 60, 2)

            # Time series data
            time_series_list = [
                {
                    "metric": {
                        "type": "run.googleapis.com/request_count",
                        "labels": {}
                    },
                    "resource": {
                        "type": "cloud_run_revision",
                        "labels": {
                            "service_name": service_id,
                            "project_id": project,
                        }
                    },
                    "metricKind": "DELTA",
                    "valueType": "INT64",
                    "points": [
                        {
                            "interval": {
                                "startTime": point_start.isoformat(),
                                "endTime": point_end.isoformat(),
                            },
                            "value": {"int64Value": new_invocations},
                        }
                    ],
                },
                {
                    "metric": {
                        "type": "run.googleapis.com/request_latencies",
                        "labels": {}
                    },
                    "resource": {
                        "type": "cloud_run_revision",
                        "labels": {
                            "service_name": service_id,
                            "project_id": project,
                        }
                    },
                    "metricKind": "DELTA",
                    "valueType": "DOUBLE",
                    "points": [
                        {
                            "interval": {
                                "startTime": point_start.isoformat(),
                                "endTime": point_end.isoformat(),
                            },
                            "value": {"doubleValue": avg_execution_time},
                        }
                    ],
                },
                {
                    "metric": {
                        "type": "run.googleapis.com/request_count",
                        "labels": {"response_code": "4xx"}
                    },
                    "resource": {
                        "type": "cloud_run_revision",
                        "labels": {
                            "service_name": service_id,
                            "project_id": project,
                        }
                    },
                    "metricKind": "DELTA",
                    "valueType": "INT64",
                    "points": [
                        {
                            "interval": {
                                "startTime": point_start.isoformat(),
                                "endTime": point_end.isoformat(),
                            },
                            "value": {"int64Value": error_count},
                        }
                    ],
                },
                {
                    "metric": {
                        "type": "run.googleapis.com/instance_count",
                        "labels": {}
                    },
                    "resource": {
                        "type": "cloud_run_revision",
                        "labels": {
                            "service_name": service_id,
                            "project_id": project,
                        }
                    },
                    "metricKind": "GAUGE",
                    "valueType": "INT64",
                    "points": [
                        {
                            "interval": {
                                "startTime": point_start.isoformat(),
                                "endTime": point_end.isoformat(),
                            },
                            "value": {"int64Value": max(1, random.randint(1, 5))},
                        }
                    ],
                },
                {
                    "metric": {
                        "type": "run.googleapis.com/memory/utilization",
                        "labels": {}
                    },
                    "resource": {
                        "type": "cloud_run_revision",
                        "labels": {
                            "service_name": service_id,
                            "project_id": project,
                        }
                    },
                    "metricKind": "GAUGE",
                    "valueType": "INT64",
                    "points": [
                        {
                            "interval": {
                                "startTime": point_start.isoformat(),
                                "endTime": point_end.isoformat(),
                            },
                            "value": {"int64Value": int(memory_usage * 1024 * 1024)},  # In bytes
                        }
                    ],
                },
            ]

            # Store time series in monitoring storage
            for ts in time_series_list:
                self.monitoring_storage.put_time_series(project, ts)

                # Auto-create metric descriptor if needed
                metric_type = ts["metric"]["type"]
                if not self.monitoring_storage.get_metric_descriptor(project, metric_type):
                    from app.services.monitoring.models import (
                        MetricDescriptor, MetricKind, ValueType
                    )
                    
                    descriptor = MetricDescriptor(
                        name=f"projects/{project}/metricDescriptors/{metric_type}",
                        type=metric_type,
                        metric_kind=MetricKind.DELTA if "DELTA" in ts.get("metricKind", "GAUGE") else MetricKind.GAUGE,
                        value_type=ValueType.DOUBLE if ts.get("valueType") == "DOUBLE" else ValueType.INT64,
                        unit="ms" if "latenc" in metric_type else "1",
                        description=f"Auto-published metric from Cloud Run",
                        display_name=metric_type,
                    )
                    self.monitoring_storage.put_metric_descriptor(project, descriptor)

            logger.debug(f"[CloudRunMetricPublisher] Published {len(time_series_list)} metrics for service {service_id}")

        except Exception as e:
            logger.error(f"[CloudRunMetricPublisher] Error publishing service metrics: {e}")

    def get_service_count(self) -> int:
        """Get total count of services being monitored."""
        try:
            count = 0
            if hasattr(self.storage, 'services'):
                for services in self.storage.services.values():
                    count += len(services)
            return count
        except Exception:
            return 0
