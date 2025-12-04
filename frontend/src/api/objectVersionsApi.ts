import apiClient from "./client";
import { GCSObject, ObjectVersion } from "../types";

const PROJECT_ID = "test-project";

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
  bucketName: string,
  objectName: string
): Promise<{ items: ObjectVersion[] }> => {
  try {
    // TODO: The user-specified endpoint might differ from the standard GCS API.
    // Standard GCS API for listing versions is GET /storage/v1/b/{bucket}/o?versions=true&prefix={objectName}
    const response = await apiClient.get(
      `/storage/v1/b/${bucketName}/o?versions=true&prefix=${encodeURIComponent(objectName)}&project=${PROJECT_ID}`
    );
    // Filter to get versions only for the exact object name
    const versions = response.data.items.filter((v: ObjectVersion) => v.name === objectName);
    return { items: versions };
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
