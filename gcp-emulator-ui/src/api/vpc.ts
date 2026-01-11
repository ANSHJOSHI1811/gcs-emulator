/**
 * VPC API Client
 * Interfaces with backend VPC endpoints (Phase 1: Control plane only)
 */

const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8080';

export interface Network {
  id: string;
  name: string;
  description: string;
  selfLink: string;
  autoCreateSubnetworks: boolean;
  subnetworks: string[];
  routingConfig: {
    routingMode: 'REGIONAL' | 'GLOBAL';
  };
  mtu: number;
  kind: string;
  creationTimestamp: string;
}

export interface Subnetwork {
  id: string;
  name: string;
  description: string;
  selfLink: string;
  network: string;
  ipCidrRange: string;
  gatewayAddress: string;
  region: string;
  privateIpGoogleAccess: boolean;
  kind: string;
  creationTimestamp: string;
}

export interface NetworksListResponse {
  kind: string;
  id: string;
  items: Network[];
  selfLink: string;
}

export interface SubnetworksListResponse {
  kind: string;
  id: string;
  items: Subnetwork[];
  selfLink: string;
}

/**
 * List all VPC networks in a project
 */
export const listNetworks = async (projectId: string = 'test-project'): Promise<Network[]> => {
  const response = await fetch(
    `${API_BASE_URL}/compute/v1/projects/${projectId}/global/networks`
  );
  
  if (!response.ok) {
    throw new Error(`Failed to list networks: ${response.statusText}`);
  }
  
  const data: NetworksListResponse = await response.json();
  return data.items || [];
};

/**
 * Get a specific VPC network
 */
export const getNetwork = async (
  projectId: string = 'test-project',
  networkName: string
): Promise<Network> => {
  const response = await fetch(
    `${API_BASE_URL}/compute/v1/projects/${projectId}/global/networks/${networkName}`
  );
  
  if (!response.ok) {
    throw new Error(`Failed to get network: ${response.statusText}`);
  }
  
  return response.json();
};

/**
 * List subnetworks in a region
 */
export const listSubnetworks = async (
  projectId: string = 'test-project',
  region: string
): Promise<Subnetwork[]> => {
  const response = await fetch(
    `${API_BASE_URL}/compute/v1/projects/${projectId}/regions/${region}/subnetworks`
  );
  
  if (!response.ok) {
    throw new Error(`Failed to list subnetworks: ${response.statusText}`);
  }
  
  const data: SubnetworksListResponse = await response.json();
  return data.items || [];
};

/**
 * List all subnetworks across all regions for a project
 * Helper function to aggregate subnets from all regions
 */
export const listAllSubnetworks = async (
  projectId: string = 'test-project'
): Promise<Subnetwork[]> => {
  // Common GCP regions
  const regions = [
    'us-central1',
    'us-east1',
    'us-west1',
    'europe-west1',
    'asia-east1'
  ];
  
  const allSubnets: Subnetwork[] = [];
  
  for (const region of regions) {
    try {
      const subnets = await listSubnetworks(projectId, region);
      allSubnets.push(...subnets);
    } catch (error) {
      // Region might not have subnets, continue
      console.debug(`No subnets in region ${region}`);
    }
  }
  
  return allSubnets;
};

/**
 * Get a specific subnetwork
 */
export const getSubnetwork = async (
  projectId: string = 'test-project',
  region: string,
  subnetworkName: string
): Promise<Subnetwork> => {
  const response = await fetch(
    `${API_BASE_URL}/compute/v1/projects/${projectId}/regions/${region}/subnetworks/${subnetworkName}`
  );
  
  if (!response.ok) {
    throw new Error(`Failed to get subnetwork: ${response.statusText}`);
  }
  
  return response.json();
};
