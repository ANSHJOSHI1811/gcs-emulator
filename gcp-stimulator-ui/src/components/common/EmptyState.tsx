import { Box, Typography } from '@mui/material';
import FolderOffIcon from '@mui/icons-material/FolderOff';

interface EmptyStateProps {
  message?: string;
  description?: string;
  icon?: React.ReactNode;
  action?: React.ReactNode;
}

export default function EmptyState({
  message = 'No items found',
  description,
  icon,
  action,
}: EmptyStateProps) {
  return (
    <Box
      display="flex"
      flexDirection="column"
      alignItems="center"
      justifyContent="center"
      minHeight="300px"
      gap={2}
      p={4}
    >
      {icon || <FolderOffIcon sx={{ fontSize: 64, color: 'text.disabled' }} />}
      <Typography variant="h6" color="text.secondary">
        {message}
      </Typography>
      {description && (
        <Typography variant="body2" color="text.disabled" textAlign="center">
          {description}
        </Typography>
      )}
      {action && <Box mt={2}>{action}</Box>}
    </Box>
  );
}
