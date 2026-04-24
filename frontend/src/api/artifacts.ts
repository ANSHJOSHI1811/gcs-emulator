import { apiClient, getCurrentProject } from './client';

export interface ArtifactRepository {
  name: string;
  repositoryId: string;
  location: string;
  format: string;
  description: string;
  labels: Record<string, string>;
  createTime: string;
  updateTime: string;
  registryHost: string;
  dockerRepositoryPrefix: string;
}

export interface ArtifactOperation {
  name: string;
  done: boolean;
  response?: unknown;
  metadata?: Record<string, unknown>;
}

export interface RepoPayload {
  format: string;
  description: string;
  labels: Record<string, string>;
}

export interface RegistryStatus {
  repository: ArtifactRepository;
  registry: {
    container_id: string;
    endpoint: string;
    status: string;
  };
  pushExample: string;
}

interface RawRepository {
  name: string;
  format?: string;
  description?: string;
  labels?: Record<string, string>;
  createTime?: string;
  updateTime?: string;
  registryHost?: string;
  dockerRepositoryPrefix?: string;
}

function parseRepoName(fullName: string): { repositoryId: string; location: string } {
  const parts = fullName.split('/');
  const repoIdx = parts.indexOf('repositories');
  const locIdx = parts.indexOf('locations');
  return {
    repositoryId: repoIdx >= 0 ? (parts[repoIdx + 1] || '') : fullName,
    location: locIdx >= 0 ? (parts[locIdx + 1] || 'us-central1') : 'us-central1',
  };
}

function normalizeRepository(raw: RawRepository): ArtifactRepository {
  const parsed = parseRepoName(raw.name || '');
  return {
    name: raw.name,
    repositoryId: parsed.repositoryId,
    location: parsed.location,
    format: raw.format || 'DOCKER',
    description: raw.description || '',
    labels: raw.labels || {},
    createTime: raw.createTime || '',
    updateTime: raw.updateTime || raw.createTime || '',
    registryHost: raw.registryHost || 'localhost:5000',
    dockerRepositoryPrefix: raw.dockerRepositoryPrefix || '',
  };
}

function unwrapOperationRepo(data: unknown): ArtifactRepository {
  const op = data as ArtifactOperation;
  const raw = (op?.response || data) as RawRepository;
  return normalizeRepository(raw);
}

export async function listRepositories(location: string, project?: string): Promise<ArtifactRepository[]> {
  const proj = project || getCurrentProject();
  const res = await apiClient.get<{ repositories?: RawRepository[] }>(
    `/v1/projects/${proj}/locations/${location}/repositories`
  );
  return (res.data.repositories || []).map(normalizeRepository);
}

export async function createRepository(
  location: string,
  repositoryId: string,
  payload?: Partial<RepoPayload>
): Promise<ArtifactRepository> {
  const project = getCurrentProject();
  const body = {
    format: payload?.format || 'DOCKER',
    description: payload?.description || '',
    labels: payload?.labels || {},
  };

  const res = await apiClient.post<ArtifactOperation>(
    `/v1/projects/${project}/locations/${location}/repositories`,
    body,
    { params: { repository_id: repositoryId } }
  );
  return unwrapOperationRepo(res.data);
}

export async function getRepository(location: string, repositoryId: string): Promise<ArtifactRepository> {
  const project = getCurrentProject();
  const res = await apiClient.get<RawRepository>(
    `/v1/projects/${project}/locations/${location}/repositories/${repositoryId}`
  );
  return normalizeRepository(res.data);
}

export async function deleteRepository(location: string, repositoryId: string): Promise<void> {
  const project = getCurrentProject();
  await apiClient.delete(`/v1/projects/${project}/locations/${location}/repositories/${repositoryId}`);
}

export async function ensureRegistry(location: string, repositoryId: string): Promise<RegistryStatus> {
  const project = getCurrentProject();
  const res = await apiClient.post<RegistryStatus>(
    `/v1/projects/${project}/locations/${location}/repositories/${repositoryId}:ensureRegistry`,
    {}
  );
  return {
    ...res.data,
    repository: normalizeRepository(res.data.repository as unknown as RawRepository),
  };
}
