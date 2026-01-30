// Central export file for all types
export * from './storage';
export * from './compute';
export * from './vpc';
export type { ServiceAccount, ServiceAccountKey, IamPolicy, Role } from './iam';

// Common API response types
export interface ApiResponse<T> {
  data: T;
  status: number;
  statusText: string;
}

export interface ListResponse<T> {
  items: T[];
  nextPageToken?: string;
  kind?: string;
}

export interface ApiError {
  error: {
    code: number;
    message: string;
    errors?: Array<{
      domain: string;
      reason: string;
      message: string;
    }>;
  };
}

export interface Operation {
  id: string;
  name: string;
  operationType: string;
  targetId?: string;
  targetLink?: string;
  status: 'PENDING' | 'RUNNING' | 'DONE';
  progress?: number;
  insertTime: string;
  startTime?: string;
  endTime?: string;
  error?: {
    errors: Array<{
      code: string;
      message: string;
    }>;
  };
  warnings?: Array<{
    code: string;
    message: string;
  }>;
  user?: string;
  region?: string;
  zone?: string;
}

// Common query/filter types
export interface ListOptions {
  pageToken?: string;
  maxResults?: number;
  filter?: string;
  orderBy?: string;
}

export interface PaginationInfo {
  currentPage: number;
  pageSize: number;
  totalItems: number;
  totalPages: number;
}
