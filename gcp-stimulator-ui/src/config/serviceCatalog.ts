import { LucideIcon, HardDrive, Cpu, Network, Shield, MessageSquare, Activity, Globe, Lock, Route, TableIcon, Box, Server, Layers } from 'lucide-react';

export interface ServiceLink {
  label: string;
  path: string;
  icon?: LucideIcon;
}

export interface Service {
  id: string;
  name: string;
  description: string;
  icon: LucideIcon;
  category: string;
  enabled: boolean;
  sidebarLinks?: ServiceLink[];
}

export interface ServiceCategory {
  id: string;
  name: string;
  services: Service[];
}

export const serviceCategories: ServiceCategory[] = [
  {
    id: 'storage',
    name: 'Storage',
    services: [
      {
        id: 'storage',
        name: 'Cloud Storage',
        description: 'Object storage for companies of all sizes',
        icon: HardDrive,
        category: 'Storage',
        enabled: true,
        sidebarLinks: [
          { label: 'Dashboard', path: '/services/storage' },
          { label: 'Buckets', path: '/services/storage/buckets', icon: HardDrive },
          { label: 'Activity', path: '/services/storage/activity', icon: Activity },
          { label: 'Settings', path: '/services/storage/settings' },
        ],
      },
    ],
  },
  {
    id: 'compute',
    name: 'Compute',
    services: [
      {
        id: 'compute-engine',
        name: 'Compute Engine',
        description: 'Virtual machines running in Google\'s data center',
        icon: Cpu,
        category: 'Compute',
        enabled: true,
        sidebarLinks: [
          { label: 'VM Instances', path: '/services/compute-engine/instances', icon: Cpu },
        ],
      },
    ],
  },
  {
    id: 'networking',
    name: 'Networking',
    services: [
      {
        id: 'vpc',
        name: 'VPC Network',
        description: 'Virtual Private Cloud and networking',
        icon: Network,
        category: 'Networking',
        enabled: true,
        sidebarLinks: [
          { label: 'VPC Networks', path: '/services/vpc/networks', icon: Globe },
          { label: 'Subnets', path: '/services/vpc/subnets', icon: Network },
          { label: 'Firewall Rules', path: '/services/vpc/firewalls', icon: Lock },
          { label: 'Routes', path: '/services/vpc/routes', icon: Route },
        ],
      },
    ],
  },
  {
    id: 'iam',
    name: 'IAM & Admin',
    services: [
      {
        id: 'iam',
        name: 'IAM',
        description: 'Identity and Access Management',
        icon: Shield,
        category: 'IAM & Admin',
        enabled: true,
        sidebarLinks: [
          { label: 'Dashboard', path: '/services/iam' },
          { label: 'Service Accounts', path: '/services/iam/service-accounts', icon: Shield },
          { label: 'IAM Policies', path: '/services/iam/policies' },
        ],
      },
    ],
  },
  {
    id: 'containers',
    name: 'Containers',
    services: [
      {
        id: 'gke',
        name: 'Kubernetes Engine',
        description: 'Managed Kubernetes service for containerised workloads',
        icon: Box,
        category: 'Containers',
        enabled: true,
        sidebarLinks: [
          { label: 'Clusters', path: '/services/gke/clusters', icon: Server },
          { label: 'Node Pools', path: '/services/gke/node-pools', icon: Layers },
        ],
      },
    ],
  },
  {
    id: 'messaging',
    name: 'Messaging',
    services: [
      {
        id: 'pubsub',
        name: 'Pub/Sub',
        description: 'Messaging and ingestion for event-driven systems',
        icon: MessageSquare,
        category: 'Messaging',
        enabled: false,
      },
    ],
  },
  {
    id: 'monitoring',
    name: 'Monitoring',
    services: [
      {
        id: 'monitoring',
        name: 'Monitoring',
        description: 'Monitor your Google Cloud and AWS resources',
        icon: Activity,
        category: 'Monitoring',
        enabled: false,
      },
    ],
  },
];

export const getAllServices = (): Service[] => {
  return serviceCategories.flatMap(category => category.services);
};

export const getServiceById = (serviceId: string): Service | undefined => {
  return getAllServices().find(service => service.id === serviceId);
};
