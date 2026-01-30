export interface Instance {
  id: string;
  name: string;
  machineType: string;
  status: InstanceStatus;
  zone: string;
  creationTimestamp: string;
  disks: AttachedDisk[];
  networkInterfaces?: NetworkInterface[];
  serviceAccounts?: ServiceAccountInfo[];
  metadata?: Metadata;
  tags?: Tags;
  labels?: Record<string, string>;
  selfLink?: string;
  description?: string;
  canIpForward?: boolean;
  scheduling?: Scheduling;
  _stimulator?: {
    containerId?: string | null;
    containerName?: string | null;
  };
}

export type InstanceStatus = 
  | 'PROVISIONING'
  | 'STAGING'
  | 'RUNNING'
  | 'STOPPING'
  | 'STOPPED'
  | 'SUSPENDING'
  | 'SUSPENDED'
  | 'TERMINATED';

export interface AttachedDisk {
  type?: string;
  boot: boolean;
  deviceName?: string;
  source?: string;
  autoDelete?: boolean;
  diskSizeGb?: string;
  initializeParams?: {
    diskName?: string;
    diskSizeGb?: string;
    diskType?: string;
    sourceImage?: string;
  };
}

export interface NetworkInterface {
  network: string;
  subnetwork?: string;
  networkIP?: string;
  name?: string;
  accessConfigs?: AccessConfig[];
  aliasIpRanges?: AliasIpRange[];
}

export interface AccessConfig {
  type: string;
  name: string;
  natIP?: string;
}

export interface AliasIpRange {
  ipCidrRange: string;
  subnetworkRangeName?: string;
}

export interface ServiceAccountInfo {
  email: string;
  scopes: string[];
}

export interface Metadata {
  items?: MetadataItem[];
  fingerprint?: string;
}

export interface MetadataItem {
  key: string;
  value: string;
}

export interface Tags {
  items?: string[];
  fingerprint?: string;
}

export interface Scheduling {
  onHostMaintenance?: string;
  automaticRestart?: boolean;
  preemptible?: boolean;
}

export interface MachineType {
  id: string;
  name: string;
  guestCpus: number;
  memoryMb: number;
  zone: string;
  description?: string;
  maximumPersistentDisks?: number;
  maximumPersistentDisksSizeGb?: string;
  selfLink?: string;
}

export interface Zone {
  id: string;
  name: string;
  description?: string;
  status: string;
  region: string;
  selfLink?: string;
}

export interface Region {
  id: string;
  name: string;
  description?: string;
  status: string;
  zones?: string[];
  selfLink?: string;
}

export interface Disk {
  id: string;
  name: string;
  zone: string;
  status: string;
  sizeGb: string;
  type: string;
  sourceImage?: string;
  sourceImageId?: string;
  creationTimestamp: string;
  description?: string;
  labels?: Record<string, string>;
  selfLink?: string;
}

export interface CreateInstanceRequest {
  name: string;
  machineType: string;
  zone: string;
  disks: AttachedDisk[];
  networkInterfaces: NetworkInterface[];
  serviceAccounts?: ServiceAccountInfo[];
  metadata?: Metadata;
  tags?: Tags;
  labels?: Record<string, string>;
  description?: string;
  scheduling?: Scheduling;
}
