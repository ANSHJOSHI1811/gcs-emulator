import { useState } from 'react';
import { Box, Typography, IconButton, Chip } from '@mui/material';
import DeleteIcon from '@mui/icons-material/Delete';
import { useMutation, useQueryClient } from '@tanstack/react-query';
import { toast } from 'react-toastify';
import { DataTable, LoadingSpinner, ErrorAlert, EmptyState, SearchInput, ConfirmDialog, Column } from '@/components/common';
import { useVPC } from '@/hooks/useVPC';
import { vpcApi } from '@/api/vpc';
import { Network } from '@/types/vpc';
import { useProjectStore } from '@/stores/projectStore';

export default function NetworkList() {
  
  const queryClient = useQueryClient();
  const { selectedProject } = useProjectStore();
  const { listNetworks } = useVPC();
  const [searchQuery, setSearchQuery] = useState('');
  const [deleteDialogOpen, setDeleteDialogOpen] = useState(false);
  const [networkToDelete, setNetworkToDelete] = useState<string | null>(null);

  const deleteMutation = useMutation({
    mutationFn: (network: string) => vpcApi.deleteNetwork(selectedProject!, network),
    onSuccess: () => { queryClient.invalidateQueries({ queryKey: ['networks'] }); toast.success('Network deleted'); setDeleteDialogOpen(false); },
    onError: (error: any) => toast.error(error?.response?.data?.error?.message || 'Failed to delete'),
  });

  const filteredNetworks = (listNetworks.data || []).filter((network: Network) =>
    network.name.toLowerCase().includes(searchQuery.toLowerCase())
  );

  const columns: Column<Network>[] = [
    { id: 'name', label: 'Name', minWidth: 200 },
    { id: 'autoCreateSubnetworks', label: 'Subnet Mode', minWidth: 150, format: (value) => <Chip label={value ? 'Auto' : 'Custom'} size="small" /> },
    { id: 'creationTimestamp', label: 'Created', minWidth: 150, format: (value) => new Date(value).toLocaleString() },
    {
      id: 'actions', label: 'Actions', minWidth: 120, align: 'right', sortable: false,
      format: (_, network) => (
        <IconButton size="small" color="error" onClick={(e) => { e.stopPropagation(); setNetworkToDelete(network.name); setDeleteDialogOpen(true); }}><DeleteIcon /></IconButton>
      ),
    },
  ];

  if (listNetworks.isLoading) return <LoadingSpinner />;
  if (listNetworks.isError) return <ErrorAlert error={listNetworks.error} onRetry={() => listNetworks.refetch()} />;

  return (
    <Box>
      <Box sx={{ display: 'flex', justifyContent: 'space-between', mb: 3 }}>
        <Typography variant="h4">VPC Networks</Typography>
      </Box>
      <SearchInput onSearch={setSearchQuery} placeholder="Search networks..." />
      <Box sx={{ mt: 2 }}>
        {filteredNetworks.length === 0 ? <EmptyState message="No networks found" /> : <DataTable columns={columns} rows={filteredNetworks} getRowId={(row) => row.name} />}
      </Box>
      <ConfirmDialog open={deleteDialogOpen} onClose={() => setDeleteDialogOpen(false)} onConfirm={() => networkToDelete && deleteMutation.mutate(networkToDelete)} title="Delete Network" message="Are you sure?" danger loading={deleteMutation.isPending} />
    </Box>
  );
}
