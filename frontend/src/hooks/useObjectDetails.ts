import { useState, useCallback, useEffect } from 'react';
import { GCSObject, ObjectVersion } from '../types';
import {
  getObjectMetadata,
  listObjectVersions,
  deleteObjectVersion as apiDeleteObjectVersion,
} from '../api/objectVersionsApi';

export const useObjectDetails = (bucketName?: string, objectName?: string) => {
  const [metadata, setMetadata] = useState<GCSObject | null>(null);
  const [versions, setVersions] = useState<ObjectVersion[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const refresh = useCallback(async () => {
    if (!bucketName || !objectName) return;

    setIsLoading(true);
    setError(null);

    try {
      const [meta, vers] = await Promise.all([
        getObjectMetadata(bucketName, objectName),
        listObjectVersions(bucketName, objectName),
      ]);
      
      setMetadata(meta);
      
      const versionItems = vers.items || [];
      // Mark the latest version
      if (versionItems.length > 0 && meta.generation) {
        const latest = versionItems.find(v => v.generation === meta.generation);
        if (latest) {
          latest.isLatest = true;
        }
      }
      setVersions(versionItems);

    } catch (err) {
      setError((err as Error).message);
    } finally {
      setIsLoading(false);
    }
  }, [bucketName, objectName]);

  useEffect(() => {
    refresh();
  }, [refresh]);

  const deleteVersion = async (generation: string) => {
    if (!bucketName || !objectName) return;

    try {
      await apiDeleteObjectVersion(bucketName, objectName, generation);
      await refresh(); // Refresh the list after deletion
    } catch (err) {
      setError((err as Error).message);
      // Re-throw to allow UI to handle it
      throw err;
    }
  };

  return {
    isLoading,
    error,
    metadata,
    versions,
    refresh,
    deleteVersion,
  };
};
