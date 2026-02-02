// Bucket name validation (GCS rules)
export const isValidBucketName = (name: string): boolean => {
  // Between 3 and 63 characters
  if (name.length < 3 || name.length > 63) return false;
  
  // Only lowercase letters, numbers, hyphens, underscores, and dots
  if (!/^[a-z0-9._-]+$/.test(name)) return false;
  
  // Must start and end with number or letter
  if (!/^[a-z0-9]/.test(name) || !/[a-z0-9]$/.test(name)) return false;
  
  // Cannot contain consecutive dots
  if (/\.\./.test(name)) return false;
  
  return true;
};

// Object name validation with path traversal prevention
export const isValidObjectName = (name: string): boolean => {
  if (!name || name.length === 0) return false;
  if (name.length > 1024) return false;
  
  // Prevent path traversal attempts
  if (name.includes('..')) return false;
  if (name.includes('\\')) return false;
  if (name.startsWith('/')) return false;
  
  // Prevent Windows drive letters
  if (name.length >= 2 && name[1] === ':') return false;
  
  return true;
};

// Get detailed error message for object name validation
export const getObjectNameError = (name: string): string | null => {
  if (!name) return "Object name is required";
  if (name.length > 1024) return "Object name must be less than 1024 characters";
  if (name.includes('..')) return "Object name cannot contain '..' (path traversal)";
  if (name.includes('\\')) return "Object name cannot contain backslashes";
  if (name.startsWith('/')) return "Object name cannot start with '/'";
  if (name.length >= 2 && name[1] === ':') return "Object name cannot contain drive letters";
  return null;
};
