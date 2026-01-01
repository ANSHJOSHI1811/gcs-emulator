import { apiClient } from './client';

// ============================================================================
// Types
// ============================================================================

export interface ComputeInstance {
  id: string;
  name: string;
  image: string;
  cpu: number;
  memory_mb: number;
  container_id: string | null;
  state: 'pending' | 'running' | 'stopping' | 'stopped' | 'terminated';
  created_at: string;
  updated_at: string;
}

export interface CreateInstanceRequest {
  name: string;
  image: string;
  cpu?: number;
  memory?: number;
}

export interface ListInstancesResponse {
  count: number;
  instances: ComputeInstance[];
}

// ============================================================================
// API Functions
// ============================================================================

export async function listInstances(
  instanceIds?: string[],
  states?: string[]
): Promise<ComputeInstance[]> {
  const params = new URLSearchParams();
  if (instanceIds && instanceIds.length > 0) {
    params.append('instance_ids', instanceIds.join(','));
  }
  if (states && states.length > 0) {
    params.append('states', states.join(','));
  }

  const response = await apiClient.get<ListInstancesResponse>(
    `/compute/instances?${params.toString()}`
  );
  return response.data.instances || [];
}

export async function getInstance(instanceId: string): Promise<ComputeInstance> {
  const response = await apiClient.get<ComputeInstance>(`/compute/instances/${instanceId}`);
  return response.data;
}

export async function createInstance(request: CreateInstanceRequest): Promise<ComputeInstance> {
  const response = await apiClient.post<ComputeInstance>('/compute/instances', request);
  return response.data;
}

export async function stopInstance(instanceId: string): Promise<void> {
  await apiClient.post(`/compute/instances/${instanceId}/stop`);
}

export async function startInstance(instanceId: string): Promise<void> {
  await apiClient.post(`/compute/instances/${instanceId}/start`);
}

export async function terminateInstance(instanceId: string): Promise<void> {
  await apiClient.post(`/compute/instances/${instanceId}/terminate`);
}

// ============================================================================
// Helper Functions
// ============================================================================

export function getStateColor(state: ComputeInstance['state']): string {
  switch (state) {
    case 'running':
      return 'text-green-600 bg-green-50';
    case 'stopped':
      return 'text-gray-600 bg-gray-50';
    case 'pending':
      return 'text-yellow-600 bg-yellow-50';
    case 'stopping':
      return 'text-orange-600 bg-orange-50';
    case 'terminated':
      return 'text-red-600 bg-red-50';
    default:
      return 'text-gray-600 bg-gray-50';
  }
}

export function getStateIcon(state: ComputeInstance['state']): string {
  switch (state) {
    case 'running':
      return '●';
    case 'stopped':
      return '■';
    case 'pending':
      return '◐';
    case 'stopping':
      return '◑';
    case 'terminated':
      return '✕';
    default:
      return '○';
  }
}
