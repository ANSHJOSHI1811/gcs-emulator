import { useState, useEffect, Fragment } from "react";
import { Dialog, Transition } from "@headlessui/react";
import { useUpload } from "../hooks/useUpload";

interface UploadObjectModalProps {
  isOpen: boolean;
  onClose: () => void;
  bucketName: string;
  onUploaded: () => void;
}

type UploadType = "media" | "multipart";

export default function UploadObjectModal({
  isOpen,
  onClose,
  bucketName,
  onUploaded,
}: UploadObjectModalProps) {
  const [file, setFile] = useState<File | null>(null);
  const [objectName, setObjectName] = useState("");
  const [uploadType, setUploadType] = useState<UploadType>("media");
  const { isUploading, uploadMedia, uploadMultipart } = useUpload();

  useEffect(() => {
    if (file) {
      setObjectName(file.name);
    }
  }, [file]);

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files) {
      setFile(e.target.files[0]);
    }
  };

  const handleUpload = async () => {
    if (!file) return;

    try {
      if (uploadType === "media") {
        await uploadMedia(bucketName, file, objectName);
      } else {
        await uploadMultipart(bucketName, file, objectName);
      }
      onUploaded();
      onClose();
    } catch (error) {
      console.error("Upload failed:", error);
      // You might want to show an error to the user here
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
                      onChange={(e) => setObjectName(e.target.value)}
                      className="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500 sm:text-sm"
                    />
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
                    </div>
                  </fieldset>
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
                    className="inline-flex justify-center rounded-md border border-transparent bg-blue-600 px-4 py-2 text-sm font-medium text-white hover:bg-blue-700 focus:outline-none focus-visible:ring-2 focus-visible:ring-blue-500 focus-visible:ring-offset-2 disabled:bg-gray-300"
                    onClick={handleUpload}
                    disabled={!file || !objectName || isUploading}
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
