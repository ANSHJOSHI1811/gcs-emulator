import { apiClient, getCurrentProject } from './client';

export interface Replication {
  automatic?: Record<string, never>;
  userManaged?: {
    replicas: Array<{ location: string }>;
  };
}

export interface Secret {
  name: string;
  replication: Replication;
  createTime: string;
  labels: Record<string, string>;
  description?: string;
}

export interface SecretVersion {
  name: string;
  createTime: string;
  state: 'ENABLED' | 'DISABLED' | 'DESTROYED';
  destroyTime?: string;
}

export interface AccessSecretVersionResponse {
  name: string;
  payload: {
    data: string;
  };
}

// ============================================================================
// SECRETS
// ============================================================================

export async function listSecrets(project?: string): Promise<Secret[]> {
  const proj = project || getCurrentProject();
  const response = await apiClient.get<{ secrets?: Secret[]; nextPageToken?: string }>(
    `/v1/projects/${proj}/secrets`
  );
  return response.data.secrets || [];
}

export async function getSecret(secretName: string): Promise<Secret> {
  const response = await apiClient.get<Secret>(`/v1/${secretName}`);
  return response.data;
}

export async function createSecret(payload: {
  secretId: string;
  replication?: Replication;
  labels?: Record<string, string>;
  description?: string;
  project?: string;
}): Promise<Secret> {
  const proj = payload.project || getCurrentProject();
  const response = await apiClient.post<Secret>(`/v1/projects/${proj}/secrets`, {
    secretId: payload.secretId,
    replication: payload.replication || { automatic: {} },
    labels: payload.labels || {},
    description: payload.description || '',
  });
  return response.data;
}

export async function updateSecret(
  secretName: string,
  updates: {
    labels?: Record<string, string>;
    description?: string;
  }
): Promise<Secret> {
  const response = await apiClient.patch<Secret>(`/v1/${secretName}`, {
    secret: updates,
  });
  return response.data;
}

export async function deleteSecret(secretName: string): Promise<void> {
  await apiClient.delete(`/v1/${secretName}`);
}

// ============================================================================
// SECRET VERSIONS
// ============================================================================

export async function listVersions(secretName: string): Promise<SecretVersion[]> {
  const response = await apiClient.get<{
    versions?: SecretVersion[];
    nextPageToken?: string;
  }>(`/v1/${secretName}/versions`);
  return response.data.versions || [];
}

export async function getVersion(versionName: string): Promise<SecretVersion> {
  const response = await apiClient.get<SecretVersion>(`/v1/${versionName}`);
  return response.data;
}

export async function addSecretVersion(
  secretName: string,
  data: string
): Promise<SecretVersion> {
  const response = await apiClient.post<SecretVersion>(`/v1/${secretName}:addVersion`, {
    payload: { data },
  });
  return response.data;
}

export async function accessSecretVersion(
  versionName: string
): Promise<AccessSecretVersionResponse> {
  const response = await apiClient.post<AccessSecretVersionResponse>(
    `/v1/${versionName}:access`,
    {}
  );
  return response.data;
}

export async function enableSecretVersion(versionName: string): Promise<SecretVersion> {
  const response = await apiClient.post<SecretVersion>(`/v1/${versionName}:enable`, {});
  return response.data;
}

export async function disableSecretVersion(versionName: string): Promise<SecretVersion> {
  const response = await apiClient.post<SecretVersion>(`/v1/${versionName}:disable`, {});
  return response.data;
}

export async function destroySecretVersion(versionName: string): Promise<SecretVersion> {
  const response = await apiClient.post<SecretVersion>(`/v1/${versionName}:destroy`, {});
  return response.data;
}

// ============================================================================
// UTILITIES
// ============================================================================

export async function generatePassword(options?: {
  length?: number;
  includeUppercase?: boolean;
  includeLowercase?: boolean;
  includeDigits?: boolean;
  includeSymbols?: boolean;
  excludeAmbiguous?: boolean;
}): Promise<string> {
  const response = await apiClient.post<{ password: string }>('/generateRandomPassword', {
    length: options?.length || 16,
    includeUppercase: options?.includeUppercase ?? true,
    includeLowercase: options?.includeLowercase ?? true,
    includeDigits: options?.includeDigits ?? true,
    includeSymbols: options?.includeSymbols ?? true,
    excludeAmbiguous: options?.excludeAmbiguous ?? true,
  });
  return response.data.password;
}
