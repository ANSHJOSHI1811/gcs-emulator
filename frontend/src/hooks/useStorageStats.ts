import { useState, useEffect, useCallback } from 'react';
import { getDashboardStats } from '../api/storageStats';

export const useStorageStats = () => {
  const [totalObjects, setTotalObjects] = useState(0);
  const [totalStorageBytes, setTotalStorageBytes] = useState(0);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const fetchStats = useCallback(async () => {
    setIsLoading(true);
    setError(null);
    try {
      const { totalObjects, totalStorageBytes } = await getDashboardStats();
      setTotalObjects(totalObjects);
      setTotalStorageBytes(totalStorageBytes);
    } catch (err: any) {
      setError(err.message || 'Failed to fetch storage statistics.');
      setTotalObjects(0);
      setTotalStorageBytes(0);
    } finally {
      setIsLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchStats();
  }, [fetchStats]);

  return {
    totalObjects,
    totalStorageBytes,
    isLoading,
    error,
    refresh: fetchStats,
  };
};
