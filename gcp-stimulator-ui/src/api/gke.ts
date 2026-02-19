import { apiClient, getCurrentProject } from './client';

// ─── Interfaces ───────────────────────────────────────────────────────────────

export interface GKECluster {
  name: string;
  description: string;
  status: 'PROVISIONING' | 'RUNNING' | 'RECONCILING' | 'STOPPING' | 'STOPPED' | 'ERROR';
  location: string;
  masterVersion: string;
  currentMasterVersion: string;
  currentNodeVersion: string;
  endpoint: string;
  currentNodeCount: number;
  initialNodeCount: number;
  network: string;
  subnetwork: string;
  nodeConfig: {
    machineType: string;
    diskSizeGb: number;
    imageType?: string;
    preemptible?: boolean;
    spot?: boolean;
  };
  clusterType: 'STANDARD' | 'AUTOPILOT';
  autopilot: { enabled: boolean };
  releaseChannel: { channel: 'RAPID' | 'REGULAR' | 'STABLE' | 'NONE' };
  loggingService: string;
  monitoringService: string;
  binaryAuthorization: { evaluationMode: string };
  masterAuth: { clusterCaCertificate: string };
  clusterIpv4Cidr: string;
  servicesIpv4Cidr: string;
  privateClusterConfig: {
    enablePrivateNodes: boolean;
    enablePrivateEndpoint: boolean;
  };
  addonsConfig: {
    httpLoadBalancing?: { disabled: boolean };
    horizontalPodAutoscaling?: { disabled: boolean };
    networkPolicyConfig?: { disabled: boolean };
  };
  resourceLabels: Record<string, string>;
  selfLink: string;
  createTime: string;
  updateTime?: string;
}

export interface GKENodePool {
  name: string;
  status: string;
  clusterName: string;
  location: string;
  nodeCount: number;
  config: {
    machineType: string;
    diskSizeGb: number;
    imageType?: string;
    preemptible?: boolean;
    spot?: boolean;
  };
  autoscaling: {
    enabled: boolean;
    minNodeCount: number;
    maxNodeCount: number;
  };
  management: {
    autoRepair: boolean;
    autoUpgrade: boolean;
  };
  selfLink: string;
  createTime: string;
}

export interface GKEAddon {
  name: string;
  status: 'ENABLED' | 'DISABLED';
  version: string;
  clusterName: string;
  createTime: string;
  updateTime?: string;
}

export interface GKENode {
  name: string;
  status: 'Ready' | 'NotReady';
  roles: string;
  age: string;
  version: string;
  internalIP: string;
  osImage: string;
  containerRuntime: string;
}

export interface ServerConfig {
  defaultClusterVersion: string;
  validMasterVersions: string[];
  validNodeVersions: string[];
  channels: { channel: string; defaultVersion: string; validVersions: string[] }[];
}

export interface CreateClusterPayload {
  name: string;
  description?: string;
  masterVersion?: string;
  initialNodeCount?: number;
  nodeConfig?: {
    machineType?: string;
    diskSizeGb?: number;
    preemptible?: boolean;
    spot?: boolean;
  };
  network?: string;
  subnetwork?: string;
  clusterType?: 'STANDARD' | 'AUTOPILOT';
  autopilot?: { enabled: boolean };
  releaseChannel?: { channel: string };
  clusterIpv4Cidr?: string;
  servicesIpv4Cidr?: string;
  privateClusterConfig?: { enablePrivateNodes?: boolean };
  loggingService?: string;
  monitoringService?: string;
  resourceLabels?: Record<string, string>;
  nodePools?: { name: string }[];
}

export interface CreateNodePoolPayload {
  name: string;
  initialNodeCount?: number;
  config?: {
    machineType?: string;
    diskSizeGb?: number;
    imageType?: string;
    preemptible?: boolean;
    spot?: boolean;
  };
  autoscaling?: {
    enabled?: boolean;
    minNodeCount?: number;
    maxNodeCount?: number;
  };
  management?: {
    autoRepair?: boolean;
    autoUpgrade?: boolean;
  };
}

// ─── Server Config ────────────────────────────────────────────────────────────

export async function getServerConfig(location: string): Promise<ServerConfig> {
  const project = getCurrentProject();
  const res = await apiClient.get<ServerConfig>(
    `/container/v1/projects/${project}/locations/${location}/serverConfig`
  );
  return res.data;
}

// ─── Cluster API ──────────────────────────────────────────────────────────────

export async function listClusters(location = '-', project?: string): Promise<GKECluster[]> {
  const proj = project || getCurrentProject();
  const res = await apiClient.get<{ clusters?: GKECluster[] }>(
    `/container/v1/projects/${proj}/locations/${location}/clusters`
  );
  return res.data.clusters ?? [];
}

export async function createCluster(
  location: string,
  payload: CreateClusterPayload
): Promise<void> {
  const project = getCurrentProject();
  await apiClient.post(
    `/container/v1/projects/${project}/locations/${location}/clusters`,
    { cluster: payload }
  );
}

export async function getCluster(location: string, clusterName: string): Promise<GKECluster> {
  const project = getCurrentProject();
  const res = await apiClient.get<GKECluster>(
    `/container/v1/projects/${project}/locations/${location}/clusters/${clusterName}`
  );
  return res.data;
}

export async function deleteCluster(location: string, clusterName: string): Promise<void> {
  const project = getCurrentProject();
  await apiClient.delete(
    `/container/v1/projects/${project}/locations/${location}/clusters/${clusterName}`
  );
}

export async function stopCluster(location: string, clusterName: string): Promise<void> {
  const project = getCurrentProject();
  await apiClient.post(
    `/container/v1/projects/${project}/locations/${location}/clusters/${clusterName}:stop`,
    {}
  );
}

export async function startCluster(location: string, clusterName: string): Promise<void> {
  const project = getCurrentProject();
  await apiClient.post(
    `/container/v1/projects/${project}/locations/${location}/clusters/${clusterName}:start`,
    {}
  );
}

export async function updateCluster(
  location: string,
  clusterName: string,
  update: Record<string, unknown>
): Promise<void> {
  const project = getCurrentProject();
  await apiClient.patch(
    `/container/v1/projects/${project}/locations/${location}/clusters/${clusterName}`,
    { update }
  );
}

export async function getKubeconfig(location: string, clusterName: string): Promise<string> {
  const project = getCurrentProject();
  const res = await apiClient.get<{ kubeconfig: string }>(
    `/container/v1/projects/${project}/locations/${location}/clusters/${clusterName}/kubeconfig`
  );
  return res.data.kubeconfig;
}

export async function execKubectl(
  location: string,
  clusterName: string,
  command: string
): Promise<{ stdout: string; stderr: string; returnCode: number }> {
  const project = getCurrentProject();
  const res = await apiClient.post<{ stdout: string; stderr: string; returnCode: number }>(
    `/container/v1/projects/${project}/locations/${location}/clusters/${clusterName}/kubectl`,
    { command }
  );
  return res.data;
}

// ─── Node Pool API ────────────────────────────────────────────────────────────

export async function listNodePools(location: string, clusterName: string): Promise<GKENodePool[]> {
  const project = getCurrentProject();
  const res = await apiClient.get<{ nodePools?: GKENodePool[] }>(
    `/container/v1/projects/${project}/locations/${location}/clusters/${clusterName}/nodePools`
  );
  return res.data.nodePools ?? [];
}

export async function createNodePool(
  location: string,
  clusterName: string,
  payload: CreateNodePoolPayload
): Promise<void> {
  const project = getCurrentProject();
  await apiClient.post(
    `/container/v1/projects/${project}/locations/${location}/clusters/${clusterName}/nodePools`,
    { nodePool: payload }
  );
}

export async function getNodePool(
  location: string,
  clusterName: string,
  poolName: string
): Promise<GKENodePool> {
  const project = getCurrentProject();
  const res = await apiClient.get<GKENodePool>(
    `/container/v1/projects/${project}/locations/${location}/clusters/${clusterName}/nodePools/${poolName}`
  );
  return res.data;
}

export async function setNodePoolAutoscaling(
  location: string,
  clusterName: string,
  poolName: string,
  autoscaling: { enabled: boolean; minNodeCount?: number; maxNodeCount?: number }
): Promise<GKENodePool> {
  const project = getCurrentProject();
  const res = await apiClient.post<GKENodePool>(
    `/container/v1/projects/${project}/locations/${location}/clusters/${clusterName}/nodePools/${poolName}:setAutoscaling`,
    { autoscaling }
  );
  return res.data;
}

export async function deleteNodePool(
  location: string,
  clusterName: string,
  poolName: string
): Promise<void> {
  const project = getCurrentProject();
  await apiClient.delete(
    `/container/v1/projects/${project}/locations/${location}/clusters/${clusterName}/nodePools/${poolName}`
  );
}

export async function setNodePoolSize(
  location: string,
  clusterName: string,
  poolName: string,
  nodeCount: number
): Promise<void> {
  const project = getCurrentProject();
  await apiClient.post(
    `/container/v1/projects/${project}/locations/${location}/clusters/${clusterName}/nodePools/${poolName}:setSize`,
    { nodeCount }
  );
}

// ─── Nodes API ────────────────────────────────────────────────────────────────

export async function listNodes(
  location: string,
  clusterName: string
): Promise<{ nodes: GKENode[]; error?: string }> {
  const project = getCurrentProject();
  const res = await apiClient.get<{ nodes: GKENode[]; error?: string }>(
    `/container/v1/projects/${project}/locations/${location}/clusters/${clusterName}/nodes`
  );
  return res.data;
}

// ─── Addon API ────────────────────────────────────────────────────────────────

export async function listAddons(location: string, clusterName: string): Promise<GKEAddon[]> {
  const project = getCurrentProject();
  const res = await apiClient.get<{ addons?: GKEAddon[] }>(
    `/container/v1/projects/${project}/locations/${location}/clusters/${clusterName}/addons`
  );
  return res.data.addons ?? [];
}

export async function createAddon(
  location: string,
  clusterName: string,
  name: string,
  version?: string
): Promise<GKEAddon> {
  const project = getCurrentProject();
  const res = await apiClient.post<GKEAddon>(
    `/container/v1/projects/${project}/locations/${location}/clusters/${clusterName}/addons`,
    { name, version }
  );
  return res.data;
}

export async function deleteAddon(
  location: string,
  clusterName: string,
  addonName: string
): Promise<void> {
  const project = getCurrentProject();
  await apiClient.delete(
    `/container/v1/projects/${project}/locations/${location}/clusters/${clusterName}/addons/${addonName}`
  );
}
