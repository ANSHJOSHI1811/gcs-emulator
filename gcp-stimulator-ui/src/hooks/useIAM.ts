import { useQuery } from '@tanstack/react-query';
import { iamApi } from '@/api/iam';
import { useProjectStore } from '@/stores/projectStore';

export function useIAM() {
  const { selectedProject } = useProjectStore();

  const listServiceAccounts = useQuery({
    queryKey: ['serviceAccounts', selectedProject],
    queryFn: async () => {
      if (!selectedProject) throw new Error('No project selected');
      const response = await iamApi.listServiceAccounts(selectedProject);
      return response.data.accounts || [];
    },
    enabled: !!selectedProject,
  });

  return { listServiceAccounts };
}
