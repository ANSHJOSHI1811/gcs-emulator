import apiClient from './client';
import { Bucket, CreateBucketRequest, ListBucketsResponse } from '@/types';

const PROJECT_ID = import.meta.env.VITE_PROJECT_ID || 'test-project';

// TODO: The backend response for list buckets is an object with an 'items' array.
// This mapping function extracts that array. This might need adjustment
// if the backend response shape changes.
interface BackendBucketListResponse {
  items: any[];
}

export async function fetchBuckets(): Promise<Bucket[]> {
  const response = await apiClient.get<BackendBucketListResponse>(
    `/storage/v1/b?project=${PROJECT_ID}`
  );
  // The actual bucket data is in response.data.items
  return response.data.items.map((item: any) => ({
    name: item.name,
    location: item.location,
    storageClass: item.storageClass,
    timeCreated: item.timeCreated,
    updated: item.updated,
    // The backend doesn't provide objectCount in the list view, so we'll leave it undefined.
  }));
}

export async function createBucket(
  name: string
): Promise<Bucket> {
  const response = await apiClient.post<any>(
    `/storage/v1/b?project=${PROJECT_ID}`,
    { name }
  );
  // The backend returns the full bucket object on creation.
  return {
    name: response.data.name,
    location: response.data.location,
    storageClass: response.data.storageClass,
    timeCreated: response.data.timeCreated,
    updated: response.data.updated,
  };
}

export async function deleteBucket(name: string): Promise<void> {
  await apiClient.delete(`/storage/v1/b/${name}`);
}
