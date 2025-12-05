import { apiClient, PROJECT_ID } from './client';
import { ListBucketsResponse, ListObjectsResponse } from '../types';

interface DashboardStats {
  totalObjects: number;
  totalStorageBytes: number;
}

/**
 * Fetches all objects from all buckets to calculate total object count and storage size.
 * This is a potentially expensive operation.
 * @returns An object containing total objects and total storage in bytes.
 */
export const getDashboardStats = async (): Promise<DashboardStats> => {
  let totalObjects = 0;
  let totalStorageBytes = 0;

  // 1. Fetch all buckets
  const bucketsResponse = await apiClient.get<ListBucketsResponse>(`/storage/v1/b?project=${PROJECT_ID}`);
  const buckets = bucketsResponse.data.items || [];

  // 2. For each bucket, fetch its objects
  const objectPromises = buckets.map(bucket =>
    apiClient.get<ListObjectsResponse>(`/storage/v1/b/${bucket.name}/o?project=${PROJECT_ID}`)
  );

  const objectResponses = await Promise.all(objectPromises);

  // 3. Sum objects and their sizes
  for (const res of objectResponses) {
    const objects = res.data.items || [];
    totalObjects += objects.length;
    totalStorageBytes += objects.reduce((sum, obj) => sum + (obj.size || 0), 0);
  }

  return { totalObjects, totalStorageBytes };
};
