import { apiClient, getCurrentProject } from './client';

export enum MetricKind {
  GAUGE = 'GAUGE',
  DELTA = 'DELTA',
  CUMULATIVE = 'CUMULATIVE',
}

export enum ValueType {
  BOOL = 'BOOL',
  INT64 = 'INT64',
  DOUBLE = 'DOUBLE',
  STRING = 'STRING',
  DISTRIBUTION = 'DISTRIBUTION',
}

export interface MetricDescriptor {
  name: string;
  type: string;
  metricKind: MetricKind;
  valueType: ValueType;
  unit: string;
  description: string;
  displayName: string;
  labels: Array<{ key: string; valueType: string; description?: string }>;
  monitoredResourceTypes: string[];
}

export interface Point {
  interval: {
    endTime: string;
    startTime?: string;
  };
  value: {
    boolValue?: boolean;
    int64Value?: number;
    doubleValue?: number;
    stringValue?: string;
  };
}

export interface TimeSeries {
  metric: {
    type: string;
    labels?: Record<string, string>;
  };
  resource: {
    type: string;
    labels?: Record<string, string>;
  };
  metricKind: MetricKind;
  valueType: ValueType;
  points: Point[];
}

export interface Condition {
  name?: string;
  displayName?: string;
  conditionThreshold?: {
    filter: string;
    comparison: string;
    thresholdValue: number;
    duration: string;
    aggregations?: Array<{
      alignmentPeriod: string;
      perSeriesAligner: string;
      crossSeriesReducer?: string;
      groupByFields?: string[];
    }>;
  };
}

export interface AlertPolicy {
  name: string;
  displayName: string;
  documentation?: {
    content: string;
    mimeType?: string;
  };
  conditions: Condition[];
  combiner?: string;
  enabled: boolean;
  notificationChannels?: string[];
  creationRecord?: {
    mutateTime: string;
    mutatedBy: string;
  };
  mutationRecord?: {
    mutateTime: string;
    mutatedBy: string;
  };
}

export interface NotificationChannel {
  name: string;
  type: string;
  displayName: string;
  description?: string;
  labels?: Record<string, string>;
  userLabels?: Record<string, string>;
  enabled: boolean;
  creationRecord?: {
    mutateTime: string;
    mutatedBy: string;
  };
}

// ============================================================================
// METRIC DESCRIPTORS
// ============================================================================

/**
 * List metric descriptors
 */
export async function listMetricDescriptors(
  filter?: string,
  project?: string
): Promise<MetricDescriptor[]> {
  const proj = project || getCurrentProject();
  const params: Record<string, string> = {};
  if (filter) params.filter = filter;

  const response = await apiClient.get<{ metricDescriptors?: MetricDescriptor[] }>(
    `/v3/projects/${proj}/metricDescriptors`,
    { params }
  );
  return response.data.metricDescriptors ?? [];
}

/**
 * Get a specific metric descriptor
 */
export async function getMetricDescriptor(
  metricType: string,
  project?: string
): Promise<MetricDescriptor> {
  const proj = project || getCurrentProject();
  const response = await apiClient.get<MetricDescriptor>(
    `/v3/projects/${proj}/metricDescriptors/${encodeURIComponent(metricType)}`
  );
  return response.data;
}

/**
 * Create a metric descriptor
 */
export async function createMetricDescriptor(
  metricType: string,
  metricKind: MetricKind,
  valueType: ValueType,
  displayName: string,
  description?: string,
  unit?: string,
  project?: string
): Promise<MetricDescriptor> {
  const proj = project || getCurrentProject();
  const response = await apiClient.post<MetricDescriptor>(
    `/v3/projects/${proj}/metricDescriptors`,
    {
      type: metricType,
      metricKind,
      valueType,
      displayName,
      description: description || '',
      unit: unit || '1',
      labels: [],
      monitoredResourceTypes: [],
    }
  );
  return response.data;
}

/**
 * Delete a metric descriptor
 */
export async function deleteMetricDescriptor(
  metricType: string,
  project?: string
): Promise<void> {
  const proj = project || getCurrentProject();
  await apiClient.delete(
    `/v3/projects/${proj}/metricDescriptors/${encodeURIComponent(metricType)}`
  );
}

// ============================================================================
// TIME SERIES
// ============================================================================

/**
 * Query time series data
 */
export async function queryTimeSeries(
  filter: string,
  startTime?: string,
  endTime?: string,
  project?: string
): Promise<TimeSeries[]> {
  const proj = project || getCurrentProject();
  const params: Record<string, string> = { filter };
  
  if (startTime) params['interval.startTime'] = startTime;
  if (endTime) params['interval.endTime'] = endTime;

  const response = await apiClient.get<{ timeSeries?: TimeSeries[] }>(
    `/v3/projects/${proj}/timeSeries`,
    { params }
  );
  return response.data.timeSeries ?? [];
}

/**
 * Write time series data
 */
export async function writeTimeSeries(
  timeSeries: Partial<TimeSeries>[],
  project?: string
): Promise<void> {
  const proj = project || getCurrentProject();
  await apiClient.post(`/v3/projects/${proj}/timeSeries`, { timeSeries });
}

// ============================================================================
// ALERT POLICIES
// ============================================================================

/**
 * List alert policies
 */
export async function listAlertPolicies(project?: string): Promise<AlertPolicy[]> {
  const proj = project || getCurrentProject();
  const response = await apiClient.get<{ alertPolicies?: AlertPolicy[] }>(
    `/v3/projects/${proj}/alertPolicies`
  );
  return response.data.alertPolicies ?? [];
}

/**
 * Get a specific alert policy
 */
export async function getAlertPolicy(
  policyId: string,
  project?: string
): Promise<AlertPolicy> {
  const proj = project || getCurrentProject();
  const response = await apiClient.get<AlertPolicy>(
    `/v3/projects/${proj}/alertPolicies/${policyId}`
  );
  return response.data;
}

/**
 * Create an alert policy
 */
export async function createAlertPolicy(
  displayName: string,
  conditions: Condition[],
  notificationChannels?: string[],
  documentation?: string,
  project?: string
): Promise<AlertPolicy> {
  const proj = project || getCurrentProject();
  const response = await apiClient.post<AlertPolicy>(
    `/v3/projects/${proj}/alertPolicies`,
    {
      displayName,
      conditions,
      combiner: 'OR',
      enabled: true,
      notificationChannels: notificationChannels || [],
      documentation: documentation ? { content: documentation, mimeType: 'text/markdown' } : undefined,
    }
  );
  return response.data;
}

/**
 * Update an alert policy
 */
export async function updateAlertPolicy(
  policyId: string,
  updates: {
    displayName?: string;
    conditions?: Condition[];
    enabled?: boolean;
    notificationChannels?: string[];
    documentation?: string;
  },
  project?: string
): Promise<AlertPolicy> {
  const proj = project || getCurrentProject();
  const payload: Record<string, unknown> = {};

  if (updates.displayName !== undefined) payload.displayName = updates.displayName;
  if (updates.conditions !== undefined) payload.conditions = updates.conditions;
  if (updates.enabled !== undefined) payload.enabled = updates.enabled;
  if (updates.notificationChannels !== undefined) {
    payload.notificationChannels = updates.notificationChannels;
  }
  if (updates.documentation !== undefined) {
    payload.documentation = { content: updates.documentation, mimeType: 'text/markdown' };
  }

  const response = await apiClient.patch<AlertPolicy>(
    `/v3/projects/${proj}/alertPolicies/${policyId}`,
    payload
  );
  return response.data;
}

/**
 * Delete an alert policy
 */
export async function deleteAlertPolicy(
  policyId: string,
  project?: string
): Promise<void> {
  const proj = project || getCurrentProject();
  await apiClient.delete(`/v3/projects/${proj}/alertPolicies/${policyId}`);
}

// ============================================================================
// NOTIFICATION CHANNELS
// ============================================================================

/**
 * List notification channels
 */
export async function listNotificationChannels(
  project?: string
): Promise<NotificationChannel[]> {
  const proj = project || getCurrentProject();
  const response = await apiClient.get<{ notificationChannels?: NotificationChannel[] }>(
    `/v3/projects/${proj}/notificationChannels`
  );
  return response.data.notificationChannels ?? [];
}

/**
 * Get a specific notification channel
 */
export async function getNotificationChannel(
  channelId: string,
  project?: string
): Promise<NotificationChannel> {
  const proj = project || getCurrentProject();
  const response = await apiClient.get<NotificationChannel>(
    `/v3/projects/${proj}/notificationChannels/${channelId}`
  );
  return response.data;
}

/**
 * Create a notification channel
 */
export async function createNotificationChannel(
  type: string,
  displayName: string,
  labels?: Record<string, string>,
  description?: string,
  project?: string
): Promise<NotificationChannel> {
  const proj = project || getCurrentProject();
  const response = await apiClient.post<NotificationChannel>(
    `/v3/projects/${proj}/notificationChannels`,
    {
      type,
      displayName,
      description: description || '',
      labels: labels || {},
      userLabels: {},
      enabled: true,
    }
  );
  return response.data;
}

/**
 * Update a notification channel
 */
export async function updateNotificationChannel(
  channelId: string,
  updates: {
    displayName?: string;
    labels?: Record<string, string>;
    enabled?: boolean;
  },
  project?: string
): Promise<NotificationChannel> {
  const proj = project || getCurrentProject();
  const response = await apiClient.patch<NotificationChannel>(
    `/v3/projects/${proj}/notificationChannels/${channelId}`,
    updates
  );
  return response.data;
}

/**
 * Delete a notification channel
 */
export async function deleteNotificationChannel(
  channelId: string,
  project?: string
): Promise<void> {
  const proj = project || getCurrentProject();
  await apiClient.delete(`/v3/projects/${proj}/notificationChannels/${channelId}`);
}
