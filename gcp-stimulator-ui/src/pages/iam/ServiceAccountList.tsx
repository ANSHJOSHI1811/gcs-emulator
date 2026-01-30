import { useState } from 'react';
import { Box, Typography, IconButton } from '@mui/material';
import DeleteIcon from '@mui/icons-material/Delete';
import { useMutation, useQueryClient } from '@tanstack/react-query';
import { toast } from 'react-toastify';
import { DataTable, LoadingSpinner, ErrorAlert, EmptyState, SearchInput, ConfirmDialog, Column } from '@/components/common';
import { useIAM } from '@/hooks/useIAM';
import { iamApi } from '@/api/iam';
import { ServiceAccount } from '@/types/iam';

export default function ServiceAccountList() {
  
  const queryClient = useQueryClient();
  const { listServiceAccounts } = useIAM();
  const [searchQuery, setSearchQuery] = useState('');
  const [deleteDialogOpen, setDeleteDialogOpen] = useState(false);
  const [saToDelete, setSaToDelete] = useState<string | null>(null);

  const deleteMutation = useMutation({
    mutationFn: (name: string) => iamApi.deleteServiceAccount(name),
    onSuccess: () => { queryClient.invalidateQueries({ queryKey: ['serviceAccounts'] }); toast.success('Service account deleted'); setDeleteDialogOpen(false); },
    onError: (error: any) => toast.error(error?.response?.data?.error?.message || 'Failed to delete'),
  });

  const filteredSAs = (listServiceAccounts.data || []).filter((sa: ServiceAccount) =>
    sa.email.toLowerCase().includes(searchQuery.toLowerCase())
  );

  const columns: Column<ServiceAccount>[] = [
    { id: 'displayName', label: 'Display Name', minWidth: 200, format: (value) => value || 'N/A' },
    { id: 'email', label: 'Email', minWidth: 300 },
    { id: 'uniqueId', label: 'Unique ID', minWidth: 150 },
    {
      id: 'actions', label: 'Actions', minWidth: 120, align: 'right', sortable: false,
      format: (_, sa) => (
        <IconButton size="small" color="error" onClick={(e) => { e.stopPropagation(); setSaToDelete(sa.name); setDeleteDialogOpen(true); }}><DeleteIcon /></IconButton>
      ),
    },
  ];

  if (listServiceAccounts.isLoading) return <LoadingSpinner />;
  if (listServiceAccounts.isError) return <ErrorAlert error={listServiceAccounts.error} onRetry={() => listServiceAccounts.refetch()} />;

  return (
    <Box>
      <Box sx={{ display: 'flex', justifyContent: 'space-between', mb: 3 }}>
        <Typography variant="h4">Service Accounts</Typography>
      </Box>
      <SearchInput onSearch={setSearchQuery} placeholder="Search service accounts..." />
      <Box sx={{ mt: 2 }}>
        {filteredSAs.length === 0 ? <EmptyState message="No service accounts found" /> : <DataTable columns={columns} rows={filteredSAs} getRowId={(row) => row.email} />}
      </Box>
      <ConfirmDialog open={deleteDialogOpen} onClose={() => setDeleteDialogOpen(false)} onConfirm={() => saToDelete && deleteMutation.mutate(saToDelete)} title="Delete Service Account" message="Are you sure?" danger loading={deleteMutation.isPending} />
    </Box>
  );
}
