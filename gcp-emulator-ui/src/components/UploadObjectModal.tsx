import { useState, useEffect, Fragment } from "react";
import { Dialog, Transition } from "@headlessui/react";
import { useUpload } from "../hooks/useUpload";
import { isValidObjectName, getObjectNameError } from "../utils/validators";
import toast from "react-hot-toast";
import { Upload as UploadIcon, File, X } from "lucide-react";

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
  const [isDragging, setIsDragging] = useState(false);

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
    if (e.target.files && e.target.files[0]) {
      setFile(e.target.files[0]);
    }
  };

  const handleDragOver = (e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(true);
  };

  const handleDragLeave = () => {
    setIsDragging(false);
  };

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(false);
    
    if (e.dataTransfer.files && e.dataTransfer.files[0]) {
      setFile(e.dataTransfer.files[0]);
    }
  };

  const handleObjectNameChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const value = e.target.value;
    setObjectName(value);
    setObjectNameError(getObjectNameError(value));
  };

  const formatFileSize = (bytes: number) => {
    if (bytes === 0) return '0 Bytes';
    const k = 1024;
    const sizes = ['Bytes', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return Math.round((bytes / Math.pow(k, i)) * 100) / 100 + ' ' + sizes[i];
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
      setFile(null);
      setObjectName("");
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
              <Dialog.Panel className="w-full max-w-2xl transform overflow-hidden rounded-2xl bg-white p-6 text-left align-middle shadow-xl transition-all">
                <Dialog.Title
                  as="h3"
                  className="text-xl font-semibold leading-6 text-gray-900 mb-6"
                >
                  Upload Object to {bucketName}
                </Dialog.Title>
                <div className="space-y-6">
                  {/* Drag & Drop Zone */}
                  <div
                    onDragOver={handleDragOver}
                    onDragLeave={handleDragLeave}
                    onDrop={handleDrop}
                    className={`relative border-2 border-dashed rounded-xl p-8 transition-colors ${
                      isDragging
                        ? 'border-blue-500 bg-blue-50'
                        : file
                        ? 'border-green-300 bg-green-50'
                        : 'border-gray-300 bg-gray-50 hover:border-gray-400'
                    }`}
                  >
                    <input
                      type="file"
                      onChange={handleFileChange}
                      className="absolute inset-0 w-full h-full opacity-0 cursor-pointer"
                      id="file-upload"
                    />
                    
                    {!file ? (
                      <div className="text-center">
                        <UploadIcon className="mx-auto h-12 w-12 text-gray-400" />
                        <p className="mt-2 text-sm font-medium text-gray-900">
                          Drop your file here or click to browse
                        </p>
                        <p className="mt-1 text-xs text-gray-500">
                          Supports all file types
                        </p>
                      </div>
                    ) : (
                      <div className="flex items-center justify-between">
                        <div className="flex items-center gap-3">
                          <div className="p-3 bg-white rounded-lg border border-green-200">
                            <File className="w-6 h-6 text-green-600" />
                          </div>
                          <div>
                            <p className="text-sm font-medium text-gray-900 truncate max-w-md">
                              {file.name}
                            </p>
                            <p className="text-xs text-gray-500">{formatFileSize(file.size)}</p>
                          </div>
                        </div>
                        <button
                          onClick={(e) => {
                            e.stopPropagation();
                            setFile(null);
                            setObjectName("");
                          }}
                          className="p-2 text-gray-400 hover:text-red-600 hover:bg-red-50 rounded-lg transition-colors"
                        >
                          <X className="w-5 h-5" />
                        </button>
                      </div>
                    )}
                  </div>

                  {/* Object Name Input */}
                  <div>
                    <label
                      htmlFor="objectName"
                      className="block text-sm font-medium text-gray-700 mb-2"
                    >
                      Object Name
                    </label>
                    <input
                      type="text"
                      id="objectName"
                      value={objectName}
                      onChange={handleObjectNameChange}
                      placeholder="Enter object name..."
                      className={`block w-full rounded-lg shadow-sm sm:text-sm px-4 py-3 border ${
                        objectNameError
                          ? 'border-red-300 focus:border-red-500 focus:ring-red-500'
                          : 'border-gray-300 focus:border-blue-500 focus:ring-blue-500'
                      }`}
                    />
                    {objectNameError && (
                      <p className="mt-2 text-sm text-red-600 flex items-center gap-1">
                        <span>⚠️</span>
                        {objectNameError}
                      </p>
                    )}
                    <p className="mt-2 text-xs text-gray-500">
                      Letters, numbers, hyphens, underscores, and forward slashes allowed
                    </p>
                  </div>

                  {/* Upload Type Selection */}
                  <fieldset className="border border-gray-200 rounded-lg p-4">
                    <legend className="text-sm font-medium text-gray-900 px-2">
                      Upload Method
                    </legend>
                    <div className="mt-3 space-y-3">
                      <label className="flex items-start gap-3 cursor-pointer group">
                        <input
                          type="radio"
                          value="media"
                          checked={uploadType === "media"}
                          onChange={() => setUploadType("media")}
                          className="mt-1 h-4 w-4 border-gray-300 text-blue-600 focus:ring-blue-500"
                        />
                        <div className="flex-1">
                          <span className="block text-sm font-medium text-gray-900 group-hover:text-blue-600">
                            Media Upload
                          </span>
                          <span className="block text-xs text-gray-500">Best for small files</span>
                        </div>
                      </label>
                      
                      <label className="flex items-start gap-3 cursor-pointer group">
                        <input
                          type="radio"
                          value="multipart"
                          checked={uploadType === "multipart"}
                          onChange={() => setUploadType("multipart")}
                          className="mt-1 h-4 w-4 border-gray-300 text-blue-600 focus:ring-blue-500"
                        />
                        <div className="flex-1">
                          <span className="block text-sm font-medium text-gray-900 group-hover:text-blue-600">
                            Multipart Upload
                          </span>
                          <span className="block text-xs text-gray-500">For files with metadata</span>
                        </div>
                      </label>
                      
                      <label className="flex items-start gap-3 cursor-pointer group">
                        <input
                          type="radio"
                          value="resumable"
                          checked={uploadType === "resumable"}
                          onChange={() => setUploadType("resumable")}
                          className="mt-1 h-4 w-4 border-gray-300 text-blue-600 focus:ring-blue-500"
                        />
                        <div className="flex-1">
                          <span className="block text-sm font-medium text-gray-900 group-hover:text-blue-600">
                            Resumable Upload
                            {file && file.size > 5 * 1024 * 1024 && (
                              <span className="ml-2 text-xs bg-green-100 text-green-700 px-2 py-0.5 rounded-full font-semibold">
                                Recommended
                              </span>
                            )}
                          </span>
                          <span className="block text-xs text-gray-500">For large files &gt; 5MB</span>
                        </div>
                      </label>
                    </div>
                  </fieldset>

                  {/* Progress Bar */}
                  {uploadType === "resumable" && uploadProgress > 0 && (
                    <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
                      <div className="flex justify-between items-center mb-2">
                        <span className="text-sm font-medium text-blue-900">Uploading...</span>
                        <span className="text-sm font-semibold text-blue-700">{uploadProgress}%</span>
                      </div>
                      <div className="w-full bg-blue-200 rounded-full h-3 overflow-hidden">
                        <div
                          className="bg-blue-600 h-3 rounded-full transition-all duration-300 ease-out"
                          style={{ width: `${uploadProgress}%` }}
                        ></div>
                      </div>
                    </div>
                  )}
                </div>

                {/* Actions */}
                <div className="mt-8 flex justify-end gap-3">
                  <button
                    type="button"
                    className="px-5 py-2.5 rounded-lg border-2 border-gray-300 text-sm font-medium text-gray-700 hover:bg-gray-50 transition-colors"
                    onClick={onClose}
                    disabled={isUploading}
                  >
                    Cancel
                  </button>
                  <button
                    type="button"
                    className="px-6 py-2.5 rounded-lg border-2 border-transparent bg-blue-600 text-sm font-medium text-white hover:bg-blue-700 transition-colors disabled:bg-gray-300 disabled:cursor-not-allowed shadow-sm"
                    onClick={handleUpload}
                    disabled={!file || !objectName || !!objectNameError || isUploading}
                  >
                    {isUploading ? "Uploading..." : "Upload File"}
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
