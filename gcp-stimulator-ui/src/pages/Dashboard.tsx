import { Box, Typography, Grid, Paper } from '@mui/material';
import StorageIcon from '@mui/icons-material/Storage';
import ComputerIcon from '@mui/icons-material/Computer';
import NetworkCheckIcon from '@mui/icons-material/NetworkCheck';
import SecurityIcon from '@mui/icons-material/Security';
import { useProjectStore } from '@/stores/projectStore';
import { useStorage } from '@/hooks/useStorage';
import { useCompute } from '@/hooks/useCompute';
import { useVPC } from '@/hooks/useVPC';
import { useIAM } from '@/hooks/useIAM';
import { useNavigate } from 'react-router-dom';

export default function Dashboard() {
  const navigate = useNavigate();
  const { selectedProject } = useProjectStore();
  const { listBuckets } = useStorage();
  const { listInstances } = useCompute();
  const instances = listInstances('us-central1-a');
  const { listNetworks } = useVPC();
  const { listServiceAccounts } = useIAM();

  const resources = [
    { name: 'Storage Buckets', count: listBuckets.data?.length || 0, icon: <StorageIcon sx={{ fontSize: 48 }} />, color: '#4285F4', path: '/storage/buckets' },
    { name: 'VM Instances', count: instances.data?.length || 0, icon: <ComputerIcon sx={{ fontSize: 48 }} />, color: '#EA4335', path: '/compute/instances' },
    { name: 'VPC Networks', count: listNetworks.data?.length || 0, icon: <NetworkCheckIcon sx={{ fontSize: 48 }} />, color: '#FBBC04', path: '/vpc/networks' },
    { name: 'Service Accounts', count: listServiceAccounts.data?.length || 0, icon: <SecurityIcon sx={{ fontSize: 48 }} />, color: '#34A853', path: '/iam/service-accounts' },
  ];

  return (
    <Box>
      <Typography variant="h4" gutterBottom>Dashboard</Typography>
      <Typography variant="body1" color="text.secondary" gutterBottom>
        Project: {selectedProject || 'No project selected'}
      </Typography>
      <Grid container spacing={3} sx={{ mt: 2 }}>
        {resources.map((resource) => (
          <Grid item xs={12} sm={6} md={3} key={resource.name}>
            <Paper sx={{ p: 3, display: 'flex', flexDirection: 'column', alignItems: 'center', gap: 2, borderTop: `4px solid ${resource.color}`, cursor: 'pointer', '&:hover': { transform: 'translateY(-4px)', boxShadow: 4 } }} onClick={() => navigate(resource.path)}>
              <Box sx={{ color: resource.color }}>{resource.icon}</Box>
              <Typography variant="h3" fontWeight="bold">{resource.count}</Typography>
              <Typography variant="body2" color="text.secondary">{resource.name}</Typography>
            </Paper>
          </Grid>
        ))}
      </Grid>
    </Box>
  );
}
