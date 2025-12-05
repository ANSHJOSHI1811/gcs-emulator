// Bucket Types
export interface Bucket {
  name: string;
  location: string;
  storageClass: string;
  timeCreated: string; // ISO string
  updated?: string;
  objectCount?: number;
}

export interface CreateBucketRequest {
  name: string;
  location: string;
  storageClass?: string;
  project: string;
}

// Object Types
export interface GCSObject {
  name: string;
  bucket: string;
  generation: string;
  size: number;
  updated: string;
  contentType: string;
}

export interface ObjectVersion {
  name: string;
  generation: string;
  metageneration?: string;
  size?: number;
  updated: string;
  isLatest?: boolean;
}

// API Response Types
export interface ListBucketsResponse {
  kind: string;
  items: Bucket[];
}

export interface ListObjectsResponse {
  kind: string;
  items: GCSObject[];
  prefixes?: string[];
}

export interface ApiError {
  message: string;
  code?: string;
  details?: any;
}

export interface UploadProgress {
  loaded: number;
  total: number;
  percentage: number;
}

export interface UploadResponse {
  name: string;
  bucket: string;
  size?: number;
  generation?: string;
  metageneration?: string;
}
