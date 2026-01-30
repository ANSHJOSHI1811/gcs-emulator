import { createBrowserRouter, Navigate } from 'react-router-dom';
import Layout from './layouts/Layout';
import Dashboard from './pages/Dashboard';
import BucketList from './pages/storage/BucketList';
import BucketDetails from './pages/storage/BucketDetails';
import InstanceList from './pages/compute/InstanceList';
import CreateInstance from './pages/compute/CreateInstance';
import InstanceDetails from './pages/compute/InstanceDetails';
import NetworkList from './pages/vpc/NetworkList';
import NetworkDetails from './pages/vpc/NetworkDetails';
import CreateFirewall from './pages/vpc/CreateFirewall';
import ServiceAccountList from './pages/iam/ServiceAccountList';
import ServiceAccountDetails from './pages/iam/ServiceAccountDetails';
import IAMPolicies from './pages/iam/IAMPolicies';
import Roles from './pages/iam/Roles';

export const router = createBrowserRouter([
  {
    path: '/',
    element: <Layout />,
    children: [
      {
        index: true,
        element: <Dashboard />,
      },
      {
        path: 'storage',
        children: [
          { index: true, element: <BucketList /> },
          { path: ':bucketName', element: <BucketDetails /> },
        ],
      },
      {
        path: 'compute',
        children: [
          { path: 'instances', element: <InstanceList /> },
          { path: 'instances/create', element: <CreateInstance /> },
          { path: 'instances/:zone/:name', element: <InstanceDetails /> },
        ],
      },
      {
        path: 'vpc',
        children: [
          { path: 'networks', element: <NetworkList /> },
          { path: 'networks/:name', element: <NetworkDetails /> },
          { path: 'firewalls/create', element: <CreateFirewall /> },
        ],
      },
      {
        path: 'iam',
        children: [
          { path: 'serviceaccounts', element: <ServiceAccountList /> },
          { path: 'serviceaccounts/:email', element: <ServiceAccountDetails /> },
          { path: 'policies', element: <IAMPolicies /> },
          { path: 'roles', element: <Roles /> },
        ],
      },
      {
        path: '*',
        element: <Navigate to="/" replace />,
      },
    ],
  },
]);
