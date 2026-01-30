import { Alert, AlertTitle, Button } from '@mui/material';
import RefreshIcon from '@mui/icons-material/Refresh';

interface ErrorAlertProps {
  error: any;
  onRetry?: () => void;
  title?: string;
}

export default function ErrorAlert({ error, onRetry, title = 'Error' }: ErrorAlertProps) {
  const errorMessage = error?.response?.data?.error?.message || error?.message || 'An unexpected error occurred';

  return (
    <Alert 
      severity="error"
      action={
        onRetry && (
          <Button
            color="inherit"
            size="small"
            startIcon={<RefreshIcon />}
            onClick={onRetry}
          >
            Retry
          </Button>
        )
      }
    >
      <AlertTitle>{title}</AlertTitle>
      {errorMessage}
    </Alert>
  );
}
