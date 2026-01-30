export interface ServiceAccount {
  name: string;
  email: string;
  projectId: string;
  uniqueId: string;
  displayName?: string;
  description?: string;
  disabled?: boolean;
  oauth2ClientId?: string;
}

export interface ServiceAccountKey {
  name: string;
  privateKeyType?: string;
  keyAlgorithm: string;
  privateKeyData?: string;
  publicKeyData?: string;
  validAfterTime: string;
  validBeforeTime: string;
  keyOrigin?: string;
  keyType?: string;
}

export interface IamPolicy {
  bindings: IamBinding[];
  etag?: string;
  version?: number;
  auditConfigs?: AuditConfig[];
}

export interface IamBinding {
  role: string;
  members: string[];
  condition?: IamCondition;
}

export interface IamCondition {
  expression: string;
  title: string;
  description?: string;
  location?: string;
}

export interface AuditConfig {
  service: string;
  auditLogConfigs: AuditLogConfig[];
}

export interface AuditLogConfig {
  logType: string;
  exemptedMembers?: string[];
}

export interface Role {
  name: string;
  title: string;
  description?: string;
  stage?: string;
  includedPermissions?: string[];
  deleted?: boolean;
  etag?: string;
}

export interface Permission {
  name: string;
  title?: string;
  description?: string;
  onlyInPredefinedRoles?: boolean;
  stage?: string;
  customRolesSupportLevel?: string;
  apiDisabled?: boolean;
}

export interface TestIamPermissionsRequest {
  permissions: string[];
}

export interface TestIamPermissionsResponse {
  permissions: string[];
}

export interface CreateServiceAccountRequest {
  accountId: string;
  serviceAccount?: {
    displayName?: string;
    description?: string;
  };
}

export interface CreateServiceAccountKeyRequest {
  privateKeyType?: 'TYPE_PKCS12_FILE' | 'TYPE_GOOGLE_CREDENTIALS_FILE';
  keyAlgorithm?: 'KEY_ALG_RSA_1024' | 'KEY_ALG_RSA_2048';
}

export interface CreateRoleRequest {
  roleId: string;
  role: {
    title: string;
    description?: string;
    includedPermissions: string[];
    stage?: string;
  };
}

export interface UpdateRoleRequest {
  title?: string;
  description?: string;
  includedPermissions?: string[];
  stage?: string;
}

// Common member types for IAM bindings
export type IamMemberType =
  | `user:${string}`
  | `serviceAccount:${string}`
  | `group:${string}`
  | `domain:${string}`
  | 'allUsers'
  | 'allAuthenticatedUsers';

// Common IAM roles
export const CommonRoles = {
  OWNER: 'roles/owner',
  EDITOR: 'roles/editor',
  VIEWER: 'roles/viewer',
  STORAGE_ADMIN: 'roles/storage.admin',
  STORAGE_OBJECT_ADMIN: 'roles/storage.objectAdmin',
  STORAGE_OBJECT_VIEWER: 'roles/storage.objectViewer',
  COMPUTE_ADMIN: 'roles/compute.admin',
  COMPUTE_INSTANCE_ADMIN: 'roles/compute.instanceAdmin.v1',
  COMPUTE_NETWORK_ADMIN: 'roles/compute.networkAdmin',
  IAM_ADMIN: 'roles/iam.serviceAccountAdmin',
  IAM_KEY_ADMIN: 'roles/iam.serviceAccountKeyAdmin',
} as const;
