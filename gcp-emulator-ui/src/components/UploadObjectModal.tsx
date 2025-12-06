import { useState, useEffect, Fragment } from "react";
import { Dialog, Transition } from "@headlessui/react";
import { useUpload } from "../hooks/useUpload";
import { isValidObjectName, getObjectNameError } from "../utils/validators";
import toast from "react-hot-toast";

interface UploadObjectModalProps {
  isOpen: boolean;
  onClose: () => void;
  bucketName: string;
  onUploaded: () => void;
}

type UploadType = "media" | "multipart" | "resumable";

export default function UploadObjectModal({
  isOpen,
  onClose,
  bucketName,
  onUploaded,
}: UploadObjectModalProps) {
  const [file, setFile] = useState<File | null>(null);
  const [objectName, setObjectName] = useState("");
  const [objectNameError, setObjectNameError] = useState<string | null>(null);
  const [uploadType, setUploadType] = useState<UploadType>("media");
  const { isUploading, uploadMedia, uploadMultipart, uploadResumable } = useUpload();
  const [uploadProgress, setUploadProgress] = useState(0);

  useEffect(() => {
    if (file) {
      setObjectName(file.name);
      // Auto-select resumable for files > 5MB
      if (file.size > 5 * 1024 * 1024) {
        setUploadType("resumable");
      }
    }
  }, [file]);

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files) {
      setFile(e.target.files[0]);
    }
  };

  const handleObjectNameChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const value = e.target.value;
    setObjectName(value);
    setObjectNameError(getObjectNameError(value));
  };

  const handleUpload = async () => {
    if (!file || !isValidObjectName(objectName)) return;

    try {
      if (uploadType === "media") {
        await uploadMedia(bucketName, file, objectName);
      } else if (uploadType === "multipart") {
        await uploadMultipart(bucketName, file, objectName);
      } else if (uploadType === "resumable") {
        await uploadResumable(bucketName, file, objectName, (progress) => {
          setUploadProgress(progress);
        });
      }
      toast.success(`✅ File "${objectName}" uploaded successfully!`);
      setUploadProgress(0);
      onUploaded();
      onClose();
    } catch (error: any) {
      console.error("Upload failed:", error);
      const errorMessage = error.response?.data?.error || error.message || "Upload failed";
      if (errorMessage.includes('path traversal') || errorMessage.includes('not allowed')) {
        toast.error('❌ Invalid object name: Path traversal detected');
      } else {
        toast.error(`❌ Upload failed: ${errorMessage}`);
      }
    }
  };

  return (
    <Transition appear show={isOpen} as={Fragment}>
      <Dialog as="div" className="relative z-10" onClose={onClose}>
        <Transition.Child
          as={Fragment}
          enter="ease-out duration-300"
          enterFrom="opacity-0"
          enterTo="opacity-100"
          leave="ease-in duration-200"
          leaveFrom="opacity-100"
          leaveTo="opacity-0"
        >
          <div className="fixed inset-0 bg-black bg-opacity-25" />
        </Transition.Child>

        <div className="fixed inset-0 overflow-y-auto">
          <div className="flex min-h-full items-center justify-center p-4 text-center">
            <Transition.Child
              as={Fragment}
              enter="ease-out duration-300"
              enterFrom="opacity-0 scale-95"
              enterTo="opacity-100 scale-100"
              leave="ease-in duration-200"
              leaveFrom="opacity-100 scale-100"
              leaveTo="opacity-0 scale-95"
            >
              <Dialog.Panel className="w-full max-w-md transform overflow-hidden rounded-2xl bg-white p-6 text-left align-middle shadow-xl transition-all">
                <Dialog.Title
                  as="h3"
                  className="text-lg font-medium leading-6 text-gray-900"
                >
                  Upload Object
                </Dialog.Title>
                <div className="mt-4 space-y-4">
                  <div>
                    <label className="block text-sm font-medium text-gray-700">
                      File
                    </label>
                    <input
                      type="file"
                      onChange={handleFileChange}
                      className="mt-1 block w-full text-sm text-gray-500 file:mr-4 file:py-2 file:px-4 file:rounded-full file:border-0 file:text-sm file:font-semibold file:bg-violet-50 file:text-violet-700 hover:file:bg-violet-100"
                    />
                  </div>
                  <div>
                    <label
                      htmlFor="objectName"
                      className="block text-sm font-medium text-gray-700"
                    >
                      Object Name
                    </label>
                    <input
                      type="text"
                      id="objectName"
                      value={objectName}
                      onChange={handleObjectNameChange}
                      className={`mt-1 block w-full rounded-md shadow-sm sm:text-sm ${
                        objectNameError
                          ? 'border-red-300 focus:border-red-500 focus:ring-red-500'
                          : 'border-gray-300 focus:border-indigo-500 focus:ring-indigo-500'
                      }`}
                    />
                    {objectNameError && (
                      <p className="mt-1 text-sm text-red-600">{objectNameError}</p>
                    )}
                    <p className="mt-1 text-xs text-gray-500">
                      Allowed: letters, numbers, hyphens, underscores, forward slashes. No path traversal (..), backslashes, or drive letters.
                    </p>
                  </div>
                  <fieldset>
                    <legend className="text-sm font-medium text-gray-900">
                      Upload Type
                    </legend>
                    <div className="mt-2 space-y-2">
                      <div className="flex items-center">
                        <input
                          id="media"
                          name="upload-type"
                          type="radio"
                          value="media"
                          checked={uploadType === "media"}
                          onChange={() => setUploadType("media")}
                          className="h-4 w-4 border-gray-300 text-indigo-600 focus:ring-indigo-500"
                        />
                        <label
                          htmlFor="media"
                          className="ml-3 block text-sm font-medium text-gray-700"
                        >
                          Media upload
                        </label>
                      </div>
                      <div className="flex items-center">
                        <input
                          id="multipart"
                          name="upload-type"
                          type="radio"
                          value="multipart"
                          checked={uploadType === "multipart"}
                          onChange={() => setUploadType("multipart")}
                          className="h-4 w-4 border-gray-300 text-indigo-600 focus:ring-indigo-500"
                        />
                        <label
                          htmlFor="multipart"
                          className="ml-3 block text-sm font-medium text-gray-700"
                        >
                          Multipart upload
                        </label>
                      </div>
                      <div className="flex items-center">
                        <input
                          id="resumable"
                          name="upload-type"
                          type="radio"
                          value="resumable"
                          checked={uploadType === "resumable"}
                          onChange={() => setUploadType("resumable")}
                          className="h-4 w-4 border-gray-300 text-indigo-600 focus:ring-indigo-500"
                        />
                        <label
                          htmlFor="resumable"
                          className="ml-3 block text-sm font-medium text-gray-700"
                        >
                          Resumable upload (for large files &gt; 5MB)
                          {file && file.size > 5 * 1024 * 1024 && (
                            <span className="ml-2 text-xs text-green-600 font-semibold">
                              Recommended
                            </span>
                          )}
                        </label>
                      </div>
                    </div>
                  </fieldset>
                  {uploadType === "resumable" && uploadProgress > 0 && (
                    <div className="mt-4">
                      <div className="flex justify-between mb-1">
                        <span className="text-sm font-medium text-gray-700">Upload Progress</span>
                        <span className="text-sm font-medium text-gray-700">{uploadProgress}%</span>
                      </div>
                      <div className="w-full bg-gray-200 rounded-full h-2.5">
                        <div
                          className="bg-blue-600 h-2.5 rounded-full transition-all duration-300"
                          style={{ width: `${uploadProgress}%` }}
                        ></div>
                      </div>
                    </div>
                  )}
                </div>

                <div className="mt-6 flex justify-end space-x-2">
                  <button
                    type="button"
                    className="inline-flex justify-center rounded-md border border-transparent bg-gray-100 px-4 py-2 text-sm font-medium text-gray-700 hover:bg-gray-200 focus:outline-none focus-visible:ring-2 focus-visible:ring-gray-500 focus-visible:ring-offset-2"
                    onClick={onClose}
                  >
                    Cancel
                  </button>
                  <button
                    type="button"
                    className="inline-flex justify-center rounded-md border border-transparent bg-blue-600 px-4 py-2 text-sm font-medium text-white hover:bg-blue-700 focus:outline-none focus-visible:ring-2 focus-visible:ring-blue-500 focus-visible:ring-offset-2 disabled:bg-gray-300 disabled:cursor-not-allowed"
                    onClick={handleUpload}
                    disabled={!file || !objectName || !!objectNameError || isUploading}
                  >
                    {isUploading ? "Uploading..." : "Upload"}
                  </button>
                </div>
              </Dialog.Panel>
            </Transition.Child>
          </div>
        </div>
      </Dialog>
    </Transition>
  );
}
