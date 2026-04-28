"""
Compute Engine Metric Publisher.

Auto-publishes metrics for Compute Engine instances to Cloud Monitoring.
Collects: CPU usage, Memory utilization, Network I/O, Disk I/O.
"""

import asyncio
import random
import uuid
from datetime import datetime, timezone, timedelta
from typing import Dict, List, Any, Optional
import logging

logger = logging.getLogger(__name__)


class ComputeMetricPublisher:
    """Publishes Compute Engine instance metrics to Cloud Monitoring."""

    def __init__(self, storage, monitoring_storage):
        """Initialize with references to compute and monitoring storage."""
        self.storage = storage  # Compute storage for instances
        self.monitoring_storage = monitoring_storage  # Monitoring storage
        self.running = False
        self.publish_interval = 10  # seconds

    async def start(self):
        """Start the metric publisher background task."""
        self.running = True
        logger.info("[ComputeMetricPublisher] Started metric publisher")
        try:
            while self.running:
                await self._publish_metrics()
                await asyncio.sleep(self.publish_interval)
        except Exception as e:
            logger.error(f"[ComputeMetricPublisher] Error in publisher loop: {e}")

    async def stop(self):
        """Stop the metric publisher."""
        self.running = False
        logger.info("[ComputeMetricPublisher] Stopped metric publisher")

    async def _publish_metrics(self):
        """Collect and publish metrics for all instances."""
        try:
            # Get all instances from compute storage
            all_instances = {}
            
            # The compute storage has structure: {project_id: {zone: {instance_id: Instance}}}
            if hasattr(self.storage, 'instances'):
                for project_id, zones in self.storage.instances.items():
                    for zone, instances in zones.items():
                        for instance_id, instance in instances.items():
                            if project_id not in all_instances:
                                all_instances[project_id] = []
                            all_instances[project_id].append({
                                'project': project_id,
                                'zone': zone,
                                'instance_id': instance_id,
                                'instance': instance,
                            })

            # Publish metrics for each instance
            for project_id, instances in all_instances.items():
                for inst_data in instances:
                    await self._publish_instance_metrics(inst_data)

        except Exception as e:
            logger.error(f"[ComputeMetricPublisher] Error publishing metrics: {e}")

    async def _publish_instance_metrics(self, inst_data: Dict[str, Any]):
        """Publish metrics for a single instance."""
        try:
            project = inst_data['project']
            zone = inst_data['zone']
            instance_id = inst_data['instance_id']
            instance = inst_data['instance']

            # Generate simulated metrics
            now = datetime.now(timezone.utc)
            point_end = now
            point_start = now - timedelta(seconds=60)

            # CPU usage (simulated 20-95%)
            cpu_usage = round(20 + random.random() * 75, 2)

            # Memory utilization (simulated 30-80%)
            memory_usage = round(30 + random.random() * 50, 2)

            # Network I/O (simulated 100KB-500KB/s)
            network_io = round(100 + random.random() * 400, 2)

            # Disk I/O (simulated 1-50 IOPS)
            disk_io = round(1 + random.random() * 49, 2)

            # Time series data
            time_series_list = [
                {
                    "metric": {
                        "type": "compute.googleapis.com/instance/cpu/utilization",
                        "labels": {
                            "resource_name": instance_id,
                        }
                    },
                    "resource": {
                        "type": "gce_instance",
                        "labels": {
                            "instance_id": instance_id,
                            "zone": zone,
                            "project_id": project,
                        }
                    },
                    "metricKind": "GAUGE",
                    "valueType": "DOUBLE",
                    "points": [
                        {
                            "interval": {
                                "startTime": point_start.isoformat(),
                                "endTime": point_end.isoformat(),
                            },
                            "value": {"doubleValue": cpu_usage},
                        }
                    ],
                },
                {
                    "metric": {
                        "type": "compute.googleapis.com/instance/memory/utilization",
                        "labels": {
                            "resource_name": instance_id,
                        }
                    },
                    "resource": {
                        "type": "gce_instance",
                        "labels": {
                            "instance_id": instance_id,
                            "zone": zone,
                            "project_id": project,
                        }
                    },
                    "metricKind": "GAUGE",
                    "valueType": "DOUBLE",
                    "points": [
                        {
                            "interval": {
                                "startTime": point_start.isoformat(),
                                "endTime": point_end.isoformat(),
                            },
                            "value": {"doubleValue": memory_usage},
                        }
                    ],
                },
                {
                    "metric": {
                        "type": "compute.googleapis.com/instance/network/sent_bytes_count",
                        "labels": {}
                    },
                    "resource": {
                        "type": "gce_instance",
                        "labels": {
                            "instance_id": instance_id,
                            "zone": zone,
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
                            "value": {"int64Value": int(network_io * 1024)},  # Convert to bytes
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
                        metric_kind=MetricKind.GAUGE if ts.get("metricKind") == "GAUGE" else MetricKind.DELTA,
                        value_type=ValueType.DOUBLE if ts.get("valueType") == "DOUBLE" else ValueType.INT64,
                        unit="%" if "utilization" in metric_type else "1",
                        description=f"Auto-published metric from Compute Engine",
                        display_name=metric_type,
                    )
                    self.monitoring_storage.put_metric_descriptor(project, descriptor)

            logger.debug(f"[ComputeMetricPublisher] Published {len(time_series_list)} metrics for {instance_id}")

        except Exception as e:
            logger.error(f"[ComputeMetricPublisher] Error publishing instance metrics: {e}")

    def get_instance_count(self) -> int:
        """Get total count of instances being monitored."""
        try:
            count = 0
            if hasattr(self.storage, 'instances'):
                for zones in self.storage.instances.values():
                    for instances in zones.values():
                        count += len(instances)
            return count
        except Exception:
            return 0
