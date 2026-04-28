import { Dialog, Transition } from '@headlessui/react';
import { Fragment } from 'react';
import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import * as z from 'zod';
import { useBuckets } from '../../hooks/useBuckets';

const createBucketSchema = z.object({
  name: z.string().min(3, "Name must be at least 3 characters").regex(/^[a-z0-9][a-z0-9-]*[a-z0-9]$/, "Invalid bucket name format."),
});

type CreateBucketFormData = z.infer<typeof createBucketSchema>;

interface CreateBucketModalProps {
  isOpen: boolean;
  onClose: () => void;
  onBucketCreated: () => void;
}

export default function CreateBucketModal({ isOpen, onClose, onBucketCreated }: CreateBucketModalProps) {
  const { handleCreateBucket } = useBuckets();
  const {
    register,
    handleSubmit,
    formState: { errors, isSubmitting },
    reset,
  } = useForm<CreateBucketFormData>({
    resolver: zodResolver(createBucketSchema),
  });

  const onSubmit = async (data: CreateBucketFormData) => {
    try {
      await handleCreateBucket(data.name);
      reset();
      onBucketCreated(); // Use the callback
    } catch (error) {
      // Error is already handled by toast in the hook
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
                  Create a new bucket
                </Dialog.Title>
                <form onSubmit={handleSubmit(onSubmit)} className="mt-4">
                  <div className="flex flex-col space-y-2">
                    <label htmlFor="name" className="text-sm font-medium text-gray-700">Bucket name</label>
                    <input
                      id="name"
                      type="text"
                      {...register('name')}
                      className="block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm placeholder-gray-400 focus:outline-none focus:ring-blue-500 focus:border-blue-500 sm:text-sm"
                      placeholder="my-awesome-bucket"
                    />
                    {errors.name && <p className="text-sm text-red-600">{errors.name.message}</p>}
                  </div>

                  <div className="mt-6 flex justify-end space-x-2">
                    <button
                      type="button"
                      className="inline-flex justify-center rounded-md border border-transparent bg-gray-100 px-4 py-2 text-sm font-medium text-gray-700 hover:bg-gray-200 focus:outline-none focus-visible:ring-2 focus-visible:ring-blue-500 focus-visible:ring-offset-2"
                      onClick={onClose}
                    >
                      Cancel
                    </button>
                    <button
                      type="submit"
                      disabled={isSubmitting}
                      className="inline-flex justify-center rounded-md border border-transparent bg-blue-600 px-4 py-2 text-sm font-medium text-white hover:bg-blue-700 focus:outline-none focus-visible:ring-2 focus-visible:ring-blue-500 focus-visible:ring-offset-2 disabled:opacity-50"
                    >
                      {isSubmitting ? 'Creating...' : 'Create'}
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
