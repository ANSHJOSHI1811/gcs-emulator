import apiClient from './client';

export interface Network {
  id: string;
  name: string;
  description?: string;
  autoCreateSubnetworks: boolean;
  IPv4Range?: string;
  creationTimestamp: string;
  selfLink: string;
}

export interface Subnet {
  id: string;
  name: string;
  network: string;
  region: string;
  ipCidrRange: string;
  gatewayAddress: string;
  creationTimestamp: string;
  selfLink: string;
}

export interface CreateNetworkRequest {
  name: string;
  autoCreateSubnetworks?: boolean;
  IPv4Range?: string;
  description?: string;
}

export interface CreateSubnetRequest {
  name: string;
  network: string;
  region: string;
  ipCidrRange: string;
}

export interface NetworkStats {
  totalNetworks: number;
  totalSubnets: number;
  totalInstances: number;
  ipUtilization: {
    network: string;
    subnet: string;
    totalIps: number;
    usedIps: number;
    availableIps: number;
  }[];
}

// Network Operations
export const listNetworks = async (project: string): Promise<Network[]> => {
  const response = await apiClient.get(
    `/compute/v1/projects/${project}/global/networks`
  );
  return response.data.items || [];
};

export const getNetwork = async (project: string, network: string): Promise<Network> => {
  const response = await apiClient.get(
    `/compute/v1/projects/${project}/global/networks/${network}`
  );
  return response.data;
};

export const createNetwork = async (
  project: string,
  data: CreateNetworkRequest
): Promise<Network> => {
  const response = await apiClient.post(
    `/compute/v1/projects/${project}/global/networks`,
    data
  );
  return response.data;
};

export const deleteNetwork = async (
  project: string,
  network: string
): Promise<void> => {
  await apiClient.delete(
    `/compute/v1/projects/${project}/global/networks/${network}`
  );
};

// Subnet Operations
export const listSubnets = async (
  project: string,
  region?: string
): Promise<Subnet[]> => {
  const url = region
    ? `/compute/v1/projects/${project}/regions/${region}/subnetworks`
    : `/compute/v1/projects/${project}/aggregated/subnetworks`;
  
  const response = await apiClient.get(url);
  
  if (region) {
    return response.data.items || [];
  } else {
    // Aggregated response format
    const items: Subnet[] = [];
    Object.values(response.data.items || {}).forEach((regionData: any) => {
      if (regionData.subnetworks) {
        items.push(...regionData.subnetworks);
      }
    });
    return items;
  }
};

export const getSubnet = async (
  project: string,
  region: string,
  subnet: string
): Promise<Subnet> => {
  const response = await apiClient.get(
    `/compute/v1/projects/${project}/regions/${region}/subnetworks/${subnet}`
  );
  return response.data;
};

export const createSubnet = async (
  project: string,
  region: string,
  data: CreateSubnetRequest
): Promise<Subnet> => {
  const response = await apiClient.post(
    `/compute/v1/projects/${project}/regions/${region}/subnetworks`,
    data
  );
  return response.data;
};

export const deleteSubnet = async (
  project: string,
  region: string,
  subnet: string
): Promise<void> => {
  await apiClient.delete(
    `/compute/v1/projects/${project}/regions/${region}/subnetworks/${subnet}`
  );
};

// Network Statistics
export const getNetworkStats = async (project: string): Promise<NetworkStats> => {
  const response = await apiClient.get(
    `/compute/v1/projects/${project}/network-stats`
  );
  return response.data;
};
