// Error message handler for API responses
export const getErrorMessage = (error: any): string => {
  // Handle path traversal errors
  if (error.response?.status === 400) {
    const message = error.response?.data?.error || error.message;
    if (message.includes('path traversal') || message.includes('not allowed')) {
      return '❌ Invalid object name: Path traversal detected. Please use a valid name without "..", "\\", or absolute paths.';
    }
    return `❌ Bad Request: ${message}`;
  }
  
  // Handle bucket not empty errors
  if (error.response?.status === 409 || error.message?.includes('not empty')) {
    return '❌ Bucket is not empty. Please delete all objects first.';
  }
  
  // Handle bucket not found
  if (error.response?.status === 404) {
    return '❌ Bucket or object not found.';
  }
  
  // Handle precondition failures
  if (error.response?.status === 412) {
    return '❌ Precondition failed. The object may have been modified by another process.';
  }
  
  // Handle server errors
  if (error.response?.status >= 500) {
    return '❌ Server error. Please try again later.';
  }
  
  return `❌ Error: ${error.message || 'Unknown error occurred'}`;
};
