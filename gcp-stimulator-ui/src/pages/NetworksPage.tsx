import { useEffect, useState } from 'react';
import { useProject } from '../contexts/ProjectContext';
import { Link } from 'react-router-dom';
import { Globe, Plus, Trash2, RefreshCw, AlertCircle, Network, HelpCircle } from 'lucide-react';
import { Modal, ModalFooter, ModalButton } from '../components/Modal';
import { FormField, Input, RadioGroup } from '../components/FormFields';
import { listNetworks, createNetwork, deleteNetwork } from '../api/networking';
import { validateCIDR, calculateUsableIPs, getGatewayIP } from '../utils/cidr';

interface Network {
  id: number;
  name: string;
  autoCreateSubnetworks: boolean;
  IPv4Range?: string;
  creationTimestamp?: string;
  selfLink?: string;
  dockerNetworkName?: string;
}

const NetworksPage = () => {
  const { currentProject } = useProject();
  const [networks, setNetworks] = useState<Network[]>([]);
  const [loading, setLoading] = useState(true);
  const [showCreateModal, setShowCreateModal] = useState(false);
  const [createLoading, setCreateLoading] = useState(false);
  const [deleteLoading, setDeleteLoading] = useState<string | null>(null);
  const [formData, setFormData] = useState({
    name: '',
    autoCreateSubnetworks: true,
    IPv4Range: '10.128.0.0/16',
  });
  const [cidrError, setCidrError] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    loadNetworks();
    
    // Auto-refresh every 3 seconds to match compute page
    const interval = setInterval(() => {
      loadNetworks();
    }, 3000);
    
    return () => clearInterval(interval);
  }, [currentProject]);

  const loadNetworks = async () => {
    try {
      setLoading(true);
      setError(null);
      const networksList = await listNetworks(currentProject);
      setNetworks(networksList as any);
    } catch (error: any) {
      console.error('Failed to load networks:', error);
      setError('Failed to load networks. Please try again.');
    } finally {
      setLoading(false);
    }
  };

  const handleCreate = async (e: React.FormEvent) => {
    e.preventDefault();
    setCreateLoading(true);
    setError(null);
    setCidrError(null);

    // Validate CIDR if provided and custom mode
    if (!formData.autoCreateSubnetworks && formData.IPv4Range) {
      const validation = validateCIDR(formData.IPv4Range);
      if (!validation.valid) {
        setCidrError(validation.error || 'Invalid CIDR');
        setCreateLoading(false);
        return;
      }
    }

    try {
      await createNetwork(currentProject, {
        name: formData.name,
        autoCreateSubnetworks: formData.autoCreateSubnetworks,
        IPv4Range: !formData.autoCreateSubnetworks ? formData.IPv4Range : undefined,
      });

      setShowCreateModal(false);
      setFormData({
        name: '',
        autoCreateSubnetworks: true,
        IPv4Range: '10.128.0.0/16',
      });
      setCidrError(null);
      await loadNetworks();
    } catch (error: any) {
      console.error('Failed to create network:', error);
      setError(error.response?.data?.detail || 'Failed to create network');
    } finally {
      setCreateLoading(false);
    }
  };

  const handleDelete = async (networkName: string) => {
    if (!confirm(`Are you sure you want to delete network "${networkName}"?`)) {
      return;
    }

    setDeleteLoading(networkName);
    setError(null);

    try {
      await deleteNetwork(currentProject, networkName);
      await loadNetworks();
    } catch (error: any) {
      console.error('Failed to delete network:', error);
      setError(error.response?.data?.detail || 'Failed to delete network');
    } finally {
      setDeleteLoading(null);
    }
  };

  return (
    <div className="h-full flex flex-col bg-gray-50">
      {/* Header */}
      <div className="bg-white border-b border-gray-200 px-8 py-6">
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-2xl font-semibold text-gray-900">VPC Networks</h1>
            <p className="text-sm text-gray-500 mt-1">
              Manage your Virtual Private Cloud networks • <Link to="/services/vpc/subnets" className="text-blue-600 hover:underline">View Subnets</Link> • <Link to="/services/compute-engine" className="text-blue-600 hover:underline">View Instances</Link>
            </p>
          </div>
          <div className="flex items-center gap-3">
            <button
              onClick={loadNetworks}
              disabled={loading}
              className="flex items-center gap-2 px-4 py-2 text-sm font-medium text-gray-700 bg-white border border-gray-300 rounded-lg hover:bg-gray-50 disabled:opacity-50"
            >
              <RefreshCw className={`w-4 h-4 ${loading ? 'animate-spin' : ''}`} />
              Refresh
            </button>
            <button
              onClick={() => setShowCreateModal(true)}
              className="flex items-center gap-2 px-4 py-2 text-sm font-medium text-white bg-blue-600 rounded-lg hover:bg-blue-700"
            >
              <Plus className="w-4 h-4" />
              Create Network
            </button>
          </div>
        </div>
      </div>

      {/* Error Message */}
      {error && (
        <div className="mx-8 mt-4 p-4 bg-red-50 border border-red-200 rounded-lg flex items-start gap-3">
          <AlertCircle className="w-5 h-5 text-red-600 flex-shrink-0 mt-0.5" />
          <div className="flex-1">
            <h3 className="text-sm font-medium text-red-800">Error</h3>
            <p className="text-sm text-red-700 mt-1">{error}</p>
          </div>
          <button
            onClick={() => setError(null)}
            className="text-red-600 hover:text-red-800"
          >
            ×
          </button>
        </div>
      )}

      {/* Content */}
      <div className="flex-1 overflow-auto p-8">
        {loading ? (
          <div className="flex items-center justify-center h-64">
            <div className="text-gray-500">Loading networks...</div>
          </div>
        ) : networks.length === 0 ? (
          <div className="flex flex-col items-center justify-center h-64 bg-white rounded-lg border border-gray-200">
            <Globe className="w-12 h-12 text-gray-400 mb-4" />
            <h3 className="text-lg font-medium text-gray-900 mb-2">No networks found</h3>
            <p className="text-sm text-gray-500 mb-4">Create your first VPC network to get started</p>
            <button
              onClick={() => setShowCreateModal(true)}
              className="flex items-center gap-2 px-4 py-2 text-sm font-medium text-white bg-blue-600 rounded-lg hover:bg-blue-700"
            >
              <Plus className="w-4 h-4" />
              Create Network
            </button>
          </div>
        ) : (
          <div className="bg-white rounded-lg border border-gray-200 overflow-hidden">
            <table className="min-w-full divide-y divide-gray-200">
              <thead className="bg-gray-50">
                <tr>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Name
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Subnet Mode
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    CIDR Range
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Docker Network
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Created
                  </th>
                  <th className="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Actions
                  </th>
                </tr>
              </thead>
              <tbody className="bg-white divide-y divide-gray-200">
                {networks.map((network) => (
                  <tr key={network.id} className="hover:bg-gray-50">
                    <td className="px-6 py-4 whitespace-nowrap">
                      <div className="flex items-center">
                        <Globe className="w-5 h-5 text-blue-600 mr-3" />
                        <div>
                          <div className="text-sm font-medium text-gray-900">{network.name}</div>
                          <div className="text-xs text-gray-500">ID: {network.id}</div>
                        </div>
                      </div>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap">
                      <span className={`inline-flex px-2 py-1 text-xs font-semibold rounded-full ${
                        network.autoCreateSubnetworks
                          ? 'bg-green-100 text-green-800'
                          : 'bg-blue-100 text-blue-800'
                      }`}>
                        {network.autoCreateSubnetworks ? 'Auto' : 'Custom'}
                      </span>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap">
                      {network.IPv4Range ? (
                        <div>
                          <div className="text-sm text-gray-900 font-mono">{network.IPv4Range}</div>
                          <div className="text-xs text-gray-500">
                            {calculateUsableIPs(network.IPv4Range).toLocaleString()} usable IPs
                          </div>
                        </div>
                      ) : (
                        <span className="text-sm text-gray-400">-</span>
                      )}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap">
                      <div className="text-sm text-gray-600 font-mono">{network.dockerNetworkName || '-'}</div>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap">
                      <div className="text-sm text-gray-500">
                        {network.creationTimestamp 
                          ? new Date(network.creationTimestamp).toLocaleDateString()
                          : '-'}
                      </div>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-right text-sm font-medium">
                      <div className="flex items-center justify-end gap-2">
                        <Link
                          to={`/services/vpc/subnets?network=${network.name}`}
                          className="text-blue-600 hover:text-blue-900 flex items-center gap-1"
                          title="View subnets"
                        >
                          <Network className="w-4 h-4" />
                          <span className="text-xs">Subnets</span>
                        </Link>
                        <button
                          onClick={() => handleDelete(network.name)}
                          disabled={deleteLoading === network.name || network.name === 'default'}
                          className="text-red-600 hover:text-red-900 disabled:opacity-50 disabled:cursor-not-allowed"
                          title={network.name === 'default' ? 'Cannot delete default network' : 'Delete network'}
                        >
                          <Trash2 className="w-4 h-4" />
                        </button>
                      </div>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>

      {/* Create Modal */}
      <Modal
        isOpen={showCreateModal}
        onClose={() => setShowCreateModal(false)}
        title="Create VPC Network"
        description="Configure a new virtual private cloud network"
        size="lg"
      >
        <form onSubmit={handleCreate} className="space-y-5">
          <FormField
            label="Network Name"
            required
            help="Lowercase letters, numbers, and hyphens only"
          >
            <Input
              type="text"
              value={formData.name}
              onChange={(e) => setFormData({ ...formData, name: e.target.value.toLowerCase() })}
              placeholder="my-network"
              required
            />
          </FormField>

          <FormField label="Subnet Creation Mode">
            <div className="mb-3 p-4 bg-gradient-to-r from-blue-50 to-indigo-50 border border-blue-200 rounded-xl flex items-start gap-3 shadow-sm">
              <HelpCircle className="w-5 h-5 text-blue-600 mt-0.5 flex-shrink-0" />
              <div className="text-sm text-blue-900 space-y-2">
                <div>
                  <strong className="font-semibold">🔷 Auto Mode:</strong> 
                  <span className="ml-1">Automatically creates one /20 subnet in each of 16 GCP regions using the fixed CIDR range 10.128.0.0/9. Best for quick setup and multi-region deployments.</span>
                </div>
                <div>
                  <strong className="font-semibold">🔧 Custom Mode:</strong> 
                  <span className="ml-1">You define your own CIDR range and manually create subnets in specific regions. Ideal for precise IP management and isolated deployments.</span>
                </div>
              </div>
            </div>
            <RadioGroup
              name="subnetMode"
              value={formData.autoCreateSubnetworks.toString()}
              onChange={(value) => {
                setFormData({ 
                  ...formData, 
                  autoCreateSubnetworks: value === 'true',
                  IPv4Range: value === 'true' ? '10.128.0.0/9' : '10.0.0.0/16'
                });
                setCidrError(null);
              }}
              options={[
                {
                  value: 'true',
                  label: 'Automatic (Auto Mode)',
                  description: '16 subnets auto-created | Fixed CIDR: 10.128.0.0/9'
                },
                {
                  value: 'false',
                  label: 'Custom (Manual Control)',
                  description: 'Define your own CIDR and create subnets manually'
                }
              ]}
            />
          </FormField>

          {formData.autoCreateSubnetworks && (
            <FormField 
              label="VPC CIDR Range" 
              help="This CIDR is fixed for auto-mode networks and covers all 16 regional subnets"
            >
              <div className="relative">
                <Input
                  type="text"
                  value="10.128.0.0/9"
                  disabled
                  className="bg-gray-100 cursor-not-allowed text-gray-600 font-mono"
                />
                <div className="absolute right-3 top-1/2 -translate-y-1/2 bg-blue-100 text-blue-700 px-2 py-1 rounded text-xs font-semibold">
                  READ-ONLY
                </div>
              </div>
              <div className="mt-2 p-3 bg-green-50 border border-green-200 rounded-lg">
                <p className="text-xs text-green-800">
                  <strong>✓ Auto-Mode Benefit:</strong> 16 /20 subnets (4,096 IPs each) will be automatically created across all major GCP regions: us-central1, us-east1, europe-west1, asia-east1, and more.
                </p>
              </div>
            </FormField>
          )}

          {!formData.autoCreateSubnetworks && (
            <FormField
              label="IPv4 CIDR Range"
              required
              help="Private IP range for the VPC (e.g., 10.0.0.0/16)"
              error={cidrError || undefined}
            >
              <Input
                type="text"
                value={formData.IPv4Range}
                onChange={(e) => {
                  setFormData({ ...formData, IPv4Range: e.target.value });
                  setCidrError(null);
                }}
                placeholder="10.0.0.0/16"
                required
                onBlur={() => {
                  if (formData.IPv4Range) {
                    const validation = validateCIDR(formData.IPv4Range);
                    if (!validation.valid) {
                      setCidrError(validation.error || null);
                    }
                  }
                }}
              />
              {formData.IPv4Range && !cidrError && (
                <div className="mt-2 text-xs text-gray-600">
                  Gateway: {getGatewayIP(formData.IPv4Range)} • {calculateUsableIPs(formData.IPv4Range).toLocaleString()} usable IPs
                </div>
              )}
            </FormField>
          )}

          <ModalFooter>
            <ModalButton
              variant="secondary"
              onClick={() => setShowCreateModal(false)}
              disabled={createLoading}
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
    </div>
  );
};

export default NetworksPage;
