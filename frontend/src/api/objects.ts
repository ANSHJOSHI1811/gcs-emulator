import apiClient from './client';
import { GCSObject } from '../types';

interface ListObjectsResponse {
  items?: any[];
}

export async function listObjects(bucketName: string): Promise<GCSObject[]> {
  const response = await apiClient.get<ListObjectsResponse>(`/storage/v1/b/${bucketName}/o`);
  if (!response.data.items) {
    return [];
  }
  // TODO: The backend response shape is not fully known.
  // Mapping known fields and leaving others as placeholders.
  return response.data.items.map((item: any) => ({
    name: item.name,
    size: parseInt(item.size, 10),
    contentType: item.contentType,
    updated: item.updated,
    generation: item.generation,
  }));
}

export async function downloadObject(bucketName: string, objectName: string, generation?: string): Promise<Blob> {
  let url = `/storage/v1/b/${bucketName}/o/${objectName}?alt=media`;
  if (generation) {
    url += `&generation=${generation}`;
  }
  const response = await apiClient.get(url, {
    responseType: 'blob',
  });
  return response.data;
}

export async function deleteObject(bucketName: string, objectName: string, generation?: string): Promise<void> {
  let url = `/storage/v1/b/${bucketName}/o/${objectName}`;
  if (generation) {
    url += `?generation=${generation}`;
  }
  await apiClient.delete(url);
}
