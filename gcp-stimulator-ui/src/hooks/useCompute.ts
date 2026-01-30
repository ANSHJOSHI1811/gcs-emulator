import { useQuery } from '@tanstack/react-query';
import { computeApi } from '@/api/compute';
import { useProjectStore } from '@/stores/projectStore';

export function useCompute() {
  const { selectedProject } = useProjectStore();

  const listInstances = (zone: string = 'us-central1-a') =>
    useQuery({
      queryKey: ['instances', selectedProject, zone],
      queryFn: async () => {
        if (!selectedProject) throw new Error('No project selected');
        const response = await computeApi.listInstances(selectedProject, zone);
        return response.data.items || [];
      },
      enabled: !!selectedProject,
      refetchInterval: 5000,
    });

  const listMachineTypes = (zone: string = 'us-central1-a') =>
    useQuery({
      queryKey: ['machineTypes', selectedProject, zone],
      queryFn: async () => {
        if (!selectedProject) throw new Error('No project selected');
        const response = await computeApi.listMachineTypes(selectedProject, zone);
        return response.data.items || [];
      },
      enabled: !!selectedProject,
    });

  return { listInstances, listMachineTypes };
}
