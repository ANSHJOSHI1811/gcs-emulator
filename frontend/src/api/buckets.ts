import { apiClient, PROJECT_ID } from './client';
import { Bucket } from '@/types';

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
    `/storage/v1/b?project=${PROJECT_ID}`
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
    `/storage/v1/b?project=${PROJECT_ID}`,
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
  await apiClient.delete(`/storage/v1/b/${name}?project=${PROJECT_ID}`);
}
