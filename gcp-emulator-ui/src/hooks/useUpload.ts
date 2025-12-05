import { useState } from "react";
import { uploadMedia as apiUploadMedia, uploadMultipart as apiUploadMultipart } from "../api/uploadApi";

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

  return {
    isUploading,
    error,
    uploadMedia,
    uploadMultipart,
  };
};
