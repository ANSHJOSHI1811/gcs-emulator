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
  metageneration?: string;
  size: number;
  updated: string;
  contentType: string;
  md5Hash?: string;
  crc32c?: string;
  storageClass?: string;
  acl?: ACLValue;
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

export interface UploadResponse {
  kind?: string;
  name: string;
  bucket: string;
  generation?: string;
  size?: number;
  metageneration?: string;
  sessionId?: string; // For resumable uploads
  Location?: string; // For resumable uploads
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

// Phase 4: ACL Types
export type ACLValue = 'private' | 'publicRead';

export interface ACLResponse {
  kind: string;
  bucket?: string;
  object?: string;
  acl: ACLValue;
}

// Phase 4: Object Event Types
export interface ObjectEvent {
  event_id: string;
  bucket_name: string;
  object_name: string;
  event_type: 'OBJECT_FINALIZE' | 'OBJECT_DELETE' | 'OBJECT_METADATA_UPDATE';
  generation: number;
  timestamp: string;
  delivered: boolean;
  metadata_json?: string;
}

export interface ListEventsResponse {
  kind: string;
  items?: ObjectEvent[];
}

// Phase 4: Lifecycle Rule Types
export interface LifecycleRule {
  ruleId: string;
  bucket: string;
  action: 'Delete' | 'Archive';
  ageDays: number;
  createdAt: string;
}

export interface CreateLifecycleRuleRequest {
  bucket: string;
  action: 'Delete' | 'Archive';
  ageDays: number;
}

export interface LifecycleRulesResponse {
  kind: string;
  items: LifecycleRule[];
}

// Phase 4: Object Metadata with Storage Class
export interface ObjectMetadata {
  name: string;
  bucket: string;
  generation: string;
  metageneration: string;
  size: number;
  updated: string;
  contentType: string;
  md5Hash?: string;
  crc32c?: string;
  storageClass?: 'STANDARD' | 'ARCHIVE';
  acl?: ACLValue;
}
