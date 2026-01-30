import apiClient from './client';

export const computeApi = {
  // Instances
  listInstances: (project: string, zone: string) =>
    apiClient.get(`/compute/v1/projects/${project}/zones/${zone}/instances`),
  
  aggregatedListInstances: (project: string) =>
    apiClient.get(`/compute/v1/projects/${project}/aggregated/instances`),
  
  getInstance: (project: string, zone: string, instance: string) =>
    apiClient.get(`/compute/v1/projects/${project}/zones/${zone}/instances/${instance}`),
  
  createInstance: (project: string, zone: string, data: any) =>
    apiClient.post(`/compute/v1/projects/${project}/zones/${zone}/instances`, data),
  
  deleteInstance: (project: string, zone: string, instance: string) =>
    apiClient.delete(`/compute/v1/projects/${project}/zones/${zone}/instances/${instance}`),
  
  startInstance: (project: string, zone: string, instance: string) =>
    apiClient.post(`/compute/v1/projects/${project}/zones/${zone}/instances/${instance}/start`),
  
  stopInstance: (project: string, zone: string, instance: string) =>
    apiClient.post(`/compute/v1/projects/${project}/zones/${zone}/instances/${instance}/stop`),
  
  resetInstance: (project: string, zone: string, instance: string) =>
    apiClient.post(`/compute/v1/projects/${project}/zones/${zone}/instances/${instance}/reset`),
  
  // Machine Types
  listMachineTypes: (project: string, zone: string) =>
    apiClient.get(`/compute/v1/projects/${project}/zones/${zone}/machineTypes`),
  
  getMachineType: (project: string, zone: string, machineType: string) =>
    apiClient.get(`/compute/v1/projects/${project}/zones/${zone}/machineTypes/${machineType}`),
  
  // Zones
  listZones: (project: string) =>
    apiClient.get(`/compute/v1/projects/${project}/zones`),
  
  getZone: (project: string, zone: string) =>
    apiClient.get(`/compute/v1/projects/${project}/zones/${zone}`),
  
  // Regions
  listRegions: (project: string) =>
    apiClient.get(`/compute/v1/projects/${project}/regions`),
  
  getRegion: (project: string, region: string) =>
    apiClient.get(`/compute/v1/projects/${project}/regions/${region}`),
  
  // Disks
  listDisks: (project: string, zone: string) =>
    apiClient.get(`/compute/v1/projects/${project}/zones/${zone}/disks`),
  
  getDisk: (project: string, zone: string, disk: string) =>
    apiClient.get(`/compute/v1/projects/${project}/zones/${zone}/disks/${disk}`),
  
  createDisk: (project: string, zone: string, data: any) =>
    apiClient.post(`/compute/v1/projects/${project}/zones/${zone}/disks`, data),
  
  deleteDisk: (project: string, zone: string, disk: string) =>
    apiClient.delete(`/compute/v1/projects/${project}/zones/${zone}/disks/${disk}`),
};
