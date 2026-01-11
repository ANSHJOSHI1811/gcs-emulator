export interface Instance {
  id: string;
  name: string;
  zone?: string;
  machine_type?: string;
  state: string;
  labels?: Record<string, string>;
  metadata?: Record<string, string>;
  description?: string;
  created_at: string;
  updated_at: string;
  // Backend fields
  container_id: string | null;
  cpu: number;
  memory_mb: number;
  image: string;
  project_id: string;
}

export interface Operation {
  id: string;
  type: 'start' | 'stop' | 'delete';
  status: 'PENDING' | 'RUNNING' | 'DONE';
  resource_id: string;
  resource_type: 'instance';
  created_at: string;
  updated_at: string;
}
