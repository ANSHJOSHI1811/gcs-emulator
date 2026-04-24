import { apiClient, getCurrentProject } from './client';
import { Bucket, ACLResponse, ACLValue } from '@/types';

interface BackendBucket {
  name: string;
  location: string;
  storageClass: string;
  timeCreated: string;
  updated: string;
}

interface BackendBucketListResponse {
  items: BackendBucket[];
}

export async function fetchBuckets(): Promise<Bucket[]> {
  const response = await apiClient.get<BackendBucketListResponse>(
    `/storage/v1/b?project=${getCurrentProject()}`
  );
  if (!response.data.items) {
    return [];
  }
  return response.data.items.map((item) => ({
    name: item.name,
    location: item.location,
    storageClass: item.storageClass,
    timeCreated: item.timeCreated,
    updated: item.updated,
  }));
}

export async function createBucket(
  name: string
): Promise<Bucket> {
  const response = await apiClient.post<BackendBucket>(
    `/storage/v1/b?project=${getCurrentProject()}`,
    { name }
  );
  const item = response.data;
  return {
    name: item.name,
    location: item.location,
    storageClass: item.storageClass,
    timeCreated: item.timeCreated,
    updated: item.updated,
  };
}

export async function deleteBucket(name: string): Promise<void> {
  await apiClient.delete(`/storage/v1/b/${name}?project=${getCurrentProject()}`);
}

// Phase 4: Bucket ACL Management
export async function getBucketACL(bucketName: string): Promise<ACLValue> {
  const response = await apiClient.get<ACLResponse>(
    `/storage/v1/b/${bucketName}/acl`
  );
  return response.data.acl;
}

export async function updateBucketACL(bucketName: string, acl: ACLValue): Promise<ACLValue> {
  const response = await apiClient.patch<ACLResponse>(
    `/storage/v1/b/${bucketName}/acl`,
    { acl }
  );
  return response.data.acl;
}
