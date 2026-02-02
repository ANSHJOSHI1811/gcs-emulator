import { apiClient } from './client';
import { ListEventsResponse, ObjectEvent } from '../types';

// Phase 4: Object Events API
export async function listEvents(bucketName?: string): Promise<ObjectEvent[]> {
  const url = bucketName 
    ? `/internal/events?bucket=${bucketName}` 
    : '/internal/events';
  
  const response = await apiClient.get<ListEventsResponse>(url);
  return response.data.items || [];
}
