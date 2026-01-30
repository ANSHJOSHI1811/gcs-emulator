import { useQuery } from '@tanstack/react-query';
import { storageApi } from '@/api/storage';
import { useProjectStore } from '@/stores/projectStore';

export function useStorage() {
  const { selectedProject } = useProjectStore();

  const listBuckets = useQuery({
    queryKey: ['buckets', selectedProject],
    queryFn: async () => {
      if (!selectedProject) throw new Error('No project selected');
      const response = await storageApi.listBuckets(selectedProject);
      return response.data.items || [];
    },
    enabled: !!selectedProject,
  });

  const listObjects = (bucket: string, prefix?: string) =>
    useQuery({
      queryKey: ['objects', bucket, prefix],
      queryFn: async () => {
        const response = await storageApi.listObjects(bucket, prefix);
        return response.data.items || [];
      },
      enabled: !!bucket,
    });

  return {
    listBuckets,
    listObjects,
  };
}
