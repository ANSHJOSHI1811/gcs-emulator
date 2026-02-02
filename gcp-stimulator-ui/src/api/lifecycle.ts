import { apiClient } from './client';

export interface LifecycleRule {
  action: 'Delete' | 'Archive';
  ageDays: number;
}

export interface LifecycleConfig {
  kind: string;
  rule: LifecycleRule[];
}

// Phase 4: Lifecycle Configuration API (GCS-compatible endpoints)
export async function getLifecycleRules(bucketName: string): Promise<LifecycleRule[]> {
  const response = await apiClient.get<LifecycleConfig>(
    `/storage/v1/b/${bucketName}/lifecycle`
  );
  return response.data.rule || [];
}

export async function updateLifecycleRules(
  bucketName: string,
  rules: LifecycleRule[]
): Promise<LifecycleRule[]> {
  const response = await apiClient.put<LifecycleConfig>(
    `/storage/v1/b/${bucketName}/lifecycle`,
    { rule: rules }
  );
  return response.data.rule;
}

export async function deleteLifecycleConfig(bucketName: string): Promise<void> {
  await apiClient.delete(`/storage/v1/b/${bucketName}/lifecycle`);
}
