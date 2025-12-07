import { Dialog, Transition } from '@headlessui/react';
import { Fragment, useEffect, useState } from 'react';
import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import * as z from 'zod';
import { createInstance, fetchMachineTypes } from '@/api/compute';
import { MachineType } from '@/types/compute';
import Spinner from '@/components/common/Spinner';

const createInstanceSchema = z.object({
  name: z.string()
    .min(1, "Name is required")
    .max(63, "Name must be 63 characters or less")
    .regex(/^[a-z]([a-z0-9-]*[a-z0-9])?$/, "Name must start with lowercase letter and contain only lowercase letters, numbers, and hyphens"),
  machineType: z.string().min(1, "Machine type is required"),
  metadata: z.string().optional(),
  labels: z.string().optional(),
  tags: z.string().optional(),
});

type CreateInstanceFormData = z.infer<typeof createInstanceSchema>;

interface CreateInstanceModalProps {
  isOpen: boolean;
  onClose: () => void;
  onSuccess: () => void;
  zone: string;
}

export default function CreateInstanceModal({ isOpen, onClose, onSuccess, zone }: CreateInstanceModalProps) {
  const [machineTypes, setMachineTypes] = useState<MachineType[]>([]);
  const [isLoadingMachineTypes, setIsLoadingMachineTypes] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const {
    register,
    handleSubmit,
    formState: { errors, isSubmitting },
    reset,
  } = useForm<CreateInstanceFormData>({
    resolver: zodResolver(createInstanceSchema),
    defaultValues: {
      name: '',
      machineType: '',
      metadata: '',
      labels: '',
      tags: '',
    },
  });

  // Load machine types when modal opens
  useEffect(() => {
    if (isOpen && machineTypes.length === 0) {
      loadMachineTypes();
    }
  }, [isOpen]);

  const loadMachineTypes = async () => {
    setIsLoadingMachineTypes(true);
    try {
      const types = await fetchMachineTypes(zone);
      setMachineTypes(types);
    } catch (err: any) {
      setError(err.response?.data?.error?.message || err.message || "Failed to load machine types");
    } finally {
      setIsLoadingMachineTypes(false);
    }
  };

  const onSubmit = async (data: CreateInstanceFormData) => {
    setError(null);
    try {
      // Parse metadata, labels, and tags
      let metadata: Record<string, string> | undefined;
      let labels: Record<string, string> | undefined;
      let tags: string[] | undefined;

      if (data.metadata) {
        try {
          metadata = JSON.parse(data.metadata);
        } catch {
          setError("Invalid JSON format for metadata");
          return;
        }
      }

      if (data.labels) {
        try {
          labels = JSON.parse(data.labels);
        } catch {
          setError("Invalid JSON format for labels");
          return;
        }
      }

      if (data.tags) {
        try {
          tags = data.tags.split(',').map(t => t.trim()).filter(t => t.length > 0);
        } catch {
          setError("Invalid format for tags");
          return;
        }
      }

      await createInstance(zone, {
        name: data.name,
        machineType: data.machineType,
        metadata,
        labels,
        tags,
      });

      reset();
      onSuccess();
    } catch (err: any) {
      setError(err.response?.data?.error?.message || err.message || "Failed to create instance");
    }
  };

  const handleClose = () => {
    reset();
    setError(null);
    onClose();
  };

  return (
    <Transition appear show={isOpen} as={Fragment}>
      <Dialog as="div" className="relative z-10" onClose={handleClose}>
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
                  className="text-lg font-medium leading-6 text-gray-900"
                >
                  Create a VM Instance
                </Dialog.Title>
                <p className="text-sm text-gray-500 mt-1">Zone: {zone}</p>

                {error && (
                  <div className="mt-4 bg-red-50 border border-red-200 rounded-lg px-4 py-3 flex items-start gap-2" role="alert">
                    <div className="flex-shrink-0 w-5 h-5 mt-0.5">
                      <svg className="w-5 h-5 text-red-600" fill="currentColor" viewBox="0 0 20 20">
                        <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zM8.707 7.293a1 1 0 00-1.414 1.414L8.586 10l-1.293 1.293a1 1 0 101.414 1.414L10 11.414l1.293 1.293a1 1 0 001.414-1.414L11.414 10l1.293-1.293a1 1 0 00-1.414-1.414L10 8.586 8.707 7.293z" clipRule="evenodd" />
                      </svg>
                    </div>
                    <span className="text-sm text-red-800">{error}</span>
                  </div>
                )}

                <form onSubmit={handleSubmit(onSubmit)} className="mt-4 space-y-4">
                  {/* Instance Name */}
                  <div className="flex flex-col space-y-2">
                    <label htmlFor="name" className="text-sm font-medium text-gray-700">
                      Instance name <span className="text-red-500">*</span>
                    </label>
                    <input
                      id="name"
                      type="text"
                      {...register('name')}
                      className="block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm placeholder-gray-400 focus:outline-none focus:ring-blue-500 focus:border-blue-500 sm:text-sm"
                      placeholder="my-instance"
                    />
                    {errors.name && <p className="text-sm text-red-600">{errors.name.message}</p>}
                    <p className="text-xs text-gray-500">Must start with a lowercase letter and contain only lowercase letters, numbers, and hyphens</p>
                  </div>

                  {/* Machine Type */}
                  <div className="flex flex-col space-y-2">
                    <label htmlFor="machineType" className="text-sm font-medium text-gray-700">
                      Machine type <span className="text-red-500">*</span>
                    </label>
                    {isLoadingMachineTypes ? (
                      <div className="flex items-center gap-2 px-3 py-2 border border-gray-300 rounded-md bg-gray-50">
                        <Spinner />
                        <span className="text-sm text-gray-500">Loading machine types...</span>
                      </div>
                    ) : (
                      <select
                        id="machineType"
                        {...register('machineType')}
                        className="block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-blue-500 focus:border-blue-500 sm:text-sm"
                      >
                        <option value="">Select a machine type</option>
                        {machineTypes.map((type) => (
                          <option key={type.name} value={type.name}>
                            {type.name} ({type.guestCpus} vCPU{type.guestCpus > 1 ? 's' : ''}, {(type.memoryMb / 1024).toFixed(1)} GB RAM)
                          </option>
                        ))}
                      </select>
                    )}
                    {errors.machineType && <p className="text-sm text-red-600">{errors.machineType.message}</p>}
                  </div>

                  {/* Metadata (Optional) */}
                  <div className="flex flex-col space-y-2">
                    <label htmlFor="metadata" className="text-sm font-medium text-gray-700">
                      Metadata (Optional)
                    </label>
                    <textarea
                      id="metadata"
                      {...register('metadata')}
                      rows={3}
                      className="block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm placeholder-gray-400 focus:outline-none focus:ring-blue-500 focus:border-blue-500 sm:text-sm font-mono"
                      placeholder='{"key1": "value1", "key2": "value2"}'
                    />
                    {errors.metadata && <p className="text-sm text-red-600">{errors.metadata.message}</p>}
                    <p className="text-xs text-gray-500">JSON format: key-value pairs</p>
                  </div>

                  {/* Labels (Optional) */}
                  <div className="flex flex-col space-y-2">
                    <label htmlFor="labels" className="text-sm font-medium text-gray-700">
                      Labels (Optional)
                    </label>
                    <textarea
                      id="labels"
                      {...register('labels')}
                      rows={2}
                      className="block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm placeholder-gray-400 focus:outline-none focus:ring-blue-500 focus:border-blue-500 sm:text-sm font-mono"
                      placeholder='{"env": "dev", "team": "backend"}'
                    />
                    {errors.labels && <p className="text-sm text-red-600">{errors.labels.message}</p>}
                    <p className="text-xs text-gray-500">JSON format: key-value pairs for resource labels</p>
                  </div>

                  {/* Tags (Optional) */}
                  <div className="flex flex-col space-y-2">
                    <label htmlFor="tags" className="text-sm font-medium text-gray-700">
                      Network tags (Optional)
                    </label>
                    <input
                      id="tags"
                      type="text"
                      {...register('tags')}
                      className="block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm placeholder-gray-400 focus:outline-none focus:ring-blue-500 focus:border-blue-500 sm:text-sm"
                      placeholder="http-server, https-server"
                    />
                    {errors.tags && <p className="text-sm text-red-600">{errors.tags.message}</p>}
                    <p className="text-xs text-gray-500">Comma-separated list of tags</p>
                  </div>

                  {/* Action Buttons */}
                  <div className="mt-6 flex justify-end space-x-2 pt-4 border-t border-gray-200">
                    <button
                      type="button"
                      className="inline-flex justify-center rounded-md border border-transparent bg-gray-100 px-4 py-2 text-sm font-medium text-gray-700 hover:bg-gray-200 focus:outline-none focus-visible:ring-2 focus-visible:ring-blue-500 focus-visible:ring-offset-2"
                      onClick={handleClose}
                      disabled={isSubmitting}
                    >
                      Cancel
                    </button>
                    <button
                      type="submit"
                      disabled={isSubmitting || isLoadingMachineTypes}
                      className="inline-flex justify-center rounded-md border border-transparent bg-blue-600 px-4 py-2 text-sm font-medium text-white hover:bg-blue-700 focus:outline-none focus-visible:ring-2 focus-visible:ring-blue-500 focus-visible:ring-offset-2 disabled:opacity-50"
                    >
                      {isSubmitting ? 'Creating...' : 'Create Instance'}
                    </button>
                  </div>
                </form>
              </Dialog.Panel>
            </Transition.Child>
          </div>
        </div>
      </Dialog>
    </Transition>
  );
}
