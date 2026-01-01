import { Instance } from '../types/compute';

const API_BASE_URL = 'http://localhost:8080';

export const createInstance = async (data: {
  name: string;
  image: string;
  cpu?: number;
  memory_mb?: number;
}): Promise<Instance> => {
  const response = await fetch(`${API_BASE_URL}/compute/instances`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify(data),
  });

  if (!response.ok) {
    const error = await response.json().catch(() => ({ message: 'Failed to create instance' }));
    throw new Error(error.message || 'Failed to create instance');
  }

  return response.json();
};

export const getInstances = async (): Promise<Instance[]> => {
  const response = await fetch(`${API_BASE_URL}/compute/instances`);
  if (!response.ok) {
    throw new Error('Failed to fetch instances');
  }
  const data = await response.json();
  console.log('API Response:', data);
  console.log('Instances count:', data.count);
  console.log('Instances array length:', data.instances?.length);
  return data.instances || [];
};

export const startInstance = async (instanceId: string): Promise<any> => {
  const response = await fetch(`${API_BASE_URL}/compute/instances/${instanceId}/start`, {
    method: 'POST',
  });
  if (!response.ok) {
    throw new Error('Failed to start instance');
  }
  return response.json();
};

export const stopInstance = async (instanceId: string): Promise<any> => {
  const response = await fetch(`${API_BASE_URL}/compute/instances/${instanceId}/stop`, {
    method: 'POST',
  });
  if (!response.ok) {
    throw new Error('Failed to stop instance');
  }
  return response.json();
};

export const terminateInstance = async (instanceId: string): Promise<any> => {
  const response = await fetch(`${API_BASE_URL}/compute/instances/${instanceId}/terminate`, {
    method: 'POST',
  });
  if (!response.ok) {
    throw new Error('Failed to terminate instance');
  }
  return response.json();
};
