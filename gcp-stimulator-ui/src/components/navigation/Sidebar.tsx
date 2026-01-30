import {
  Drawer,
  List,
  ListItem,
  ListItemButton,
  ListItemIcon,
  ListItemText,
  Divider,
  Typography,
  Box,
  Collapse,
} from '@mui/material';
import { Link, useLocation } from 'react-router-dom';
import { useState } from 'react';

// Icons
import DashboardIcon from '@mui/icons-material/Dashboard';
import StorageIcon from '@mui/icons-material/Storage';
import ComputerIcon from '@mui/icons-material/Computer';
import NetworkCheckIcon from '@mui/icons-material/NetworkCheck';
import SecurityIcon from '@mui/icons-material/Security';
import ExpandLess from '@mui/icons-material/ExpandLess';
import ExpandMore from '@mui/icons-material/ExpandMore';

const DRAWER_WIDTH = 260;

interface NavItem {
  label: string;
  icon: React.ReactNode;
  path?: string;
  children?: { label: string; path: string }[];
}

const NAV_ITEMS: NavItem[] = [
  {
    label: 'Dashboard',
    icon: <DashboardIcon />,
    path: '/',
  },
  {
    label: 'Storage',
    icon: <StorageIcon />,
    children: [
      { label: 'Buckets', path: '/storage/buckets' },
    ],
  },
  {
    label: 'Compute Engine',
    icon: <ComputerIcon />,
    children: [
      { label: 'VM Instances', path: '/compute/instances' },
      { label: 'Create Instance', path: '/compute/create' },
    ],
  },
  {
    label: 'VPC Network',
    icon: <NetworkCheckIcon />,
    children: [
      { label: 'VPC Networks', path: '/vpc/networks' },
      { label: 'Firewall Rules', path: '/vpc/firewall' },
    ],
  },
  {
    label: 'IAM & Admin',
    icon: <SecurityIcon />,
    children: [
      { label: 'Service Accounts', path: '/iam/service-accounts' },
      { label: 'IAM Policies', path: '/iam/policies' },
      { label: 'Roles', path: '/iam/roles' },
    ],
  },
];

export default function Sidebar() {
  const location = useLocation();
  const [openSections, setOpenSections] = useState<Record<string, boolean>>({
    Storage: true,
    'Compute Engine': true,
    'VPC Network': true,
    'IAM & Admin': true,
  });

  const handleToggle = (label: string) => {
    setOpenSections((prev) => ({
      ...prev,
      [label]: !prev[label],
    }));
  };

  const isActive = (path: string) => location.pathname === path;

  return (
    <Drawer
      variant="permanent"
      sx={{
        width: DRAWER_WIDTH,
        flexShrink: 0,
        '& .MuiDrawer-paper': {
          width: DRAWER_WIDTH,
          boxSizing: 'border-box',
          top: 64, // Below AppBar
          height: 'calc(100% - 64px)',
          borderRight: '1px solid',
          borderColor: 'divider',
        },
      }}
    >
      <Box sx={{ p: 2 }}>
        <Typography variant="overline" color="text.secondary" sx={{ fontWeight: 600 }}>
          Navigation
        </Typography>
      </Box>
      <Divider />
      <List>
        {NAV_ITEMS.map((item) => (
          <div key={item.label}>
            {item.path ? (
              <ListItem disablePadding>
                <ListItemButton
                  component={Link}
                  to={item.path}
                  selected={isActive(item.path)}
                >
                  <ListItemIcon>{item.icon}</ListItemIcon>
                  <ListItemText primary={item.label} />
                </ListItemButton>
              </ListItem>
            ) : (
              <>
                <ListItemButton onClick={() => handleToggle(item.label)}>
                  <ListItemIcon>{item.icon}</ListItemIcon>
                  <ListItemText primary={item.label} />
                  {openSections[item.label] ? <ExpandLess /> : <ExpandMore />}
                </ListItemButton>
                <Collapse in={openSections[item.label]} timeout="auto" unmountOnExit>
                  <List component="div" disablePadding>
                    {item.children?.map((child) => (
                      <ListItemButton
                        key={child.path}
                        component={Link}
                        to={child.path}
                        selected={isActive(child.path)}
                        sx={{ pl: 4 }}
                      >
                        <ListItemText primary={child.label} />
                      </ListItemButton>
                    ))}
                  </List>
                </Collapse>
              </>
            )}
          </div>
        ))}
      </List>
    </Drawer>
  );
}
