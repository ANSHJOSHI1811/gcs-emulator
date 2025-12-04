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

// Object name validation
export const isValidObjectName = (name: string): boolean => {
  if (!name || name.length === 0) return false;
  if (name.length > 1024) return false;
  return true;
};
