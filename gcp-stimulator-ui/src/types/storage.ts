export interface Bucket {
  id: string;
  name: string;
  location: string;
  storageClass: string;
  projectNumber: string;
  timeCreated: string;
  updated: string;
  versioning?: {
    enabled: boolean;
  };
  lifecycle?: {
    rule: LifecycleRule[];
  };
  cors?: CorsConfig[];
  labels?: Record<string, string>;
  iamConfiguration?: {
    uniformBucketLevelAccess?: {
      enabled: boolean;
      lockedTime?: string;
    };
  };
}

export interface LifecycleRule {
  action: {
    type: string;
    storageClass?: string;
  };
  condition: {
    age?: number;
    createdBefore?: string;
    isLive?: boolean;
    matchesStorageClass?: string[];
    numNewerVersions?: number;
  };
}

export interface CorsConfig {
  origin: string[];
  method: string[];
  responseHeader?: string[];
  maxAgeSeconds?: number;
}

export interface StorageObject {
  id: string;
  name: string;
  bucket: string;
  size: string;
  timeCreated: string;
  updated: string;
  contentType?: string;
  md5Hash?: string;
  crc32c?: string;
  etag?: string;
  generation?: string;
  metageneration?: string;
  storageClass?: string;
  metadata?: Record<string, string>;
}

export interface BucketIamPolicy {
  bindings: IamBinding[];
  etag?: string;
  version?: number;
}

export interface IamBinding {
  role: string;
  members: string[];
  condition?: {
    expression: string;
    title: string;
    description?: string;
  };
}

export interface CreateBucketRequest {
  name: string;
  location?: string;
  storageClass?: string;
  versioning?: {
    enabled: boolean;
  };
  labels?: Record<string, string>;
}

export interface UploadObjectRequest {
  name: string;
  bucket: string;
  file: File;
  contentType?: string;
  metadata?: Record<string, string>;
}
