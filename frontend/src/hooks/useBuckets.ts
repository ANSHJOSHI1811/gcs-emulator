import { useState, useCallback } from "react";
import { fetchBuckets, createBucket, deleteBucket } from "../api/buckets";
import { Bucket } from "../types";
import toast from "react-hot-toast";

export function useBuckets() {
  const [buckets, setBuckets] = useState<Bucket[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const loadBuckets = useCallback(async () => {
    try {
      setIsLoading(true);
      setError(null);
      const data = await fetchBuckets();
      setBuckets(data);
    } catch (err) {
      const message = err instanceof Error ? err.message : "Failed to load buckets";
      setError(message);
      toast.error(message);
    } finally {
      setIsLoading(false);
    }
  }, []);

  const handleCreateBucket = async (name: string) => {
    try {
      setIsLoading(true);
      const newBucket = await createBucket(name);
      setBuckets((prev) => [...prev, newBucket]);
      toast.success(`Bucket "${name}" created successfully!`);
      return newBucket;
    } catch (err) {
      const message = err instanceof Error ? err.message : "Failed to create bucket";
      toast.error(message);
      throw new Error(message);
    } finally {
      setIsLoading(false);
    }
  };

  const handleDeleteBucket = async (name: string) => {
    try {
      setIsLoading(true);
      await deleteBucket(name);
      setBuckets((prev) => prev.filter((b) => b.name !== name));
      toast.success(`Bucket "${name}" deleted successfully!`);
    } catch (err) {
      const message = err instanceof Error ? err.message : "Failed to delete bucket";
      toast.error(message);
      throw new Error(message);
    } finally {
      setIsLoading(false);
    }
  };

  return {
    buckets,
    isLoading,
    error,
    loadBuckets,
    handleCreateBucket,
    handleDeleteBucket,
  };
}
