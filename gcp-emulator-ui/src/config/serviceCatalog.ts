import { LucideIcon, HardDrive, Cpu, Network, Shield, MessageSquare, Activity } from 'lucide-react';

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
        id: 'compute',
        name: 'Compute Engine',
        description: 'Virtual machines running in Docker containers',
        icon: Cpu,
        category: 'Compute',
        enabled: true,
        sidebarLinks: [
          { label: 'Instances', path: '/services/compute/instances', icon: Cpu },
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
        enabled: false,
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
          { label: 'Service Accounts', path: '/services/iam/service-accounts', icon: Shield },
          { label: 'Roles', path: '/services/iam/roles' },
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
