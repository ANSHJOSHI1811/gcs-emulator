import { apiClient, getCurrentProject } from './client';

export interface Topic {
  name: string;
  labels?: Record<string, string>;
  messageRetentionDuration?: string;
  kmsKeyName?: string;
}

export interface PushConfig {
  pushEndpoint: string;
  attributes?: Record<string, string>;
}

export interface Subscription {
  name: string;
  topic: string;
  labels?: Record<string, string>;
  deliveryType: 'PULL' | 'PUSH';
  pushConfig?: PushConfig;
  ackDeadlineSeconds: number;
  messageRetentionDuration?: string;
  enableMessageOrdering?: boolean;
  filter?: string;
}

export interface PubsubMessage {
  data: string;
  attributes?: Record<string, string>;
  messageId?: string;
  publishTime?: string;
}

export interface PullResponseMessage {
  ackId: string;
  message: PubsubMessage;
}

// ============================================================================
// TOPICS
// ============================================================================

export async function listTopics(project?: string): Promise<Topic[]> {
  const proj = project || getCurrentProject();
  const response = await apiClient.get<{ topics?: Topic[] }>(
    `/v1/projects/${proj}/topics`
  );
  return response.data.topics || [];
}

export async function getTopic(topicName: string): Promise<Topic> {
  const response = await apiClient.get<Topic>(`/v1/${topicName}`);
  return response.data;
}

export async function createTopic(
  topicId: string,
  labels?: Record<string, string>,
  project?: string
): Promise<Topic> {
  const proj = project || getCurrentProject();
  const response = await apiClient.post<Topic>(
    `/v1/projects/${proj}/topics`,
    {
      name: `projects/${proj}/topics/${topicId}`,
      labels: labels || {},
    }
  );
  return response.data;
}

export async function deleteTopic(topicName: string): Promise<void> {
  await apiClient.delete(`/v1/${topicName}`);
}

// ============================================================================
// SUBSCRIPTIONS
// ============================================================================

export async function listSubscriptions(
  topicFilter?: string,
  project?: string
): Promise<Subscription[]> {
  const proj = project || getCurrentProject();
  const params = topicFilter ? `?topic=${topicFilter}` : '';
  const response = await apiClient.get<{ subscriptions?: Subscription[] }>(
    `/v1/projects/${proj}/subscriptions${params}`
  );
  return response.data.subscriptions || [];
}

export async function getSubscription(subscriptionName: string): Promise<Subscription> {
  const response = await apiClient.get<Subscription>(`/v1/${subscriptionName}`);
  return response.data;
}

export async function createSubscription(payload: {
  subscriptionId: string;
  topic: string;
  labels?: Record<string, string>;
  deliveryType?: 'PULL' | 'PUSH';
  pushConfig?: PushConfig;
  ackDeadlineSeconds?: number;
  project?: string;
}): Promise<Subscription> {
  const proj = payload.project || getCurrentProject();
  const response = await apiClient.post<Subscription>(
    `/v1/projects/${proj}/subscriptions`,
    {
      name: `projects/${proj}/subscriptions/${payload.subscriptionId}`,
      topic: payload.topic,
      labels: payload.labels || {},
      deliveryType: payload.deliveryType || 'PULL',
      pushConfig: payload.pushConfig,
      ackDeadlineSeconds: payload.ackDeadlineSeconds || 60,
    }
  );
  return response.data;
}

export async function deleteSubscription(subscriptionName: string): Promise<void> {
  await apiClient.delete(`/v1/${subscriptionName}`);
}

// ============================================================================
// MESSAGING
// ============================================================================

export async function publishMessage(
  topic: string,
  messages: Array<{ data: string; attributes?: Record<string, string> }>
): Promise<string[]> {
  const response = await apiClient.post<{ messageIds: string[] }>(
    `/v1/${topic}:publish`,
    { messages }
  );
  return response.data.messageIds || [];
}

export async function pullMessages(
  subscription: string,
  maxMessages: number = 10,
  returnImmediately: boolean = true
): Promise<PullResponseMessage[]> {
  const response = await apiClient.post<{ receivedMessages?: PullResponseMessage[] }>(
    `/v1/${subscription}:pull`,
    {
      maxMessages,
      returnImmediately,
    }
  );
  return response.data.receivedMessages || [];
}

export async function acknowledgeMessages(
  subscription: string,
  ackIds: string[]
): Promise<void> {
  await apiClient.post(`/v1/${subscription}:acknowledge`, { ackIds });
}

export async function nackMessages(
  subscription: string,
  ackIds: string[]
): Promise<void> {
  await apiClient.post(`/v1/${subscription}:nack`, { ackIds });
}
