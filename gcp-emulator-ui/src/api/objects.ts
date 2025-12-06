import { apiClient, PROJECT_ID } from './client';
import { GCSObject, ACLResponse, ACLValue } from '../types';

interface BackendObject {
  name: string;
  size: string;
  contentType: string;
  updated: string;
  generation: string;
}

interface ListObjectsResponse {
  items?: BackendObject[];
}

export async function listObjects(bucketName: string): Promise<GCSObject[]> {
  const response = await apiClient.get<ListObjectsResponse>(`/storage/v1/b/${bucketName}/o?project=${PROJECT_ID}`);
  if (!response.data.items) {
    return [];
  }
  return response.data.items.map((item) => ({
    ...item,
    bucket: bucketName,
    size: parseInt(item.size, 10),
  }));
}

export async function downloadObject(bucketName: string, objectName: string, generation?: string): Promise<Blob> {
  const encodedObjectName = encodeURIComponent(objectName);
  let url = `/storage/v1/b/${bucketName}/o/${encodedObjectName}?alt=media&project=${PROJECT_ID}`;
  if (generation) {
    url += `&generation=${generation}`;
  }
  const response = await apiClient.get(url, {
    responseType: 'blob',
  });
  return response.data;
}

export async function deleteObject(bucketName: string, objectName: string, generation?: string): Promise<void> {
  const encodedObjectName = encodeURIComponent(objectName);
  let url = `/storage/v1/b/${bucketName}/o/${encodedObjectName}?project=${PROJECT_ID}`;
  if (generation) {
    url += `&generation=${generation}`;
  }
  await apiClient.delete(url);
}

// Phase 4: Object ACL Management
export async function getObjectACL(bucketName: string, objectName: string): Promise<ACLValue> {
  const encodedObjectName = encodeURIComponent(objectName);
  const response = await apiClient.get<ACLResponse>(
    `/storage/v1/b/${bucketName}/o/${encodedObjectName}/acl`
  );
  return response.data.acl;
}

export async function updateObjectACL(bucketName: string, objectName: string, acl: ACLValue): Promise<ACLValue> {
  const encodedObjectName = encodeURIComponent(objectName);
  const response = await apiClient.patch<ACLResponse>(
    `/storage/v1/b/${bucketName}/o/${encodedObjectName}/acl`,
    { acl }
  );
  return response.data.acl;
}
