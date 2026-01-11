import { useEffect, useState } from 'react';
import { Shield, Key, Users, Lock } from 'lucide-react';
import { apiClient } from '../api/client';

interface ServiceAccount {
  name: string;
  email: string;
  uniqueId: string;
  displayName: string;
  disabled: boolean;
}

const IAMDashboardPage = () => {
  const [serviceAccounts, setServiceAccounts] = useState<ServiceAccount[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    loadServiceAccounts();
  }, []);

  const loadServiceAccounts = async () => {
    try {
      const response = await apiClient.get('/v1/projects/demo-project/serviceAccounts');
      setServiceAccounts(response.data.accounts || []);
    } catch (error) {
      console.error('Failed to load service accounts:', error);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="p-6 max-w-7xl mx-auto">
      {/* Header */}
      <div className="mb-8">
        <h1 className="text-3xl font-semibold text-gray-900 flex items-center gap-3">
          <Shield className="w-8 h-8 text-blue-600" />
          IAM & Admin
        </h1>
        <p className="text-gray-600 mt-2">
          Manage identity and access control for your GCP resources
        </p>
      </div>

      {/* Quick Stats */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-6 mb-8">
        <div className="bg-white rounded-lg border border-gray-200 p-6">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm text-gray-600">Service Accounts</p>
              <p className="text-2xl font-semibold text-gray-900 mt-1">
                {serviceAccounts.length}
              </p>
            </div>
            <Users className="w-8 h-8 text-blue-500" />
          </div>
        </div>

        <div className="bg-white rounded-lg border border-gray-200 p-6">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm text-gray-600">Active Keys</p>
              <p className="text-2xl font-semibold text-gray-900 mt-1">0</p>
            </div>
            <Key className="w-8 h-8 text-green-500" />
          </div>
        </div>

        <div className="bg-white rounded-lg border border-gray-200 p-6">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm text-gray-600">IAM Policies</p>
              <p className="text-2xl font-semibold text-gray-900 mt-1">0</p>
            </div>
            <Lock className="w-8 h-8 text-purple-500" />
          </div>
        </div>

        <div className="bg-white rounded-lg border border-gray-200 p-6">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm text-gray-600">Roles</p>
              <p className="text-2xl font-semibold text-gray-900 mt-1">5</p>
            </div>
            <Shield className="w-8 h-8 text-orange-500" />
          </div>
        </div>
      </div>

      {/* Service Accounts List */}
      <div className="bg-white rounded-lg border border-gray-200">
        <div className="px-6 py-4 border-b border-gray-200">
          <h2 className="text-lg font-semibold text-gray-900">Service Accounts</h2>
          <p className="text-sm text-gray-600 mt-1">
            Manage service accounts and their access permissions
          </p>
        </div>

        {loading ? (
          <div className="p-12 text-center">
            <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto"></div>
            <p className="text-gray-600 mt-4">Loading service accounts...</p>
          </div>
        ) : serviceAccounts.length === 0 ? (
          <div className="p-12 text-center">
            <Shield className="w-16 h-16 text-gray-300 mx-auto mb-4" />
            <h3 className="text-lg font-medium text-gray-900 mb-2">No service accounts yet</h3>
            <p className="text-gray-600 mb-6">
              Create a service account to get started with IAM
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
                    Unique ID
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Status
                  </th>
                </tr>
              </thead>
              <tbody className="bg-white divide-y divide-gray-200">
                {serviceAccounts.map((account) => (
                  <tr key={account.uniqueId} className="hover:bg-gray-50">
                    <td className="px-6 py-4 whitespace-nowrap">
                      <div className="flex items-center">
                        <Users className="w-5 h-5 text-gray-400 mr-3" />
                        <span className="text-sm font-medium text-gray-900">
                          {account.email}
                        </span>
                      </div>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-600">
                      {account.displayName || '-'}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                      {account.uniqueId}
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
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>

      {/* API Endpoints Info */}
      <div className="mt-8 bg-blue-50 border border-blue-200 rounded-lg p-6">
        <h3 className="text-lg font-semibold text-blue-900 mb-3">Available IAM APIs</h3>
        <div className="space-y-2 text-sm">
          <div className="flex items-start">
            <code className="bg-blue-100 px-2 py-1 rounded text-blue-900 mr-3">GET</code>
            <span className="text-blue-800">/v1/projects/{'{project}'}/serviceAccounts</span>
          </div>
          <div className="flex items-start">
            <code className="bg-blue-100 px-2 py-1 rounded text-blue-900 mr-3">POST</code>
            <span className="text-blue-800">/v1/projects/{'{project}'}/serviceAccounts</span>
          </div>
          <div className="flex items-start">
            <code className="bg-blue-100 px-2 py-1 rounded text-blue-900 mr-3">GET</code>
            <span className="text-blue-800">/v1/projects/{'{project}'}/serviceAccounts/{'{email}'}/keys</span>
          </div>
        </div>
      </div>
    </div>
  );
};

export default IAMDashboardPage;
