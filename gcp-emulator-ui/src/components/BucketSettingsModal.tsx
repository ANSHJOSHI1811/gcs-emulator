import { useState, useEffect } from 'react';
import { X, Trash2, Plus } from 'lucide-react';
import { ACLValue, LifecycleRule } from '../types';
import { updateBucketACL } from '../api/buckets';
import { listLifecycleRules, deleteLifecycleRule } from '../api/lifecycle';
import toast from 'react-hot-toast';
import CreateLifecycleRuleModal from './CreateLifecycleRuleModal.tsx';

interface BucketSettingsModalProps {
  isOpen: boolean;
  onClose: () => void;
  bucketName: string;
  currentACL: ACLValue;
  onACLUpdate: (newACL: ACLValue) => void;
}

const BucketSettingsModal = ({ isOpen, onClose, bucketName, currentACL, onACLUpdate }: BucketSettingsModalProps) => {
  const [selectedACL, setSelectedACL] = useState<ACLValue>(currentACL);
  const [isUpdatingACL, setIsUpdatingACL] = useState(false);
  const [lifecycleRules, setLifecycleRules] = useState<LifecycleRule[]>([]);
  const [isLoadingRules, setIsLoadingRules] = useState(false);
  const [isCreateRuleModalOpen, setCreateRuleModalOpen] = useState(false);

  useEffect(() => {
    setSelectedACL(currentACL);
  }, [currentACL]);

  useEffect(() => {
    if (isOpen) {
      loadLifecycleRules();
    }
  }, [isOpen, bucketName]);

  const loadLifecycleRules = async () => {
    setIsLoadingRules(true);
    try {
      const rules = await listLifecycleRules(bucketName);
      setLifecycleRules(rules);
    } catch (err) {
      console.error('Failed to load lifecycle rules:', err);
      toast.error('❌ Failed to load lifecycle rules');
    } finally {
      setIsLoadingRules(false);
    }
  };

  const handleUpdateACL = async () => {
    setIsUpdatingACL(true);
    try {
      await updateBucketACL(bucketName, selectedACL);
      onACLUpdate(selectedACL);
      onClose();
    } catch (err) {
      console.error('Failed to update bucket ACL:', err);
      toast.error('❌ Failed to update bucket ACL');
    } finally {
      setIsUpdatingACL(false);
    }
  };

  const handleDeleteRule = async (ruleId: string) => {
    if (!window.confirm('Are you sure you want to delete this lifecycle rule?')) return;
    
    try {
      await deleteLifecycleRule(ruleId);
      toast.success('✅ Lifecycle rule deleted');
      loadLifecycleRules();
    } catch (err) {
      console.error('Failed to delete lifecycle rule:', err);
      toast.error('❌ Failed to delete lifecycle rule');
    }
  };

  if (!isOpen) return null;

  return (
    <>
      <div className="fixed inset-0 bg-gray-500 bg-opacity-75 transition-opacity z-40" onClick={onClose}></div>
      <div className="fixed inset-0 z-50 overflow-y-auto">
        <div className="flex min-h-full items-center justify-center p-4">
          <div className="relative bg-white rounded-lg shadow-xl max-w-2xl w-full max-h-[90vh] overflow-y-auto">
            {/* Header */}
            <div className="flex items-center justify-between p-6 border-b border-gray-200">
              <h3 className="text-lg font-semibold text-gray-900">
                Bucket Settings: <span className="font-mono">{bucketName}</span>
              </h3>
              <button onClick={onClose} className="text-gray-400 hover:text-gray-500">
                <X size={24} />
              </button>
            </div>

            {/* Content */}
            <div className="p-6 space-y-6">
              {/* ACL Section */}
              <div>
                <h4 className="text-md font-semibold text-gray-800 mb-3">Access Control (ACL)</h4>
                <p className="text-sm text-gray-600 mb-3">
                  Control default access permissions for this bucket and its objects.
                </p>
                <div className="space-y-3">
                  <select
                    value={selectedACL}
                    onChange={(e) => setSelectedACL(e.target.value as ACLValue)}
                    className="block w-full pl-3 pr-10 py-2 text-base border-gray-300 focus:outline-none focus:ring-indigo-500 focus:border-indigo-500 sm:text-sm rounded-md"
                  >
                    <option value="private">Private (Authenticated access only)</option>
                    <option value="publicRead">Public Read (Anonymous access allowed)</option>
                  </select>
                  <button
                    onClick={handleUpdateACL}
                    disabled={isUpdatingACL || selectedACL === currentACL}
                    className="inline-flex items-center px-4 py-2 border border-transparent text-sm font-medium rounded-md shadow-sm text-white bg-indigo-600 hover:bg-indigo-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-indigo-500 disabled:bg-gray-400 disabled:cursor-not-allowed"
                  >
                    {isUpdatingACL ? 'Updating...' : 'Update ACL'}
                  </button>
                </div>
              </div>

              {/* Lifecycle Rules Section */}
              <div className="border-t border-gray-200 pt-6">
                <div className="flex items-center justify-between mb-3">
                  <h4 className="text-md font-semibold text-gray-800">Lifecycle Rules</h4>
                  <button
                    onClick={() => setCreateRuleModalOpen(true)}
                    className="inline-flex items-center px-3 py-1.5 border border-transparent text-sm font-medium rounded-md text-white bg-green-600 hover:bg-green-700"
                  >
                    <Plus size={16} className="mr-1" />
                    Add Rule
                  </button>
                </div>
                <p className="text-sm text-gray-600 mb-3">
                  Automatically delete or archive objects after a specified number of days.
                </p>

                {isLoadingRules ? (
                  <div className="flex justify-center py-4">
                    <div className="animate-spin h-6 w-6 border-2 border-indigo-600 border-t-transparent rounded-full"></div>
                  </div>
                ) : lifecycleRules.length === 0 ? (
                  <div className="text-center py-6 bg-gray-50 rounded-lg border-2 border-dashed border-gray-300">
                    <p className="text-sm text-gray-500">No lifecycle rules configured</p>
                  </div>
                ) : (
                  <div className="bg-white shadow rounded-lg overflow-hidden">
                    <table className="min-w-full divide-y divide-gray-200">
                      <thead className="bg-gray-50">
                        <tr>
                          <th scope="col" className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                            Action
                          </th>
                          <th scope="col" className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                            Age (Days)
                          </th>
                          <th scope="col" className="relative px-4 py-3">
                            <span className="sr-only">Actions</span>
                          </th>
                        </tr>
                      </thead>
                      <tbody className="bg-white divide-y divide-gray-200">
                        {lifecycleRules.map((rule) => (
                          <tr key={rule.ruleId}>
                            <td className="px-4 py-3 whitespace-nowrap text-sm font-medium text-gray-900">
                              <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${
                                rule.action === 'Delete' ? 'bg-red-100 text-red-800' : 'bg-yellow-100 text-yellow-800'
                              }`}>
                                {rule.action}
                              </span>
                            </td>
                            <td className="px-4 py-3 whitespace-nowrap text-sm text-gray-500">{rule.ageDays} days</td>
                            <td className="px-4 py-3 whitespace-nowrap text-right text-sm font-medium">
                              <button
                                onClick={() => handleDeleteRule(rule.ruleId)}
                                className="text-red-600 hover:text-red-900"
                              >
                                <Trash2 size={16} />
                              </button>
                            </td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                )}
              </div>
            </div>

            {/* Footer */}
            <div className="flex items-center justify-end p-6 border-t border-gray-200">
              <button
                onClick={onClose}
                className="px-4 py-2 border border-gray-300 text-sm font-medium rounded-md text-gray-700 bg-white hover:bg-gray-50"
              >
                Close
              </button>
            </div>
          </div>
        </div>
      </div>

      <CreateLifecycleRuleModal
        isOpen={isCreateRuleModalOpen}
        onClose={() => setCreateRuleModalOpen(false)}
        bucketName={bucketName}
        onRuleCreated={() => {
          setCreateRuleModalOpen(false);
          loadLifecycleRules();
        }}
      />
    </>
  );
};

export default BucketSettingsModal;
