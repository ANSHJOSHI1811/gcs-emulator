import { apiClient, PROJECT_ID } from './client';

// ============================================================================
// Types
// ============================================================================

export interface ServiceAccount {
  name: string;
  projectId: string;
  uniqueId: string;
  email: string;
  displayName?: string;
  description?: string;
  oauth2ClientId?: string;
  disabled: boolean;
  etag?: string;
}

export interface ServiceAccountKey {
  name: string;
  keyAlgorithm: string;
  keyOrigin: string;
  keyType: string;
  validAfterTime: string;
  validBeforeTime?: string;
  disabled: boolean;
  privateKeyData?: string;
}

export interface IAMBinding {
  role: string;
  members: string[];
  condition?: {
    title?: string;
    description?: string;
    expression?: string;
  };
}

export interface IAMPolicy {
  version: number;
  bindings: IAMBinding[];
  etag?: string;
}

export interface Role {
  name: string;
  title: string;
  description?: string;
  includedPermissions: string[];
  stage: string;
  deleted: boolean;
  etag?: string;
}

// ============================================================================
// Service Account API
// ============================================================================

export async function fetchServiceAccounts(projectId: string = PROJECT_ID): Promise<ServiceAccount[]> {
  const response = await apiClient.get<{ accounts: ServiceAccount[] }>(
    `/v1/projects/${projectId}/serviceAccounts`
  );
  return response.data.accounts || [];
}

export async function getServiceAccount(
  email: string,
  projectId: string = PROJECT_ID
): Promise<ServiceAccount> {
  const response = await apiClient.get<ServiceAccount>(
    `/v1/projects/${projectId}/serviceAccounts/${email}`
  );
  return response.data;
}

export async function createServiceAccount(
  accountId: string,
  displayName?: string,
  description?: string,
  projectId: string = PROJECT_ID
): Promise<ServiceAccount> {
  const response = await apiClient.post<ServiceAccount>(
    `/v1/projects/${projectId}/serviceAccounts`,
    {
      accountId,
      displayName,
      description,
    }
  );
  return response.data;
}

export async function updateServiceAccount(
  email: string,
  displayName?: string,
  description?: string,
  projectId: string = PROJECT_ID
): Promise<ServiceAccount> {
  const response = await apiClient.patch<ServiceAccount>(
    `/v1/projects/${projectId}/serviceAccounts/${email}`,
    {
      displayName,
      description,
    }
  );
  return response.data;
}

export async function deleteServiceAccount(
  email: string,
  projectId: string = PROJECT_ID
): Promise<void> {
  await apiClient.delete(`/v1/projects/${projectId}/serviceAccounts/${email}`);
}

export async function disableServiceAccount(
  email: string,
  projectId: string = PROJECT_ID
): Promise<ServiceAccount> {
  const response = await apiClient.post<ServiceAccount>(
    `/v1/projects/${projectId}/serviceAccounts/${email}:disable`
  );
  return response.data;
}

export async function enableServiceAccount(
  email: string,
  projectId: string = PROJECT_ID
): Promise<ServiceAccount> {
  const response = await apiClient.post<ServiceAccount>(
    `/v1/projects/${projectId}/serviceAccounts/${email}:enable`
  );
  return response.data;
}

// ============================================================================
// Service Account Key API
// ============================================================================

export async function fetchServiceAccountKeys(
  email: string,
  projectId: string = PROJECT_ID
): Promise<ServiceAccountKey[]> {
  const response = await apiClient.get<{ keys: ServiceAccountKey[] }>(
    `/v1/projects/${projectId}/serviceAccounts/${email}/keys`
  );
  return response.data.keys || [];
}

export async function createServiceAccountKey(
  email: string,
  projectId: string = PROJECT_ID
): Promise<ServiceAccountKey> {
  const response = await apiClient.post<ServiceAccountKey>(
    `/v1/projects/${projectId}/serviceAccounts/${email}/keys`,
    {
      keyAlgorithm: 'KEY_ALG_RSA_2048',
      privateKeyType: 'TYPE_GOOGLE_CREDENTIALS_FILE',
    }
  );
  return response.data;
}

export async function deleteServiceAccountKey(
  email: string,
  keyId: string,
  projectId: string = PROJECT_ID
): Promise<void> {
  await apiClient.delete(
    `/v1/projects/${projectId}/serviceAccounts/${email}/keys/${keyId}`
  );
}

// ============================================================================
// IAM Policy API
// ============================================================================

export async function getIAMPolicy(resource: string): Promise<IAMPolicy> {
  const response = await apiClient.post<IAMPolicy>(`/v1/${resource}:getIamPolicy`);
  return response.data;
}

export async function setIAMPolicy(resource: string, policy: IAMPolicy): Promise<IAMPolicy> {
  const response = await apiClient.post<IAMPolicy>(`/v1/${resource}:setIamPolicy`, {
    policy,
  });
  return response.data;
}

export async function testIAMPermissions(
  resource: string,
  permissions: string[]
): Promise<string[]> {
  const response = await apiClient.post<{ permissions: string[] }>(
    `/v1/${resource}:testIamPermissions`,
    { permissions }
  );
  return response.data.permissions || [];
}

// ============================================================================
// Role API
// ============================================================================

export async function fetchRoles(projectId?: string): Promise<Role[]> {
  const url = projectId
    ? `/v1/projects/${projectId}/roles`
    : `/v1/roles`;
  const response = await apiClient.get<{ roles: Role[] }>(url);
  return response.data.roles || [];
}

export async function getRole(roleName: string): Promise<Role> {
  const response = await apiClient.get<Role>(`/v1/${roleName}`);
  return response.data;
}

export async function createRole(
  roleId: string,
  title: string,
  description?: string,
  includedPermissions?: string[],
  projectId: string = PROJECT_ID
): Promise<Role> {
  const response = await apiClient.post<Role>(
    `/v1/projects/${projectId}/roles`,
    {
      roleId,
      title,
      description,
      includedPermissions: includedPermissions || [],
      stage: 'GA',
    }
  );
  return response.data;
}

export async function updateRole(
  roleName: string,
  title?: string,
  description?: string,
  includedPermissions?: string[]
): Promise<Role> {
  const response = await apiClient.patch<Role>(`/v1/${roleName}`, {
    title,
    description,
    includedPermissions,
  });
  return response.data;
}

export async function deleteRole(roleName: string): Promise<Role> {
  const response = await apiClient.delete<Role>(`/v1/${roleName}`);
  return response.data;
}

export async function undeleteRole(roleName: string): Promise<Role> {
  const response = await apiClient.post<Role>(`/v1/${roleName}:undelete`);
  return response.data;
}
