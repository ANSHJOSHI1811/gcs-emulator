import { Outlet } from 'react-router-dom';
import { Box, AppBar, Toolbar, Typography } from '@mui/material';
import CloudIcon from '@mui/icons-material/Cloud';
import Sidebar from '@/components/navigation/Sidebar';
import ProjectSelector from '@/components/navigation/ProjectSelector';

const DRAWER_WIDTH = 260;

export default function Layout() {
  return (
    <Box sx={{ display: 'flex', minHeight: '100vh' }}>
      <AppBar position="fixed" sx={{ zIndex: (theme) => theme.zIndex.drawer + 1 }}>
        <Toolbar>
          <CloudIcon sx={{ mr: 2 }} />
          <Typography variant="h6" component="div" sx={{ flexGrow: 1 }}>
            GCP Stimulator Console
          </Typography>
          <ProjectSelector />
        </Toolbar>
      </AppBar>
      
      <Sidebar />
      
      <Box
        component="main"
        sx={{
          flexGrow: 1,
          p: 3,
          mt: 8,
          ml: `${DRAWER_WIDTH}px`,
          minHeight: '100vh',
          bgcolor: 'background.default',
        }}
      >
        <Outlet />
      </Box>
    </Box>
  );
}
