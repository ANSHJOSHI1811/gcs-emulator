"""
GKE (Google Kubernetes Engine) Metric Publisher.

Auto-publishes metrics for GKE clusters and workloads to Cloud Monitoring.
Collects: Node CPU/Memory, Pod count, Container restarts, Network bandwidth.
"""

import asyncio
import random
import uuid
from datetime import datetime, timezone, timedelta
from typing import Dict, List, Any, Optional
import logging

logger = logging.getLogger(__name__)


class GKEMetricPublisher:
    """Publishes GKE cluster metrics to Cloud Monitoring."""

    def __init__(self, storage, monitoring_storage):
        """Initialize with references to GKE and monitoring storage."""
        self.storage = storage  # GKE storage for clusters
        self.monitoring_storage = monitoring_storage  # Monitoring storage
        self.running = False
        self.publish_interval = 10  # seconds

    async def start(self):
        """Start the metric publisher background task."""
        self.running = True
        logger.info("[GKEMetricPublisher] Started metric publisher")
        try:
            while self.running:
                await self._publish_metrics()
                await asyncio.sleep(self.publish_interval)
        except Exception as e:
            logger.error(f"[GKEMetricPublisher] Error in publisher loop: {e}")

    async def stop(self):
        """Stop the metric publisher."""
        self.running = False
        logger.info("[GKEMetricPublisher] Stopped metric publisher")

    async def _publish_metrics(self):
        """Collect and publish metrics for all clusters."""
        try:
            # Get all clusters from GKE storage
            all_clusters = {}
            
            # The GKE storage has structure: {project_id: {cluster_id: Cluster}}
            if hasattr(self.storage, 'clusters'):
                for project_id, clusters in self.storage.clusters.items():
                    for cluster_id, cluster in clusters.items():
                        if project_id not in all_clusters:
                            all_clusters[project_id] = []
                        all_clusters[project_id].append({
                            'project': project_id,
                            'cluster_id': cluster_id,
                            'cluster': cluster,
                        })

            # Publish metrics for each cluster
            for project_id, clusters in all_clusters.items():
                for cluster_data in clusters:
                    await self._publish_cluster_metrics(cluster_data)

        except Exception as e:
            logger.error(f"[GKEMetricPublisher] Error publishing metrics: {e}")

    async def _publish_cluster_metrics(self, cluster_data: Dict[str, Any]):
        """Publish metrics for a single cluster."""
        try:
            project = cluster_data['project']
            cluster_id = cluster_data['cluster_id']
            cluster = cluster_data['cluster']

            # Generate simulated metrics
            now = datetime.now(timezone.utc)
            point_end = now
            point_start = now - timedelta(seconds=60)

            # Simulate node metrics
            node_count = getattr(cluster, 'node_count', random.randint(2, 10))
            node_cpu_usage = round(30 + random.random() * 60, 2)  # 30-90%
            node_memory_usage = round(40 + random.random() * 50, 2)  # 40-90%
            
            # Simulate pod metrics
            pod_count = node_count * random.randint(5, 20)
            pod_cpu_usage = round(20 + random.random() * 70, 2)  # 20-90%
            pod_memory_usage = round(25 + random.random() * 60, 2)  # 25-85%
            
            # Container restarts (simulated)
            container_restarts = random.randint(0, 5)
            
            # Network bandwidth (simulated MB/s)
            network_bandwidth = round(10 + random.random() * 100, 2)

            # Time series data
            time_series_list = [
                {
                    "metric": {
                        "type": "kubernetes.io/node/cpu/allocatable_utilization",
                        "labels": {}
                    },
                    "resource": {
                        "type": "k8s_cluster",
                        "labels": {
                            "cluster_name": cluster_id,
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
                            "value": {"doubleValue": node_cpu_usage},
                        }
                    ],
                },
                {
                    "metric": {
                        "type": "kubernetes.io/node/memory/allocatable_utilization",
                        "labels": {}
                    },
                    "resource": {
                        "type": "k8s_cluster",
                        "labels": {
                            "cluster_name": cluster_id,
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
                            "value": {"doubleValue": node_memory_usage},
                        }
                    ],
                },
                {
                    "metric": {
                        "type": "kubernetes.io/pod/cpu/core_usage_time",
                        "labels": {}
                    },
                    "resource": {
                        "type": "k8s_cluster",
                        "labels": {
                            "cluster_name": cluster_id,
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
                            "value": {"doubleValue": pod_cpu_usage},
                        }
                    ],
                },
                {
                    "metric": {
                        "type": "kubernetes.io/pod/memory/used_bytes",
                        "labels": {}
                    },
                    "resource": {
                        "type": "k8s_cluster",
                        "labels": {
                            "cluster_name": cluster_id,
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
                            "value": {"int64Value": int(pod_memory_usage * 1024 * 1024)},  # In bytes
                        }
                    ],
                },
                {
                    "metric": {
                        "type": "kubernetes.io/container/restart_count",
                        "labels": {}
                    },
                    "resource": {
                        "type": "k8s_cluster",
                        "labels": {
                            "cluster_name": cluster_id,
                            "project_id": project,
                        }
                    },
                    "metricKind": "CUMULATIVE",
                    "valueType": "INT64",
                    "points": [
                        {
                            "interval": {
                                "startTime": point_start.isoformat(),
                                "endTime": point_end.isoformat(),
                            },
                            "value": {"int64Value": container_restarts},
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
                    from services.monitoring.models import (
                        MetricDescriptor, MetricKind, ValueType
                    )
                    
                    # Map metric kind
                    kind_map = {
                        "GAUGE": MetricKind.GAUGE,
                        "DELTA": MetricKind.DELTA,
                        "CUMULATIVE": MetricKind.CUMULATIVE,
                    }
                    
                    descriptor = MetricDescriptor(
                        name=f"projects/{project}/metricDescriptors/{metric_type}",
                        type=metric_type,
                        metric_kind=kind_map.get(ts.get("metricKind"), MetricKind.GAUGE),
                        value_type=ValueType.DOUBLE if ts.get("valueType") == "DOUBLE" else ValueType.INT64,
                        unit="%" if "utilization" in metric_type else "1",
                        description=f"Auto-published metric from GKE cluster",
                        display_name=metric_type,
                    )
                    self.monitoring_storage.put_metric_descriptor(project, descriptor)

            logger.debug(f"[GKEMetricPublisher] Published {len(time_series_list)} metrics for cluster {cluster_id}")

        except Exception as e:
            logger.error(f"[GKEMetricPublisher] Error publishing cluster metrics: {e}")

    def get_cluster_count(self) -> int:
        """Get total count of clusters being monitored."""
        try:
            count = 0
            if hasattr(self.storage, 'clusters'):
                for clusters in self.storage.clusters.values():
                    count += len(clusters)
            return count
        except Exception:
            return 0
