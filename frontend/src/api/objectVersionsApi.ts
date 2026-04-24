import { apiClient, PROJECT_ID } from "./client";
import { GCSObject, ObjectVersion } from "../types";

export const getObjectMetadata = async (
  bucketName: string,
  objectName: string
): Promise<GCSObject> => {
  const response = await apiClient.get(
    `/storage/v1/b/${bucketName}/o/${encodeURIComponent(objectName)}?project=${PROJECT_ID}`
  );
  return response.data;
};

export const getObjectVersion = async (
  bucketName: string,
  objectName: string,
  generation: string
): Promise<GCSObject> => {
  const response = await apiClient.get(
    `/storage/v1/b/${bucketName}/o/${encodeURIComponent(
      objectName
    )}?generation=${generation}&project=${PROJECT_ID}`
  );
  return response.data;
};

export const listObjectVersions = async (
  bucketName: string
): Promise<{ items: ObjectVersion[] }> => {
  try {
    // Fetch all versions in the bucket and filter client-side
    const response = await apiClient.get(
      `/storage/v1/b/${bucketName}/o?versions=true&project=${PROJECT_ID}`
    );
    return response.data;
  } catch (error) {
    console.warn("Backend may not support version listing, returning empty array.", error);
    return { items: [] };
  }
};

export const deleteObjectVersion = async (
  bucketName: string,
  objectName: string,
  generation: string
): Promise<void> => {
  await apiClient.delete(
    `/storage/v1/b/${bucketName}/o/${encodeURIComponent(
      objectName
    )}?generation=${generation}&project=${PROJECT_ID}`
  );
};
