import { X } from 'lucide-react';
import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { z } from 'zod';
import { createLifecycleRule } from '../api/lifecycle';
import toast from 'react-hot-toast';

const lifecycleRuleSchema = z.object({
  action: z.enum(['Delete', 'Archive'], {
    required_error: 'Action is required',
  }),
  ageDays: z.number().int().positive('Age must be a positive integer'),
});

type LifecycleRuleFormData = z.infer<typeof lifecycleRuleSchema>;

interface CreateLifecycleRuleModalProps {
  isOpen: boolean;
  onClose: () => void;
  bucketName: string;
  onRuleCreated: () => void;
}

const CreateLifecycleRuleModal = ({ isOpen, onClose, bucketName, onRuleCreated }: CreateLifecycleRuleModalProps) => {
  const {
    register,
    handleSubmit,
    formState: { errors, isSubmitting },
    reset,
  } = useForm<LifecycleRuleFormData>({
    resolver: zodResolver(lifecycleRuleSchema),
    defaultValues: {
      action: 'Delete',
      ageDays: 30,
    },
  });

  const onSubmit = async (data: LifecycleRuleFormData) => {
    try {
      await createLifecycleRule({
        bucket: bucketName,
        action: data.action,
        ageDays: data.ageDays,
      });
      toast.success('✅ Lifecycle rule created successfully');
      reset();
      onRuleCreated();
    } catch (err) {
      console.error('Failed to create lifecycle rule:', err);
      toast.error('❌ Failed to create lifecycle rule');
    }
  };

  const handleClose = () => {
    reset();
    onClose();
  };

  if (!isOpen) return null;

  return (
    <>
      <div className="fixed inset-0 bg-gray-500 bg-opacity-75 transition-opacity z-50" onClick={handleClose}></div>
      <div className="fixed inset-0 z-50 overflow-y-auto">
        <div className="flex min-h-full items-center justify-center p-4">
          <div className="relative bg-white rounded-lg shadow-xl max-w-md w-full">
            {/* Header */}
            <div className="flex items-center justify-between p-6 border-b border-gray-200">
              <h3 className="text-lg font-semibold text-gray-900">Create Lifecycle Rule</h3>
              <button onClick={handleClose} className="text-gray-400 hover:text-gray-500">
                <X size={24} />
              </button>
            </div>

            {/* Form */}
            <form onSubmit={handleSubmit(onSubmit)} className="p-6 space-y-4">
              <div>
                <label htmlFor="action" className="block text-sm font-medium text-gray-700 mb-1">
                  Action <span className="text-red-500">*</span>
                </label>
                <select
                  id="action"
                  {...register('action')}
                  className="block w-full pl-3 pr-10 py-2 text-base border-gray-300 focus:outline-none focus:ring-indigo-500 focus:border-indigo-500 sm:text-sm rounded-md"
                >
                  <option value="Delete">Delete (Permanently remove objects)</option>
                  <option value="Archive">Archive (Move to ARCHIVE storage class)</option>
                </select>
                {errors.action && (
                  <p className="mt-1 text-sm text-red-600">{errors.action.message}</p>
                )}
              </div>

              <div>
                <label htmlFor="ageDays" className="block text-sm font-medium text-gray-700 mb-1">
                  Age (Days) <span className="text-red-500">*</span>
                </label>
                <input
                  type="number"
                  id="ageDays"
                  {...register('ageDays', { valueAsNumber: true })}
                  className="block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:ring-indigo-500 focus:border-indigo-500 sm:text-sm"
                  placeholder="e.g., 30"
                  min="1"
                />
                {errors.ageDays && (
                  <p className="mt-1 text-sm text-red-600">{errors.ageDays.message}</p>
                )}
                <p className="mt-1 text-xs text-gray-500">
                  Apply this action to objects older than this many days
                </p>
              </div>

              {/* Footer */}
              <div className="flex items-center justify-end gap-3 pt-4">
                <button
                  type="button"
                  onClick={handleClose}
                  className="px-4 py-2 border border-gray-300 text-sm font-medium rounded-md text-gray-700 bg-white hover:bg-gray-50"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  disabled={isSubmitting}
                  className="px-4 py-2 border border-transparent text-sm font-medium rounded-md shadow-sm text-white bg-indigo-600 hover:bg-indigo-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-indigo-500 disabled:bg-gray-400 disabled:cursor-not-allowed"
                >
                  {isSubmitting ? 'Creating...' : 'Create Rule'}
                </button>
              </div>
            </form>
          </div>
        </div>
      </div>
    </>
  );
};

export default CreateLifecycleRuleModal;
