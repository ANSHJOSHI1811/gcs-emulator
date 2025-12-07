import { apiClient, PROJECT_ID } from './client';
import { ComputeInstance, ComputeInstanceCreate, MachineType } from '@/types/compute';

// Backend response types (matching Flask API)
interface BackendInstance {
  id: string;
  name: string;
  project_id: string;
  zone: string;
  machineType: string;
  status: string;
  status_message?: string;
  container_id?: string;
  creationTimestamp: string;
  last_start_timestamp?: string;
  last_stop_timestamp?: string;
  metadata?: Record<string, string>;
  labels?: Record<string, string>;
  tags?: string[];
  networkInterfaces?: any[];
  disks?: any[];
}

interface BackendInstanceListResponse {
  kind: string;
  items?: BackendInstance[];
}

interface BackendMachineType {
  name: string;
  description: string;
  guestCpus: number;
  memoryMb: number;
  zone: string;
}

interface BackendMachineTypeListResponse {
  kind: string;
  items?: BackendMachineType[];
}

// Transform backend instance to frontend format
function transformInstance(item: BackendInstance): ComputeInstance {
  return {
    id: item.id,
    name: item.name,
    projectId: item.project_id,
    zone: item.zone,
    machineType: item.machineType.split('/').pop() || item.machineType,
    status: item.status as ComputeInstance['status'],
    statusMessage: item.status_message,
    containerId: item.container_id,
    creationTimestamp: item.creationTimestamp,
    lastStartTimestamp: item.last_start_timestamp,
    lastStopTimestamp: item.last_stop_timestamp,
    metadata: item.metadata,
    labels: item.labels,
    tags: item.tags,
    networkInterfaces: item.networkInterfaces,
    disks: item.disks,
  };
}

// List instances in a zone
export async function fetchInstances(zone: string = 'us-central1-a'): Promise<ComputeInstance[]> {
  const response = await apiClient.get<BackendInstanceListResponse>(
    `/compute/v1/projects/${PROJECT_ID}/zones/${zone}/instances`
  );
  if (!response.data.items) {
    return [];
  }
  return response.data.items.map(transformInstance);
}

// Get single instance
export async function fetchInstance(zone: string, name: string): Promise<ComputeInstance> {
  const response = await apiClient.get<BackendInstance>(
    `/compute/v1/projects/${PROJECT_ID}/zones/${zone}/instances/${name}`
  );
  return transformInstance(response.data);
}

// Create instance
export async function createInstance(
  zone: string,
  data: ComputeInstanceCreate
): Promise<ComputeInstance> {
  const payload = {
    name: data.name,
    machineType: `zones/${zone}/machineTypes/${data.machineType}`,
    metadata: data.metadata ? {
      items: Object.entries(data.metadata).map(([key, value]) => ({ key, value }))
    } : undefined,
    labels: data.labels,
    tags: data.tags ? { items: data.tags } : undefined,
  };

  const response = await apiClient.post<{ targetLink: string }>(
    `/compute/v1/projects/${PROJECT_ID}/zones/${zone}/instances`,
    payload
  );

  // After creation, fetch the instance details
  const instanceName = response.data.targetLink?.split('/').pop() || data.name;
  return fetchInstance(zone, instanceName);
}

// Start instance
export async function startInstance(zone: string, name: string): Promise<void> {
  await apiClient.post(
    `/compute/v1/projects/${PROJECT_ID}/zones/${zone}/instances/${name}/start`
  );
}

// Stop instance
export async function stopInstance(zone: string, name: string): Promise<void> {
  await apiClient.post(
    `/compute/v1/projects/${PROJECT_ID}/zones/${zone}/instances/${name}/stop`
  );
}

// Delete instance
export async function deleteInstance(zone: string, name: string): Promise<void> {
  await apiClient.delete(
    `/compute/v1/projects/${PROJECT_ID}/zones/${zone}/instances/${name}`
  );
}

// List machine types
export async function fetchMachineTypes(zone: string = 'us-central1-a'): Promise<MachineType[]> {
  const response = await apiClient.get<BackendMachineTypeListResponse>(
    `/compute/v1/projects/${PROJECT_ID}/zones/${zone}/machineTypes`
  );
  if (!response.data.items) {
    return [];
  }
  return response.data.items;
}

// Static zone list (commonly used zones)
export const ZONES = [
  { value: 'us-central1-a', label: 'us-central1-a (Iowa)' },
  { value: 'us-central1-b', label: 'us-central1-b (Iowa)' },
  { value: 'us-central1-c', label: 'us-central1-c (Iowa)' },
  { value: 'us-central1-f', label: 'us-central1-f (Iowa)' },
  { value: 'us-east1-b', label: 'us-east1-b (South Carolina)' },
  { value: 'us-east1-c', label: 'us-east1-c (South Carolina)' },
  { value: 'us-east1-d', label: 'us-east1-d (South Carolina)' },
  { value: 'us-west1-a', label: 'us-west1-a (Oregon)' },
  { value: 'us-west1-b', label: 'us-west1-b (Oregon)' },
  { value: 'us-west1-c', label: 'us-west1-c (Oregon)' },
  { value: 'europe-west1-b', label: 'europe-west1-b (Belgium)' },
  { value: 'europe-west1-c', label: 'europe-west1-c (Belgium)' },
  { value: 'europe-west1-d', label: 'europe-west1-d (Belgium)' },
  { value: 'asia-east1-a', label: 'asia-east1-a (Taiwan)' },
  { value: 'asia-east1-b', label: 'asia-east1-b (Taiwan)' },
  { value: 'asia-east1-c', label: 'asia-east1-c (Taiwan)' },
];
