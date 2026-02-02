import { useState, useCallback } from 'react';
import { GCSObject } from '../types';
import { listObjects, deleteObject } from '../api/objects';
import toast from 'react-hot-toast';

export function useObjects(bucketName: string) {
  const [objects, setObjects] = useState<GCSObject[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const refresh = useCallback(async () => {
    if (!bucketName) return;
    setIsLoading(true);
    setError(null);
    try {
      const data = await listObjects(bucketName);
      setObjects(data);
    } catch (err) {
      const message = err instanceof Error ? err.message : 'Failed to load objects';
      setError(message);
      toast.error(message);
    } finally {
      setIsLoading(false);
    }
  }, [bucketName]);

  const handleDelete = async (objectName: string, generation?: string) => {
    if (!bucketName) return;
    try {
      await deleteObject(bucketName, objectName, generation);
      toast.success(`Object "${objectName}" deleted successfully.`);
      await refresh();
    } catch (err) {
      const message = err instanceof Error ? err.message : 'Failed to delete object';
      toast.error(message);
    }
  };

  return { objects, isLoading, error, refresh, handleDelete };
}
