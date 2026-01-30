import apiClient from './client';

export const storageApi = {
  // Buckets
  listBuckets: (project: string) =>
    apiClient.get(`/storage/v1/b`, { params: { project } }),
  
  getBucket: (bucket: string) =>
    apiClient.get(`/storage/v1/b/${bucket}`),
  
  createBucket: (project: string, data: any) =>
    apiClient.post(`/storage/v1/b`, data, { params: { project } }),
  
  deleteBucket: (bucket: string) =>
    apiClient.delete(`/storage/v1/b/${bucket}`),
  
  updateBucket: (bucket: string, data: any) =>
    apiClient.patch(`/storage/v1/b/${bucket}`, data),
  
  // Objects
  listObjects: (bucket: string, prefix?: string, delimiter?: string) =>
    apiClient.get(`/storage/v1/b/${bucket}/o`, { 
      params: { prefix, delimiter } 
    }),
  
  getObject: (bucket: string, object: string) =>
    apiClient.get(`/storage/v1/b/${bucket}/o/${encodeURIComponent(object)}`),
  
  uploadObject: (bucket: string, file: File, name?: string) => {
    const formData = new FormData();
    formData.append('file', file);
    if (name) formData.append('name', name);
    return apiClient.post(`/storage/v1/b/${bucket}/o`, formData, {
      headers: { 'Content-Type': 'multipart/form-data' }
    });
  },
  
  deleteObject: (bucket: string, object: string) =>
    apiClient.delete(`/storage/v1/b/${bucket}/o/${encodeURIComponent(object)}`),
  
  copyObject: (sourceBucket: string, sourceObject: string, destBucket: string, destObject: string) =>
    apiClient.post(
      `/storage/v1/b/${sourceBucket}/o/${encodeURIComponent(sourceObject)}/copyTo/b/${destBucket}/o/${encodeURIComponent(destObject)}`
    ),
  
  // IAM Permissions
  getBucketIamPolicy: (bucket: string) =>
    apiClient.get(`/storage/v1/b/${bucket}/iam`),
  
  setBucketIamPolicy: (bucket: string, policy: any) =>
    apiClient.put(`/storage/v1/b/${bucket}/iam`, policy),
};
