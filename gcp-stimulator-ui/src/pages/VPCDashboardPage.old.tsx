import { useEffect, useState } from 'react';
import { useProject } from '../contexts/ProjectContext';
import { Network, Globe, Plus, Trash2 } from 'lucide-react';
import { apiClient } from '../api/client';
import { Modal, ModalFooter, ModalButton } from '../components/Modal';
import { FormField, Input } from '../components/FormFields';

interface VPCNetwork {
  name: string;
  id: string;
  autoCreateSubnetworks: boolean;
  dockerNetworkName: string;
  creationTimestamp: string;
}

const VPCDashboardPage = () => {
  const { currentProject } = useProject();
  const [networks, setNetworks] = useState<VPCNetwork[]>([]);
  const [loading, setLoading] = useState(true);
  const [showCreateModal, setShowCreateModal] = useState(false);
  const [createLoading, setCreateLoading] = useState(false);
  const [selectedNetwork, setSelectedNetwork] = useState<VPCNetwork | null>(null);
  const [isDetailsOpen, setDetailsOpen] = useState(false);
  const [actionLoading, setActionLoading] = useState(false);
  const [formData, setFormData] = useState({
    name: '',
    autoCreateSubnetworks: true
  });

  useEffect(() => {
    loadData();
    
    // Auto-refresh every 5 seconds
    const interval = setInterval(() => {
      loadData();
    }, 5000);
    
    return () => clearInterval(interval);
  }, [currentProject]);

  const loadData = async () => {
    try {
      const networksRes = await apiClient.get(`/compute/v1/projects/${currentProject}/global/networks`);
      setNetworks(networksRes.data.items || []);
    } catch (error) {
      console.error('Failed to load VPC networks:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleCreateNetwork = async (e: React.FormEvent) => {
    e.preventDefault();
    setCreateLoading(true);
    try {
      await apiClient.post(
        `/compute/v1/projects/${currentProject}/global/networks`,
        {
          name: formData.name,
          autoCreateSubnetworks: formData.autoCreateSubnetworks
        }
      );
      setShowCreateModal(false);
      setFormData({ name: '', autoCreateSubnetworks: true });
      await loadData();
    } catch (error: any) {
      console.error('Failed to create network:', error);
      alert(error.response?.data?.detail || 'Failed to create network');
    } finally {
      setCreateLoading(false);
    }
  };

  const handleDeleteNetwork = async (networkName: string) => {
    if (networkName === 'default') {
      alert('Cannot delete default network');
      return;
    }
    if (!confirm(`Are you sure you want to delete network "${networkName}"?`)) {
      return;
    }
    try {
      setActionLoading(true);
      await apiClient.delete(
        `/compute/v1/projects/${currentProject}/global/networks/${networkName}`
      );
      await loadData();
    } catch (error: any) {
      console.error('Failed to delete network:', error);
      alert(error.response?.data?.detail || 'Failed to delete network');
    } finally {
      setActionLoading(false);
    }
  };

  const customNetworks = networks.filter(n => n.name !== 'default');

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header Section */}
      <div className="bg-white border-b border-gray-200 shadow-sm">
        <div className="max-w-[1280px] mx-auto px-8 py-6">
          <div className="flex items-center justify-between mb-4">
            <div>
              <div className="flex items-start gap-4 mb-2">
                <div className="p-3 bg-blue-50 rounded-xl">
                  <Network className="w-8 h-8 text-blue-600" />
                </div>
                <div className="flex-1">
                  <h1 className="text-[28px] font-bold text-gray-900 mb-2">VPC Networks</h1>
                  <p className="text-[14px] text-gray-600 leading-relaxed">
                    Virtual Private Cloud networking for your cloud resources
                  </p>
                </div>
              </div>
            </div>
            <button
              onClick={() => setShowCreateModal(true)}
              className="inline-flex items-center gap-2 px-4 h-10 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-all shadow-sm hover:shadow-md text-[13px] font-medium"
            >
              <Plus className="w-4 h-4" />
              Create VPC Network
            </button>
          </div>

          {/* Quick Stats */}
          <div className="flex items-center gap-6 pt-4 border-t border-gray-200">
            <div className="flex items-center gap-2 px-3 py-2">
              <div className="w-2 h-2 bg-blue-500 rounded-full"></div>
              <span className="text-[13px] text-gray-600">
                <span className="font-semibold text-gray-900">{networks.length}</span> Networks
              </span>
            </div>
            <div className="flex items-center gap-2 px-3 py-2">
              <div className="w-2 h-2 bg-green-500 rounded-full"></div>
              <span className="text-[13px] text-gray-600">
                <span className="font-semibold text-gray-900">{customNetworks.length}</span> Custom
              </span>
            </div>
          </div>
        </div>
      </div>

      {/* Main Content */}
      <div className="max-w-[1280px] mx-auto px-8 py-8">
        {/* VPC Networks */}
        <div className="mb-8">
          <h2 className="text-[16px] font-bold text-gray-900 mb-4">VPC Networks</h2>
          <div className="bg-white rounded-lg border border-gray-200 shadow-[0_1px_3px_rgba(0,0,0,0.07)]">
            {loading ? (
              <div className="p-12 text-center">
                <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto"></div>
                <p className="text-gray-600 mt-4">Loading networks...</p>
              </div>
            ) : networks.length === 0 ? (
              <div className="p-12 text-center">
                <Network className="w-16 h-16 text-gray-300 mx-auto mb-4" />
                <h3 className="text-lg font-medium text-gray-900 mb-2">No networks yet</h3>
                <p className="text-gray-600 mb-6">
                  Create a VPC network to get started
                </p>
                <button
                  onClick={() => setShowCreateModal(true)}
                  className="inline-flex items-center gap-2 px-4 h-9 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-all text-[13px] font-medium"
                >
                  <Plus className="w-4 h-4" />
                  Create Your First Network
                </button>
              </div>
            ) : (
              <div className="overflow-x-auto">
                <table className="w-full">
                  <thead className="bg-gray-50 border-b border-gray-200">
                    <tr>
                      <th className="text-left px-6 py-3 text-xs font-medium text-gray-700 uppercase tracking-wider">
                        Name
                      </th>
                      <th className="text-left px-6 py-3 text-xs font-medium text-gray-700 uppercase tracking-wider">
                        Mode
                      </th>
                      <th className="text-left px-6 py-3 text-xs font-medium text-gray-700 uppercase tracking-wider">
                        Docker Network
                      </th>
                      <th className="text-right px-6 py-3 text-xs font-medium text-gray-700 uppercase tracking-wider">
                        Actions
                      </th>
                    </tr>
                  </thead>
                  <tbody className="bg-white divide-y divide-gray-100">
                    {networks.map((network) => (
                      <tr key={network.id} className="hover:bg-gray-50 transition-colors">
                        <td className="px-6 py-4 text-sm font-medium text-gray-900">
                          <button
                            onClick={() => {
                              setSelectedNetwork(network);
                              setDetailsOpen(true);
                            }}
                            className="text-blue-600 hover:text-blue-800 hover:underline flex items-center gap-2"
                          >
                            <Globe className="w-4 h-4 text-gray-400" />
                            <span>{network.name}</span>
                          </button>
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-600">
                          <span className={`px-2 py-1 text-xs font-medium rounded-full ${
                            network.autoCreateSubnetworks 
                              ? 'bg-green-100 text-green-800' 
                              : 'bg-blue-100 text-blue-800'
                          }`}>
                            {network.autoCreateSubnetworks ? 'Auto' : 'Custom'}
                          </span>
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-600 font-mono">
                          {network.dockerNetworkName}
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap text-right text-sm font-medium">
                          {network.name !== 'default' && (
                            <button
                              onClick={() => handleDeleteNetwork(network.name)}
                              disabled={actionLoading}
                              className="text-red-600 hover:text-red-800 transition-colors disabled:opacity-50"
                            >
                              <Trash2 className="w-4 h-4 inline" />
                            </button>
                          )}
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            )}
          </div>
        </div>

        {/* Recent Activity */}
        <div className="mt-8">
          <h2 className="text-[16px] font-bold text-gray-900 mb-4">Recent Activity</h2>
          <div className="bg-white rounded-lg border border-gray-200 shadow-[0_1px_3px_rgba(0,0,0,0.07)]">
            <div className="divide-y divide-gray-200">
              {networks.slice(0, 5).map((network) => (
                <div key={network.id} className="flex items-center justify-between p-4 hover:bg-gray-50 transition-colors">
                  <div className="flex items-center gap-3">
                    <div className="p-2 bg-gray-50 rounded-lg">
                      <Network className="w-4 h-4 text-gray-600" />
                    </div>
                    <div>
                      <p className="text-[13px] font-medium text-gray-900">
                        Network: <span className="text-blue-600">{network.name}</span>
                      </p>
                      <p className="text-[12px] text-gray-500">
                        {network.autoCreateSubnetworks ? 'Auto mode' : 'Custom mode'} • {network.dockerNetworkName}
                      </p>
                    </div>
                  </div>
                  <span className={`px-2 py-1 text-xs font-medium rounded-full ${
                    network.name === 'default' 
                      ? 'bg-gray-100 text-gray-800' 
                      : 'bg-green-100 text-green-800'
                  }`}>
                    {network.name === 'default' ? 'Default' : 'Active'}
                  </span>
                </div>
              ))}
              {networks.length === 0 && (
                <div className="p-8 text-center">
                  <Network className="w-12 h-12 text-gray-300 mx-auto mb-3" />
                  <p className="text-[13px] text-gray-500">No recent activity</p>
                </div>
              )}
            </div>
          </div>
        </div>
      </div>

      {/* Create Network Modal */}
      <Modal
        isOpen={showCreateModal}
        onClose={() => setShowCreateModal(false)}
        title="Create VPC Network"
        description="Create a new Virtual Private Cloud network"
        size="md"
      >
        <form onSubmit={handleCreateNetwork} className="space-y-5">
          <FormField
            label="Network Name"
            required
            help="Lowercase letters, numbers, and hyphens only"
          >
            <Input
              type="text"
              required
              value={formData.name}
              onChange={(e) => setFormData({ ...formData, name: e.target.value })}
              placeholder="my-vpc-network"
              pattern="[a-z0-9-]+"
            />
          </FormField>

          <FormField label="Subnet Creation Mode" required>
            <div className="space-y-3">
              <label className="flex items-start gap-3 p-3 border border-gray-200 rounded-lg cursor-pointer hover:bg-gray-50">
                <input
                  type="radio"
                  name="mode"
                  checked={formData.autoCreateSubnetworks}
                  onChange={() => setFormData({ ...formData, autoCreateSubnetworks: true })}
                  className="mt-1"
                />
                <div>
                  <div className="font-medium text-gray-900 text-sm">Automatic</div>
                  <div className="text-xs text-gray-500">Subnets are created automatically in each region</div>
                </div>
              </label>
              <label className="flex items-start gap-3 p-3 border border-gray-200 rounded-lg cursor-pointer hover:bg-gray-50">
                <input
                  type="radio"
                  name="mode"
                  checked={!formData.autoCreateSubnetworks}
                  onChange={() => setFormData({ ...formData, autoCreateSubnetworks: false })}
                  className="mt-1"
                />
                <div>
                  <div className="font-medium text-gray-900 text-sm">Custom</div>
                  <div className="text-xs text-gray-500">You create and manage subnets manually</div>
                </div>
              </label>
            </div>
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

      {/* Network Details Modal */}
      {selectedNetwork && (
        <Modal
          isOpen={isDetailsOpen}
          onClose={() => {
            setDetailsOpen(false);
            setSelectedNetwork(null);
          }}
          title={selectedNetwork.name}
        >
          <div className="space-y-4">
            {/* Mode Badge */}
            <div className="flex items-center gap-2">
              <span className={`px-3 py-1 text-xs font-medium rounded-full ${
                selectedNetwork.autoCreateSubnetworks 
                  ? 'bg-green-100 text-green-800' 
                  : 'bg-blue-100 text-blue-800'
              }`}>
                {selectedNetwork.autoCreateSubnetworks ? 'Auto Mode' : 'Custom Mode'}
              </span>
            </div>

            {/* Details Grid */}
            <div className="bg-gray-50 rounded-lg p-4 space-y-3">
              <div className="flex justify-between text-sm">
                <span className="text-gray-600">Network ID</span>
                <span className="text-gray-900 font-medium font-mono text-xs">{selectedNetwork.id}</span>
              </div>
              <div className="flex justify-between text-sm border-t border-gray-200 pt-3">
                <span className="text-gray-600">Docker Network</span>
                <span className="text-gray-900 font-mono text-xs">{selectedNetwork.dockerNetworkName}</span>
              </div>
              <div className="flex justify-between text-sm border-t border-gray-200 pt-3">
                <span className="text-gray-600">Subnet Mode</span>
                <span className="text-gray-900 font-medium">{selectedNetwork.autoCreateSubnetworks ? 'Automatic' : 'Custom'}</span>
              </div>
            </div>

            {/* Actions */}
            {selectedNetwork.name !== 'default' && (
              <div className="flex gap-2 pt-2">
                <button
                  onClick={() => {
                    handleDeleteNetwork(selectedNetwork.name);
                    setDetailsOpen(false);
                    setSelectedNetwork(null);
                  }}
                  disabled={actionLoading}
                  className="flex items-center justify-center gap-2 px-4 py-2 bg-red-600 text-white rounded-lg hover:bg-red-700 transition-colors text-sm font-medium disabled:opacity-50 disabled:cursor-not-allowed"
                >
                  {actionLoading ? (
                    <div className="w-4 h-4 border-2 border-white border-t-transparent rounded-full animate-spin"></div>
                  ) : (
                    <Trash2 size={16} />
                  )}
                  Delete Network
                </button>
              </div>
            )}
          </div>
        </Modal>
      )}
    </div>
  );
};

export default VPCDashboardPage;
