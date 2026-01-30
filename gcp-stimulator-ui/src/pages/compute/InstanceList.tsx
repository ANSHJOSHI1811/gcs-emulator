
import { Box, Typography, Button, IconButton } from '@mui/material';
import AddIcon from '@mui/icons-material/Add';
import PlayArrowIcon from '@mui/icons-material/PlayArrow';
import StopIcon from '@mui/icons-material/Stop';
import { useNavigate } from 'react-router-dom';
import { useMutation, useQueryClient } from '@tanstack/react-query';
import { toast } from 'react-toastify';
import { DataTable, LoadingSpinner, ErrorAlert, EmptyState, StatusChip, Column } from '@/components/common';
import { useCompute } from '@/hooks/useCompute';
import { computeApi } from '@/api/compute';
import { Instance } from '@/types/compute';
import { useProjectStore } from '@/stores/projectStore';

export default function InstanceList() {
  const navigate = useNavigate();
  const queryClient = useQueryClient();
  const { selectedProject } = useProjectStore();
  const { listInstances } = useCompute();
  const instances = listInstances('us-central1-a');

  const startMutation = useMutation({
    mutationFn: ({ instance, zone }: { instance: string; zone: string }) =>
      computeApi.startInstance(selectedProject!, zone, instance),
    onSuccess: () => { queryClient.invalidateQueries({ queryKey: ['instances'] }); toast.success('Instance started'); },
    onError: (error: any) => toast.error(error?.response?.data?.error?.message || 'Failed to start'),
  });

  const stopMutation = useMutation({
    mutationFn: ({ instance, zone }: { instance: string; zone: string }) =>
      computeApi.stopInstance(selectedProject!, zone, instance),
    onSuccess: () => { queryClient.invalidateQueries({ queryKey: ['instances'] }); toast.success('Instance stopped'); },
    onError: (error: any) => toast.error(error?.response?.data?.error?.message || 'Failed to stop'),
  });

  const columns: Column<Instance>[] = [
    { id: 'name', label: 'Name', minWidth: 200 },
    { id: 'zone', label: 'Zone', minWidth: 120 },
    { id: 'machineType', label: 'Machine Type', minWidth: 150, format: (value) => value.split('/').pop() },
    { id: 'status', label: 'Status', minWidth: 120, format: (value) => <StatusChip status={value} /> },
    {
      id: 'actions', label: 'Actions', minWidth: 150, align: 'right', sortable: false,
      format: (_, instance) => (
        <Box sx={{ display: 'flex', gap: 1, justifyContent: 'flex-end' }}>
          {instance.status === 'RUNNING' && <IconButton size="small" color="warning" onClick={(e) => { e.stopPropagation(); stopMutation.mutate({ instance: instance.name, zone: instance.zone }); }}><StopIcon /></IconButton>}
          {instance.status === 'TERMINATED' && <IconButton size="small" color="success" onClick={(e) => { e.stopPropagation(); startMutation.mutate({ instance: instance.name, zone: instance.zone }); }}><PlayArrowIcon /></IconButton>}
        </Box>
      ),
    },
  ];

  if (instances.isLoading) return <LoadingSpinner message="Loading instances..." />;
  if (instances.isError) return <ErrorAlert error={instances.error} onRetry={() => instances.refetch()} />;

  return (
    <Box>
      <Box sx={{ display: 'flex', justifyContent: 'space-between', mb: 3 }}>
        <Typography variant="h4">VM Instances</Typography>
        <Button variant="contained" startIcon={<AddIcon />} onClick={() => navigate('/compute/create')}>Create Instance</Button>
      </Box>
      {(instances.data?.length || 0) === 0 ? (
        <EmptyState message="No instances found" action={<Button variant="contained" startIcon={<AddIcon />} onClick={() => navigate('/compute/create')}>Create Instance</Button>} />
      ) : (
        <DataTable columns={columns} rows={instances.data || []} getRowId={(row) => row.name} />
      )}
    </Box>
  );
}
