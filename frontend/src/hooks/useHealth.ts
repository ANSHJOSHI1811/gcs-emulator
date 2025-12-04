import { useState, useEffect, useCallback } from 'react';
import { getApiHealth, getStorageStats, HealthStatus, StorageStats } from '../api/health';

export const useHealth = () => {
  const [healthStatus, setHealthStatus] = useState<HealthStatus | null>(null);
  const [storageStats, setStorageStats] = useState<StorageStats | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const fetchData = useCallback(async () => {
    setIsLoading(true);
    setError(null);
    try {
      const [health, stats] = await Promise.all([
        getApiHealth(),
        getStorageStats(),
      ]);
      setHealthStatus(health);
      setStorageStats(stats);
    } catch (err: any) {
      setError(err.message || 'Failed to fetch health and storage data.');
    } finally {
      setIsLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchData();
  }, [fetchData]);

  return {
    healthStatus,
    storageStats,
    isLoading,
    error,
    refresh: fetchData,
  };
};
