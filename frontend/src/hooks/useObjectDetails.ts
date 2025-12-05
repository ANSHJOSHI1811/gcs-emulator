import { useState, useCallback, useEffect } from 'react';
import { GCSObject, ObjectVersion } from '../types';
import {
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
      // Single, reliable call to get all versions
      const vers = await listObjectVersions(bucketName);
      
      const allVersions = (Array.isArray(vers) ? vers : vers.items || []).filter(
        (v) => v.name === objectName
      );

      if (allVersions.length === 0) {
        // If no versions are found, it might be a non-versioned object or an error.
        // For now, we'll show "not found". A more robust solution might try a non-versioned fetch.
        setError("Object not found or has no versions.");
        setVersions([]);
        setMetadata(null);
        return;
      }

      // Find the latest version. The GCS API doesn't explicitly flag the latest in this view,
      // so we often determine it by the most recent 'updated' timestamp.
      // A simpler way is to find the one with the largest generation number.
      const latestVersion = allVersions.reduce((a, b) =>
        new Date(a.updated) > new Date(b.updated) ? a : b
      );

      // Mark the latest version in the list
      latestVersion.isLatest = true;
      
      setMetadata(latestVersion);
      setVersions(allVersions);

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
