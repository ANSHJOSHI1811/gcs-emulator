export interface ComputeInstance {
  id: string;
  name: string;
  projectId: string;
  zone: string;
  machineType: string;
  status: 'PROVISIONING' | 'STAGING' | 'RUNNING' | 'STOPPING' | 'TERMINATED';
  statusMessage?: string;
  containerId?: string;
  creationTimestamp: string;
  lastStartTimestamp?: string;
  lastStopTimestamp?: string;
  metadata?: Record<string, string>;
  labels?: Record<string, string>;
  tags?: string[];
  networkInterfaces?: any[];
  disks?: any[];
}

export interface ComputeInstanceCreate {
  name: string;
  machineType: string;
  metadata?: Record<string, string>;
  labels?: Record<string, string>;
  tags?: string[];
}

export interface MachineType {
  name: string;
  description: string;
  guestCpus: number;
  memoryMb: number;
  zone: string;
}
