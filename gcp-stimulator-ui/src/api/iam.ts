import apiClient from './client';

export const iamApi = {
  // Service Accounts
  listServiceAccounts: (project: string) =>
    apiClient.get(`/iam/v1/projects/${project}/serviceAccounts`),
  
  getServiceAccount: (name: string) =>
    apiClient.get(`/iam/v1/${name}`),
  
  createServiceAccount: (project: string, data: any) =>
    apiClient.post(`/iam/v1/projects/${project}/serviceAccounts`, data),
  
  deleteServiceAccount: (name: string) =>
    apiClient.delete(`/iam/v1/${name}`),
  
  updateServiceAccount: (name: string, data: any) =>
    apiClient.patch(`/iam/v1/${name}`, data),
  
  // Service Account Keys
  listKeys: (serviceAccount: string) =>
    apiClient.get(`/iam/v1/${serviceAccount}/keys`),
  
  getKey: (keyName: string) =>
    apiClient.get(`/iam/v1/${keyName}`),
  
  createKey: (serviceAccount: string, data?: any) =>
    apiClient.post(`/iam/v1/${serviceAccount}/keys`, data || {}),
  
  deleteKey: (keyName: string) =>
    apiClient.delete(`/iam/v1/${keyName}`),
  
  // IAM Policies
  getIamPolicy: (resource: string) =>
    apiClient.post(`/iam/v1/${resource}:getIamPolicy`),
  
  setIamPolicy: (resource: string, policy: any) =>
    apiClient.post(`/iam/v1/${resource}:setIamPolicy`, { policy }),
  
  testIamPermissions: (resource: string, permissions: string[]) =>
    apiClient.post(`/iam/v1/${resource}:testIamPermissions`, { permissions }),
  
  // Roles
  listRoles: (parent?: string) =>
    apiClient.get(`/iam/v1/roles`, { params: { parent } }),
  
  getRole: (name: string) =>
    apiClient.get(`/iam/v1/${name}`),
  
  createRole: (parent: string, data: any) =>
    apiClient.post(`/iam/v1/${parent}/roles`, data),
  
  updateRole: (name: string, data: any) =>
    apiClient.patch(`/iam/v1/${name}`, data),
  
  deleteRole: (name: string) =>
    apiClient.delete(`/iam/v1/${name}`),
  
  // Projects (for IAM policy at project level)
  getProjectIamPolicy: (project: string) =>
    apiClient.post(`/cloudresourcemanager/v1/projects/${project}:getIamPolicy`),
  
  setProjectIamPolicy: (project: string, policy: any) =>
    apiClient.post(`/cloudresourcemanager/v1/projects/${project}:setIamPolicy`, { policy }),
};
