import { useQuery } from '@tanstack/react-query';
import { vpcApi } from '@/api/vpc';
import { useProjectStore } from '@/stores/projectStore';

export function useVPC() {
  const { selectedProject } = useProjectStore();

  const listNetworks = useQuery({
    queryKey: ['networks', selectedProject],
    queryFn: async () => {
      if (!selectedProject) throw new Error('No project selected');
      const response = await vpcApi.listNetworks(selectedProject);
      return response.data.items || [];
    },
    enabled: !!selectedProject,
  });

  const listFirewalls = useQuery({
    queryKey: ['firewalls', selectedProject],
    queryFn: async () => {
      if (!selectedProject) throw new Error('No project selected');
      const response = await vpcApi.listFirewalls(selectedProject);
      return response.data.items || [];
    },
    enabled: !!selectedProject,
  });

  return { listNetworks, listFirewalls };
}
