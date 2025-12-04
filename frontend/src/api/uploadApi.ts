import apiClient from "./client";
import { UploadResponse } from "../types";

const PROJECT_ID = "test-project";

export const uploadMedia = async (
  bucketName: string,
  file: File,
  objectName: string
): Promise<UploadResponse> => {
  const response = await apiClient.post(
    `/upload/storage/v1/b/${bucketName}/o?uploadType=media&name=${encodeURIComponent(
      objectName
    )}&project=${PROJECT_ID}`,
    file,
    {
      headers: {
        "Content-Type": file.type,
      },
    }
  );
  return response.data;
};

export const uploadMultipart = async (
  bucketName: string,
  file: File,
  objectName: string
): Promise<UploadResponse> => {
  const boundary = "----WebKitFormBoundary7MA4YWxkTrZu0gW";
  const metadata = {
    name: objectName,
    contentType: file.type,
  };

  let data = `--${boundary}\r\n`;
  data += `Content-Type: application/json; charset=UTF-8\r\n\r\n`;
  data += `${JSON.stringify(metadata)}\r\n`;
  data += `--${boundary}\r\n`;
  data += `Content-Type: ${file.type}\r\n\r\n`;

  const fileReader = new FileReader();
  const fileContent: string = await new Promise((resolve, reject) => {
    fileReader.onload = (e) => resolve(e.target?.result as string);
    fileReader.onerror = (e) => reject(e);
    fileReader.readAsBinaryString(file);
  });

  let requestBody = data + fileContent + `\r\n--${boundary}--`;

  const response = await apiClient.post(
    `/upload/storage/v1/b/${bucketName}/o?uploadType=multipart&project=${PROJECT_ID}`,
    requestBody,
    {
      headers: {
        "Content-Type": `multipart/related; boundary=${boundary}`,
      },
    }
  );

  return response.data;
};
