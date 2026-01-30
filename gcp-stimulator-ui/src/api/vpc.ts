import apiClient from './client';

export const vpcApi = {
  // Networks
  listNetworks: (project: string) =>
    apiClient.get(`/compute/v1/projects/${project}/global/networks`),
  
  getNetwork: (project: string, network: string) =>
    apiClient.get(`/compute/v1/projects/${project}/global/networks/${network}`),
  
  createNetwork: (project: string, data: any) =>
    apiClient.post(`/compute/v1/projects/${project}/global/networks`, data),
  
  deleteNetwork: (project: string, network: string) =>
    apiClient.delete(`/compute/v1/projects/${project}/global/networks/${network}`),
  
  patchNetwork: (project: string, network: string, data: any) =>
    apiClient.patch(`/compute/v1/projects/${project}/global/networks/${network}`, data),
  
  // Subnets
  listSubnets: (project: string, region: string) =>
    apiClient.get(`/compute/v1/projects/${project}/regions/${region}/subnetworks`),
  
  aggregatedListSubnets: (project: string) =>
    apiClient.get(`/compute/v1/projects/${project}/aggregated/subnetworks`),
  
  getSubnet: (project: string, region: string, subnet: string) =>
    apiClient.get(`/compute/v1/projects/${project}/regions/${region}/subnetworks/${subnet}`),
  
  createSubnet: (project: string, region: string, data: any) =>
    apiClient.post(`/compute/v1/projects/${project}/regions/${region}/subnetworks`, data),
  
  deleteSubnet: (project: string, region: string, subnet: string) =>
    apiClient.delete(`/compute/v1/projects/${project}/regions/${region}/subnetworks/${subnet}`),
  
  patchSubnet: (project: string, region: string, subnet: string, data: any) =>
    apiClient.patch(`/compute/v1/projects/${project}/regions/${region}/subnetworks/${subnet}`, data),
  
  // Firewalls
  listFirewalls: (project: string) =>
    apiClient.get(`/compute/v1/projects/${project}/global/firewalls`),
  
  getFirewall: (project: string, firewall: string) =>
    apiClient.get(`/compute/v1/projects/${project}/global/firewalls/${firewall}`),
  
  createFirewall: (project: string, data: any) =>
    apiClient.post(`/compute/v1/projects/${project}/global/firewalls`, data),
  
  deleteFirewall: (project: string, firewall: string) =>
    apiClient.delete(`/compute/v1/projects/${project}/global/firewalls/${firewall}`),
  
  patchFirewall: (project: string, firewall: string, data: any) =>
    apiClient.patch(`/compute/v1/projects/${project}/global/firewalls/${firewall}`, data),
  
  // Routes
  listRoutes: (project: string) =>
    apiClient.get(`/compute/v1/projects/${project}/global/routes`),
  
  getRoute: (project: string, route: string) =>
    apiClient.get(`/compute/v1/projects/${project}/global/routes/${route}`),
  
  createRoute: (project: string, data: any) =>
    apiClient.post(`/compute/v1/projects/${project}/global/routes`, data),
  
  deleteRoute: (project: string, route: string) =>
    apiClient.delete(`/compute/v1/projects/${project}/global/routes/${route}`),
  
  // Routers
  listRouters: (project: string, region: string) =>
    apiClient.get(`/compute/v1/projects/${project}/regions/${region}/routers`),
  
  getRouter: (project: string, region: string, router: string) =>
    apiClient.get(`/compute/v1/projects/${project}/regions/${region}/routers/${router}`),
  
  createRouter: (project: string, region: string, data: any) =>
    apiClient.post(`/compute/v1/projects/${project}/regions/${region}/routers`, data),
  
  deleteRouter: (project: string, region: string, router: string) =>
    apiClient.delete(`/compute/v1/projects/${project}/regions/${region}/routers/${router}`),
  
  // Addresses (Static IPs)
  listAddresses: (project: string, region: string) =>
    apiClient.get(`/compute/v1/projects/${project}/regions/${region}/addresses`),
  
  getAddress: (project: string, region: string, address: string) =>
    apiClient.get(`/compute/v1/projects/${project}/regions/${region}/addresses/${address}`),
  
  createAddress: (project: string, region: string, data: any) =>
    apiClient.post(`/compute/v1/projects/${project}/regions/${region}/addresses`, data),
  
  deleteAddress: (project: string, region: string, address: string) =>
    apiClient.delete(`/compute/v1/projects/${project}/regions/${region}/addresses/${address}`),
};
