import { useEffect, useState } from 'react';
import { useProject } from '../contexts/ProjectContext';
import { Shield, Plus, Users, Clock } from 'lucide-react';
import { apiClient } from '../api/client';
import { Modal, ModalFooter, ModalButton } from '../components/Modal';
import { FormField, Input, Textarea } from '../components/FormFields';

interface ServiceAccount {
  name: string;
  email: string;
  uniqueId: string;
  displayName: string;
  disabled: boolean;
  description?: string;
  projectId: string;
}

const IAMDashboardPage = () => {
  const { currentProject } = useProject();
  const [serviceAccounts, setServiceAccounts] = useState<ServiceAccount[]>([]);
  const [loading, setLoading] = useState(true);
  const [showCreateModal, setShowCreateModal] = useState(false);
  const [showDetailsModal, setShowDetailsModal] = useState(false);
  const [selectedAccount, setSelectedAccount] = useState<ServiceAccount | null>(null);
  const [createLoading, setCreateLoading] = useState(false);
  const [deleteLoading, setDeleteLoading] = useState(false);
  const [formData, setFormData] = useState({
    accountId: '',
    displayName: '',
    description: ''
  });

  useEffect(() => {
    loadServiceAccounts();
    const interval = setInterval(loadServiceAccounts, 5000);
    return () => clearInterval(interval);
  }, [currentProject]);

  const loadServiceAccounts = async () => {
    try {
      const response = await apiClient.get(`/v1/projects/${currentProject}/serviceAccounts`);
      setServiceAccounts(response.data.accounts || []);
    } catch (error) {
      console.error('Failed to load service accounts:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleCreateServiceAccount = async (e: React.FormEvent) => {
    e.preventDefault();
    setCreateLoading(true);
    try {
      await apiClient.post(`/v1/projects/${currentProject}/serviceAccounts`, {
        accountId: formData.accountId,
        serviceAccount: {
          displayName: formData.displayName,
          description: formData.description
        }
      });
      setShowCreateModal(false);
      setFormData({ accountId: '', displayName: '', description: '' });
      await loadServiceAccounts();
    } catch (error: any) {
      console.error('Failed to create service account:', error);
      alert(error.response?.data?.detail || 'Failed to create service account');
    } finally {
      setCreateLoading(false);
    }
  };

  const handleDeleteServiceAccount = async (email: string) => {
    if (!confirm('Are you sure you want to delete this service account?')) return;
    
    setDeleteLoading(true);
    try {
      await apiClient.delete(`/v1/projects/${currentProject}/serviceAccounts/${email}`);
      setShowDetailsModal(false);
      setSelectedAccount(null);
      await loadServiceAccounts();
    } catch (error: any) {
      console.error('Failed to delete service account:', error);
      alert(error.response?.data?.detail || 'Failed to delete service account');
    } finally {
      setDeleteLoading(false);
    }
  };

  const activeAccounts = serviceAccounts.filter(acc => !acc.disabled).length;
  const recentAccounts = [...serviceAccounts].slice(0, 5);

  return (
    <div className="min-h-screen bg-gray-50">
      <div className="max-w-[1280px] mx-auto px-8 py-6">
        {/* Modern Header */}
        <div className="bg-white rounded-lg shadow-[0_1px_3px_rgba(0,0,0,0.07)] px-8 py-6 mb-6">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-4">
              <Shield className="w-8 h-8 text-blue-600" />
              <div>
                <h1 className="text-2xl font-semibold text-gray-900">IAM & Admin</h1>
                <p className="text-sm text-gray-500 mt-1">Manage service accounts and access control</p>
              </div>
            </div>
            <button
              onClick={() => setShowCreateModal(true)}
              className="flex items-center gap-2 px-4 py-2 bg-blue-600 text-white text-sm font-medium rounded-md hover:bg-blue-700 transition-colors"
            >
              <Plus className="w-4 h-4" />
              Create Service Account
            </button>
          </div>
        </div>

        {/* Quick Stats Breadcrumbs */}
        <div className="flex items-center gap-4 mb-6 text-sm">
          <div className="flex items-center gap-2">
            <span className="text-gray-600">Service Accounts:</span>
            <span className="px-3 py-1 bg-blue-50 text-blue-700 font-semibold rounded-md">
              {serviceAccounts.length}
            </span>
          </div>
          <div className="flex items-center gap-2">
            <span className="text-gray-600">Active:</span>
            <span className="px-3 py-1 bg-green-50 text-green-700 font-semibold rounded-md">
              {activeAccounts}
            </span>
          </div>
        </div>

        {/* Service Accounts Table */}
        <div className="bg-white rounded-lg shadow-[0_1px_3px_rgba(0,0,0,0.07)] mb-6">
          <div className="px-6 py-4 border-b border-gray-200">
            <h2 className="text-base font-semibold text-gray-900">Service Accounts</h2>
          </div>

          {loading ? (
            <div className="p-12 text-center">
              <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto"></div>
              <p className="text-gray-600 mt-4 text-sm">Loading service accounts...</p>
            </div>
          ) : serviceAccounts.length === 0 ? (
            <div className="p-12 text-center">
              <Shield className="w-16 h-16 text-gray-300 mx-auto mb-4" />
              <h3 className="text-base font-medium text-gray-900 mb-2">No service accounts</h3>
              <p className="text-sm text-gray-500 mb-6">
                Create a service account to manage API access
              </p>
            </div>
          ) : (
            <div className="overflow-x-auto">
              <table className="min-w-full divide-y divide-gray-200">
                <thead className="bg-gray-50">
                  <tr>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      Email
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      Display Name
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      Status
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      Actions
                    </th>
                  </tr>
                </thead>
                <tbody className="bg-white divide-y divide-gray-200">
                  {serviceAccounts.map((account) => (
                    <tr key={account.uniqueId} className="hover:bg-gray-50 transition-colors">
                      <td className="px-6 py-4 whitespace-nowrap">
                        <button
                          onClick={() => {
                            setSelectedAccount(account);
                            setShowDetailsModal(true);
                          }}
                          className="flex items-center text-blue-600 hover:text-blue-700 font-medium text-sm"
                        >
                          <Users className="w-4 h-4 mr-2 text-gray-400" />
                          {account.email}
                        </button>
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-600">
                        {account.displayName || '-'}
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap">
                        <span
                          className={`px-2 py-1 text-xs font-medium rounded-full ${
                            account.disabled
                              ? 'bg-red-100 text-red-800'
                              : 'bg-green-100 text-green-800'
                          }`}
                        >
                          {account.disabled ? 'Disabled' : 'Active'}
                        </span>
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm">
                        <button
                          onClick={() => handleDeleteServiceAccount(account.email)}
                          disabled={deleteLoading}
                          className="text-red-600 hover:text-red-700 font-medium disabled:opacity-50"
                        >
                          Delete
                        </button>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </div>

        {/* Recent Activity */}
        {recentAccounts.length > 0 && (
          <div className="bg-white rounded-lg shadow-[0_1px_3px_rgba(0,0,0,0.07)]">
            <div className="px-6 py-4 border-b border-gray-200">
              <h2 className="text-base font-semibold text-gray-900 flex items-center gap-2">
                <Clock className="w-4 h-4" />
                Recent Activity
              </h2>
            </div>
            <div className="p-6">
              <div className="space-y-3">
                {recentAccounts.map((account, index) => (
                  <div
                    key={account.uniqueId}
                    className="flex items-center justify-between py-3 border-b border-gray-100 last:border-0"
                  >
                    <div className="flex items-center gap-3">
                      <div className="w-8 h-8 bg-blue-50 rounded-full flex items-center justify-center">
                        <Users className="w-4 h-4 text-blue-600" />
                      </div>
                      <div>
                        <p className="text-sm font-medium text-gray-900">{account.email}</p>
                        <p className="text-xs text-gray-500">{account.displayName || 'No display name'}</p>
                      </div>
                    </div>
                    <span
                      className={`px-2 py-1 text-xs font-medium rounded-full ${
                        account.disabled
                          ? 'bg-red-100 text-red-800'
                          : 'bg-green-100 text-green-800'
                      }`}
                    >
                      {account.disabled ? 'Disabled' : 'Active'}
                    </span>
                  </div>
                ))}
              </div>
            </div>
          </div>
        )}
      </div>

      {/* Create Service Account Modal */}
      <Modal
        isOpen={showCreateModal}
        onClose={() => setShowCreateModal(false)}
        title="Create Service Account"
        description="Create a new service account for API access"
        size="md"
      >
        <form onSubmit={handleCreateServiceAccount} className="space-y-5">
          <FormField
            label="Account ID"
            required
            help="Lowercase letters, numbers, and hyphens only"
          >
            <Input
              type="text"
              required
              value={formData.accountId}
              onChange={(e) => setFormData({ ...formData, accountId: e.target.value })}
              placeholder="my-service-account"
              pattern="[a-z0-9-]+"
            />
          </FormField>

          <FormField label="Display Name">
            <Input
              type="text"
              value={formData.displayName}
              onChange={(e) => setFormData({ ...formData, displayName: e.target.value })}
              placeholder="My Service Account"
            />
          </FormField>

          <FormField label="Description">
            <Textarea
              value={formData.description}
              onChange={(e) => setFormData({ ...formData, description: e.target.value })}
              rows={3}
              placeholder="Service account description..."
            />
          </FormField>

          <ModalFooter>
            <ModalButton
              variant="secondary"
              onClick={() => setShowCreateModal(false)}
            >
              Cancel
            </ModalButton>
            <ModalButton
              variant="primary"
              type="submit"
              loading={createLoading}
            >
              Create
            </ModalButton>
          </ModalFooter>
        </form>
      </Modal>

      {/* Service Account Details Modal */}
      {selectedAccount && (
        <Modal
          isOpen={showDetailsModal}
          onClose={() => {
            setShowDetailsModal(false);
            setSelectedAccount(null);
          }}
          title="Service Account Details"
          description={selectedAccount.email}
          size="md"
        >
          <div className="space-y-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">Email</label>
              <p className="text-sm text-gray-900 bg-gray-50 p-3 rounded-md font-mono">
                {selectedAccount.email}
              </p>
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">Display Name</label>
              <p className="text-sm text-gray-900">{selectedAccount.displayName || '-'}</p>
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">Unique ID</label>
              <p className="text-sm text-gray-900 bg-gray-50 p-3 rounded-md font-mono">
                {selectedAccount.uniqueId}
              </p>
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">Project</label>
              <p className="text-sm text-gray-900">{selectedAccount.projectId}</p>
            </div>

            {selectedAccount.description && (
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Description</label>
                <p className="text-sm text-gray-600">{selectedAccount.description}</p>
              </div>
            )}

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">Status</label>
              <span
                className={`inline-flex px-2 py-1 text-xs font-medium rounded-full ${
                  selectedAccount.disabled
                    ? 'bg-red-100 text-red-800'
                    : 'bg-green-100 text-green-800'
                }`}
              >
                {selectedAccount.disabled ? 'Disabled' : 'Active'}
              </span>
            </div>
          </div>

          <ModalFooter>
            <ModalButton
              variant="danger"
              onClick={() => handleDeleteServiceAccount(selectedAccount.email)}
              loading={deleteLoading}
            >
              Delete Service Account
            </ModalButton>
            <ModalButton
              variant="secondary"
              onClick={() => {
                setShowDetailsModal(false);
                setSelectedAccount(null);
              }}
            >
              Close
            </ModalButton>
          </ModalFooter>
        </Modal>
      )}
    </div>
  );
};

export default IAMDashboardPage;
