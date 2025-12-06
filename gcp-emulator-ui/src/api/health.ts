import { apiClient as api } from './client';
import { ListBucketsResponse } from '../types';

export interface HealthStatus {
  status: 'healthy' | 'unhealthy' | 'unknown';
  message?: string;
}

export interface StorageStats {
  totalBuckets: number;
  totalObjects: number | 'N/A';
  approximateStorageUsed: number | 'N/A'; // in bytes
}

/**
 * Checks the health of the API.
 * It first tries the /health endpoint, then falls back to the root /.
 */
export const getApiHealth = async (): Promise<HealthStatus> => {
  try {
    await api.get('/health');
    return { status: 'healthy', message: 'API is responsive.' };
  } catch (error: any) {
    try {
      // Fallback to root if /health is not found
      await api.get('/');
      return { status: 'healthy', message: 'API is responsive.' };
    } catch (rootError: any) {
      if (error.response?.status === 404) {
        return { status: 'unknown', message: 'Health endpoint not implemented' };
      }
      return { status: 'unhealthy', message: error.message || 'API is not reachable.' };
    }
  }
};

/**
 * Fetches storage statistics.
 */
export const getStorageStats = async (): Promise<StorageStats> => {
  try {
    const { data } = await api.get<ListBucketsResponse>('/storage/v1/b?project=test-project');
    const buckets = data.items || [];
    const totalBuckets = buckets.length;

    // TODO: The current backend bucket list response does not include object counts or sizes.
    // This would require iterating over each bucket, which is inefficient.
    // Returning 'N/A' as per requirements.
    const totalObjects = 'N/A';
    const approximateStorageUsed = 'N/A';

    return {
      totalBuckets,
      totalObjects,
      approximateStorageUsed,
    };
  } catch (error) {
    console.error("Failed to get storage stats:", error);
    return {
      totalBuckets: 0,
      totalObjects: 'N/A',
      approximateStorageUsed: 'N/A',
    };
  }
};
