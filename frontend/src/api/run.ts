import { apiClient, getCurrentProject } from './client';

export interface RunRevision {
  name: string;
  image: string;
  containerPort: number;
  env: Array<{ name: string; value?: string }>;
  percent: number;
  createTime?: string;
}

export interface RunTrafficTarget {
  revision?: string;
  percent: number;
  tag?: string;
  latestRevision?: boolean;
}

export interface RunService {
  name: string;
  serviceId: string;
  location: string;
  latestReadyRevision: string;
  traffic: RunTrafficTarget[];
  revisions: RunRevision[];
  uri: string;
  simulatedUrl: string;
  activeLocalUrl: string;
  updateTime?: string;
  createTime?: string;
}

export interface RunOperation {
  name: string;
  done: boolean;
  response?: unknown;
  metadata?: Record<string, unknown>;
}

export interface RunDeployPayload {
  image: string;
  containerPort?: number;
  env?: Array<{ name: string; value?: string }>;
  ingress?: string;
  labels?: Record<string, string>;
  annotations?: Record<string, string>;
}

interface RawRunService {
  name: string;
  latestReadyRevision?: string;
  traffic?: RunTrafficTarget[];
  template?: {
    containers?: Array<{
      image?: string;
      ports?: Array<{ containerPort?: number }>;
      env?: Array<{ name: string; value?: string }>;
    }>;
  };
  revisions?: Array<{
    name?: string;
    image?: string;
    containerPort?: number;
    env?: Array<{ name: string; value?: string }>;
    percent?: number;
    createTime?: string;
  }>;
  urls?: {
    simulated?: string;
    activeLocal?: string;
  };
  uri?: string;
  createTime?: string;
  updateTime?: string;
  location?: string;
}

function lastPathToken(pathOrName: string): string {
  if (!pathOrName) return '';
  const parts = pathOrName.split('/').filter(Boolean);
  return parts[parts.length - 1] || pathOrName;
}

function extractLocation(resourceName: string): string {
  const parts = resourceName.split('/');
  const locIdx = parts.indexOf('locations');
  return locIdx >= 0 && parts[locIdx + 1] ? parts[locIdx + 1] : 'us-central1';
}

function normalizeService(raw: RawRunService): RunService {
  const serviceId = lastPathToken(raw.name);
  const location = extractLocation(raw.name);

  const templateContainer = raw.template?.containers?.[0];
  const templateImage = templateContainer?.image || '';
  const templatePort = templateContainer?.ports?.[0]?.containerPort ?? 8080;
  const templateEnv = templateContainer?.env || [];

  let revisions: RunRevision[] = (raw.revisions || []).map((rev) => ({
    name: rev.name || '',
    image: rev.image || templateImage,
    containerPort: rev.containerPort ?? templatePort,
    env: rev.env || templateEnv,
    percent: rev.percent ?? 0,
    createTime: rev.createTime,
  }));

  const traffic = (raw.traffic || []).map((t) => ({
    revision: t.revision,
    percent: Number(t.percent || 0),
    tag: t.tag,
    latestRevision: Boolean(t.latestRevision),
  }));

  if (revisions.length === 0) {
    const trafficRevisions = traffic
      .map((t) => lastPathToken(t.revision || ''))
      .filter(Boolean);
    const latest = lastPathToken(raw.latestReadyRevision || '');
    const names = Array.from(new Set([...trafficRevisions, latest].filter(Boolean)));
    revisions = names.map((name) => ({
      name,
      image: templateImage,
      containerPort: templatePort,
      env: templateEnv,
      percent: traffic.find((t) => lastPathToken(t.revision || '') === name)?.percent ?? 0,
      createTime: raw.createTime,
    }));
  }

  return {
    name: raw.name,
    serviceId,
    location,
    latestReadyRevision: lastPathToken(raw.latestReadyRevision || ''),
    traffic,
    revisions,
    uri: raw.uri || '',
    simulatedUrl: raw.urls?.simulated || raw.uri || '',
    activeLocalUrl: raw.urls?.activeLocal || '',
    createTime: raw.createTime,
    updateTime: raw.updateTime,
  };
}

function unwrapOperationService(data: unknown): RunService {
  const op = data as RunOperation;
  const raw = (op?.response || data) as RawRunService;
  return normalizeService(raw);
}

export async function listRunServices(location: string, project?: string): Promise<RunService[]> {
  const proj = project || getCurrentProject();
  const res = await apiClient.get<{ services?: RawRunService[] }>(
    `/v2/projects/${proj}/locations/${location}/services`
  );
  return (res.data.services || []).map(normalizeService);
}

export async function getRunService(location: string, serviceName: string): Promise<RunService> {
  const project = getCurrentProject();
  const res = await apiClient.get<RawRunService>(
    `/v2/projects/${project}/locations/${location}/services/${serviceName}`
  );
  return normalizeService(res.data);
}

export async function deployRunService(
  location: string,
  serviceId: string,
  payload: RunDeployPayload
): Promise<RunService> {
  const project = getCurrentProject();
  const body = {
    template: {
      containers: [
        {
          image: payload.image,
          ports: [{ containerPort: payload.containerPort ?? 8080 }],
          env: payload.env || [],
        },
      ],
    },
    ingress: payload.ingress || 'INGRESS_TRAFFIC_ALL',
    labels: payload.labels || {},
    annotations: payload.annotations || {},
  };

  const res = await apiClient.post<RunOperation>(
    `/v2/projects/${project}/locations/${location}/services`,
    body,
    { params: { serviceId } }
  );
  return unwrapOperationService(res.data);
}

export async function updateRunTraffic(
  location: string,
  serviceName: string,
  traffic: RunTrafficTarget[]
): Promise<RunService> {
  const project = getCurrentProject();
  const res = await apiClient.patch<RunOperation>(
    `/v2/projects/${project}/locations/${location}/services/${serviceName}`,
    { traffic },
    { params: { updateMask: 'traffic' } }
  );
  return unwrapOperationService(res.data);
}

export async function deleteRunService(location: string, serviceName: string): Promise<void> {
  const project = getCurrentProject();
  await apiClient.delete(`/v2/projects/${project}/locations/${location}/services/${serviceName}`);
}
