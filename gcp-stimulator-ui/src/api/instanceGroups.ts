import { apiClient, getCurrentProject } from './client';

export interface NamedPort {
  name: string;
  port: number;
}

export interface InstanceGroupItem {
  kind: string;
  id: string;
  name: string;
  description?: string;
  status: string;
  size: number;
  namedPorts?: NamedPort[];
  creationTimestamp?: string;
}

export interface GroupMember {
  instance: string;
  status: string;
}

/**
 * List instance groups in a zone
 */
export async function listInstanceGroups(
  zone: string,
  project?: string
): Promise<InstanceGroupItem[]> {
  const proj = project || getCurrentProject();
  try {
    const response = await apiClient.get<{
      items?: InstanceGroupItem[];
    }>(
      `/compute/v1/projects/${proj}/zones/${zone}/instanceGroups`
    );
    return response.data.items ?? [];
  } catch {
    return [];
  }
}

/**
 * Create a new instance group
 */
export async function createInstanceGroup(
  zone: string,
  name: string,
  description?: string,
  namedPorts?: NamedPort[],
  project?: string
): Promise<InstanceGroupItem> {
  const proj = project || getCurrentProject();
  const response = await apiClient.post<InstanceGroupItem>(
    `/compute/v1/projects/${proj}/zones/${zone}/instanceGroups`,
    {
      name,
      description,
      namedPorts,
    }
  );
  return response.data;
}

/**
 * Get a specific instance group
 */
export async function getInstanceGroup(
  zone: string,
  groupName: string,
  project?: string
): Promise<InstanceGroupItem> {
  const proj = project || getCurrentProject();
  const response = await apiClient.get<InstanceGroupItem>(
    `/compute/v1/projects/${proj}/zones/${zone}/instanceGroups/${groupName}`
  );
  return response.data;
}

/**
 * Delete an instance group
 */
export async function deleteInstanceGroup(
  zone: string,
  groupName: string,
  project?: string
): Promise<void> {
  const proj = project || getCurrentProject();
  await apiClient.delete(
    `/compute/v1/projects/${proj}/zones/${zone}/instanceGroups/${groupName}`
  );
}

/**
 * Add instances to an instance group
 */
export async function addInstancesToGroup(
  zone: string,
  groupName: string,
  instanceNames: string[],
  project?: string
): Promise<void> {
  const proj = project || getCurrentProject();
  const instances = instanceNames.map((name) => ({
    instance: `projects/${proj}/zones/${zone}/instances/${name}`,
  }));
  
  await apiClient.post(
    `/compute/v1/projects/${proj}/zones/${zone}/instanceGroups/${groupName}/addInstances`,
    { instances }
  );
}

/**
 * Remove instances from an instance group
 */
export async function removeInstancesFromGroup(
  zone: string,
  groupName: string,
  instanceNames: string[],
  project?: string
): Promise<void> {
  const proj = project || getCurrentProject();
  const instances = instanceNames.map((name) => ({
    instance: `projects/${proj}/zones/${zone}/instances/${name}`,
  }));
  
  await apiClient.post(
    `/compute/v1/projects/${proj}/zones/${zone}/instanceGroups/${groupName}/removeInstances`,
    { instances }
  );
}

/**
 * List instances in an instance group
 */
export async function listGroupMembers(
  zone: string,
  groupName: string,
  project?: string
): Promise<GroupMember[]> {
  const proj = project || getCurrentProject();
  const response = await apiClient.get<{
    items?: GroupMember[];
  }>(
    `/compute/v1/projects/${proj}/zones/${zone}/instanceGroups/${groupName}/listInstances`
  );
  return response.data.items ?? [];
}
