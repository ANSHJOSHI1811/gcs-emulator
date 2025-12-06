import { apiClient, PROJECT_ID } from "./client";

export interface SignedUrlResponse {
  signedUrl: string;
  expiresAt: string;
}

/**
 * Generate a signed URL for object download (Phase 3)
 * 
 * Calls backend endpoint to generate HMAC-signed URL with expiration.
 */
export const generateSignedUrl = async (
  bucketName: string,
  objectName: string,
  method: "GET" | "PUT" = "GET",
  expiresIn: number = 3600
): Promise<string> => {
  const response = await apiClient.post<SignedUrlResponse>(
    `/storage/v1/b/${bucketName}/o/${encodeURIComponent(objectName)}/signedUrl?project=${PROJECT_ID}`,
    {
      method,
      expiresIn,
    }
  );
  return response.data.signedUrl;
};
