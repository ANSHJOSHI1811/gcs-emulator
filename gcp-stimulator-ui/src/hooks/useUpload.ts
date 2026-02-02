import { useState } from "react";
import { 
  uploadMedia as apiUploadMedia, 
  uploadMultipart as apiUploadMultipart,
  initiateResumableUpload,
  uploadChunk
} from "../api/uploadApi";

export const useUpload = () => {
  const [isUploading, setIsUploading] = useState(false);
  const [error, setError] = useState<Error | null>(null);

  const uploadMedia = async (
    bucketName: string,
    file: File,
    objectName: string
  ) => {
    setIsUploading(true);
    setError(null);
    try {
      const result = await apiUploadMedia(bucketName, file, objectName);
      setIsUploading(false);
      return result;
    } catch (err) {
      setError(err as Error);
      setIsUploading(false);
      throw err;
    }
  };

  const uploadMultipart = async (
    bucketName: string,
    file: File,
    objectName: string
  ) => {
    setIsUploading(true);
    setError(null);
    try {
      const result = await apiUploadMultipart(bucketName, file, objectName);
      setIsUploading(false);
      return result;
    } catch (err) {
      setError(err as Error);
      setIsUploading(false);
      throw err;
    }
  };

  const uploadResumable = async (
    bucketName: string,
    file: File,
    objectName: string,
    onProgress?: (progress: number) => void
  ) => {
    setIsUploading(true);
    setError(null);
    try {
      // Step 1: Initiate resumable upload session
      const { sessionId } = await initiateResumableUpload(
        bucketName,
        objectName,
        file.type || "application/octet-stream"
      );

      // Step 2: Upload file in chunks (256KB chunks)
      const CHUNK_SIZE = 256 * 1024; // 256KB
      const totalSize = file.size;
      let offset = 0;

      while (offset < totalSize) {
        const chunk = file.slice(offset, offset + CHUNK_SIZE);
        await uploadChunk(sessionId, chunk, offset, totalSize);
        
        offset += chunk.size;
        
        // Report progress
        if (onProgress) {
          const progress = Math.round((offset / totalSize) * 100);
          onProgress(progress);
        }
      }

      setIsUploading(false);
      return { success: true };
    } catch (err) {
      setError(err as Error);
      setIsUploading(false);
      throw err;
    }
  };

  return {
    isUploading,
    error,
    uploadMedia,
    uploadMultipart,
    uploadResumable,
  };
};
