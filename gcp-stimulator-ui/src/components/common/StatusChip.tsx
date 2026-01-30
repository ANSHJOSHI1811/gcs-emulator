import { Chip } from '@mui/material';

interface StatusChipProps {
  status: string;
  size?: 'small' | 'medium';
}

const STATUS_CONFIG: Record<string, { color: any; label: string }> = {
  // Compute statuses
  RUNNING: { color: 'success', label: 'Running' },
  STOPPED: { color: 'default', label: 'Stopped' },
  TERMINATED: { color: 'error', label: 'Terminated' },
  PROVISIONING: { color: 'info', label: 'Provisioning' },
  STAGING: { color: 'info', label: 'Staging' },
  STOPPING: { color: 'warning', label: 'Stopping' },
  SUSPENDING: { color: 'warning', label: 'Suspending' },
  SUSPENDED: { color: 'warning', label: 'Suspended' },
  
  // Operation statuses
  PENDING: { color: 'warning', label: 'Pending' },
  DONE: { color: 'success', label: 'Done' },
  
  // General statuses
  ACTIVE: { color: 'success', label: 'Active' },
  INACTIVE: { color: 'default', label: 'Inactive' },
  ERROR: { color: 'error', label: 'Error' },
  UP: { color: 'success', label: 'Up' },
  DOWN: { color: 'error', label: 'Down' },
};

export default function StatusChip({ status, size = 'small' }: StatusChipProps) {
  const config = STATUS_CONFIG[status] || { color: 'default', label: status };

  return (
    <Chip
      label={config.label}
      color={config.color}
      size={size}
      sx={{ fontWeight: 500 }}
    />
  );
}
