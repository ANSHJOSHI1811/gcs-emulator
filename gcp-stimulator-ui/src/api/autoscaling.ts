import { apiClient, getCurrentProject } from './client';

export enum ScalingMetricType {
  CPU_UTILIZATION = 'CPU_UTILIZATION',
  MEMORY_UTILIZATION = 'MEMORY_UTILIZATION',
  CUSTOM_METRIC = 'CUSTOM_METRIC',
  LB_SERVING_CAPACITY = 'LB_SERVING_CAPACITY',
  PUBSUB_MESSAGE_BACKLOG = 'PUBSUB_MESSAGE_BACKLOG',
}

export interface ScalingRule {
  metricType: ScalingMetricType;
  targetValue: number;
  metricName?: string;
  scaleUpThreshold: number;
  scaleDownThreshold: number;
  cooldownSeconds: number;
}

export interface AutoscalingPolicy {
  name: string;
  description?: string;
  target: string;
  minReplicas: number;
  maxReplicas: number;
  targetSize?: number;
  currentSize: number;
  scalingRules: ScalingRule[];
  enabled: boolean;
  createdAt: string;
  updatedAt: string;
  lastScalingTime?: string;
  lastAction?: 'SCALED_UP' | 'SCALED_DOWN' | 'IDLE';
  status: 'ACTIVE' | 'DELETED' | 'PENDING_CREATION';
}

export interface AutoscalerStatus {
  policyName: string;
  currentReplicas: number;
  desiredReplicas: number;
  proposedSize?: number;
  currentMetricValue?: number;
  statusMessage: string;
}

export interface ScalingAction {
  timestamp: string;
  policyName: string;
  action: 'SCALE_UP' | 'SCALE_DOWN' | 'IDLE';
  oldSize: number;
  newSize: number;
  reason: string;
  metricValue: number;
}

/**
 * List all autoscaling policies in a zone
 */
export async function listAutoscalers(
  zone: string,
  project?: string
): Promise<AutoscalingPolicy[]> {
  const proj = project || getCurrentProject();
  const response = await apiClient.get<{ items?: AutoscalingPolicy[] }>(
    `/compute/v1/projects/${proj}/zones/${zone}/autoscalers`
  );
  return response.data.items ?? [];
}

/**
 * Get a specific autoscaling policy
 */
export async function getAutoscaler(
  zone: string,
  autoscalerId: string,
  project?: string
): Promise<AutoscalingPolicy> {
  const proj = project || getCurrentProject();
  const response = await apiClient.get<AutoscalingPolicy>(
    `/compute/v1/projects/${proj}/zones/${zone}/autoscalers/${autoscalerId}`
  );
  return response.data;
}

/**
 * Create a new autoscaling policy
 */
export async function createAutoscaler(
  zone: string,
  autoscalerId: string,
  target: string,
  minReplicas: number,
  maxReplicas: number,
  scalingRules: Partial<ScalingRule>[],
  description?: string,
  project?: string
): Promise<AutoscalingPolicy> {
  const proj = project || getCurrentProject();
  const response = await apiClient.post<AutoscalingPolicy>(
    `/compute/v1/projects/${proj}/zones/${zone}/autoscalers`,
    {
      name: `projects/${proj}/zones/${zone}/autoscalers/${autoscalerId}`,
      target,
      description,
      minReplicas,
      maxReplicas,
      scalingRules: scalingRules.map(rule => ({
        metricType: rule.metricType || ScalingMetricType.CPU_UTILIZATION,
        targetValue: rule.targetValue || 70,
        metricName: rule.metricName,
        scaleUpThreshold: rule.scaleUpThreshold || 80,
        scaleDownThreshold: rule.scaleDownThreshold || 20,
        cooldownSeconds: rule.cooldownSeconds || 300,
      })),
    }
  );
  return response.data;
}

/**
 * Update an existing autoscaling policy
 */
export async function updateAutoscaler(
  zone: string,
  autoscalerId: string,
  updates: {
    minReplicas?: number;
    maxReplicas?: number;
    scalingRules?: Partial<ScalingRule>[];
    enabled?: boolean;
  },
  project?: string
): Promise<AutoscalingPolicy> {
  const proj = project || getCurrentProject();
  const payload: Record<string, unknown> = {};

  if (updates.minReplicas !== undefined) payload.minReplicas = updates.minReplicas;
  if (updates.maxReplicas !== undefined) payload.maxReplicas = updates.maxReplicas;
  if (updates.enabled !== undefined) payload.enabled = updates.enabled;
  if (updates.scalingRules) {
    payload.scalingRules = updates.scalingRules.map(rule => ({
      metricType: rule.metricType || ScalingMetricType.CPU_UTILIZATION,
      targetValue: rule.targetValue || 70,
      metricName: rule.metricName,
      scaleUpThreshold: rule.scaleUpThreshold || 80,
      scaleDownThreshold: rule.scaleDownThreshold || 20,
      cooldownSeconds: rule.cooldownSeconds || 300,
    }));
  }

  const response = await apiClient.patch<AutoscalingPolicy>(
    `/compute/v1/projects/${proj}/zones/${zone}/autoscalers/${autoscalerId}`,
    payload
  );
  return response.data;
}

/**
 * Delete an autoscaling policy
 */
export async function deleteAutoscaler(
  zone: string,
  autoscalerId: string,
  project?: string
): Promise<void> {
  const proj = project || getCurrentProject();
  await apiClient.delete(
    `/compute/v1/projects/${proj}/zones/${zone}/autoscalers/${autoscalerId}`
  );
}

/**
 * Get status of a specific autoscaler
 */
export async function getAutoscalerStatus(
  zone: string,
  autoscalerId: string,
  project?: string
): Promise<AutoscalerStatus> {
  const proj = project || getCurrentProject();
  const response = await apiClient.get<AutoscalerStatus>(
    `/compute/v1/projects/${proj}/zones/${zone}/autoscalers/${autoscalerId}/status`
  );
  return response.data;
}

/**
 * List all autoscaler statuses in a zone
 */
export async function listAutoscalerStatuses(
  zone: string,
  project?: string
): Promise<AutoscalerStatus[]> {
  const proj = project || getCurrentProject();
  const response = await apiClient.get<{ items?: AutoscalerStatus[] }>(
    `/compute/v1/projects/${proj}/zones/${zone}/autoscalers/status`
  );
  return response.data.items ?? [];
}

/**
 * List instances in a zone (for autoscaler target selection)
 */
export async function listInstances(
  zone: string,
  project?: string
): Promise<{ name: string; status: string }[]> {
  const proj = project || getCurrentProject();
  try {
    const response = await apiClient.get<{
      items?: Array<{ name: string; status: string }>;
    }>(
      `/compute/v1/projects/${proj}/zones/${zone}/instances`
    );
    return response.data.items ?? [];
  } catch {
    return [];
  }
}

/**
 * List instance groups in a zone (for autoscaler target selection)
 */
export async function listInstanceGroups(
  zone: string,
  project?: string
): Promise<{ name: string; size: number }[]> {
  const proj = project || getCurrentProject();
  try {
    const response = await apiClient.get<{
      items?: Array<{ name: string; size: number }>;
    }>(
      `/compute/v1/projects/${proj}/zones/${zone}/instanceGroups`
    );
    return response.data.items ?? [];
  } catch {
    return [];
  }
}

/**
 * Get scaling action history for an autoscaler
 */
export async function getScalingHistory(
  zone: string,
  autoscalerId: string,
  limit: number = 20,
  project?: string
): Promise<ScalingAction[]> {
  const proj = project || getCurrentProject();
  const response = await apiClient.get<{ items?: ScalingAction[] }>(
    `/compute/v1/projects/${proj}/zones/${zone}/autoscalers/${autoscalerId}/actions`,
    { params: { limit } }
  );
  return response.data.items ?? [];
}
