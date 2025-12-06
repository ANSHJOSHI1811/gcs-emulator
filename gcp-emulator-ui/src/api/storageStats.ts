import { apiClient } from './client';

interface DashboardStats {
  totalObjects: number;
  totalStorageBytes: number;
}

/**
 * Fetches aggregated dashboard statistics from backend.
 * Uses server-side aggregation for efficient performance.
 * @returns An object containing total objects and total storage in bytes.
 */
export const getDashboardStats = async (): Promise<DashboardStats> => {
  const response = await apiClient.get<DashboardStats>('/dashboard/stats');
  return response.data;
};
