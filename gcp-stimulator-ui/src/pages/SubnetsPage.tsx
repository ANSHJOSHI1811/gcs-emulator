import { useEffect, useState } from 'react';
import { useProject } from '../contexts/ProjectContext';
import { Link, useSearchParams } from 'react-router-dom';
import { Network, Plus, Trash2, RefreshCw, AlertCircle, CheckCircle, Globe, ArrowLeft } from 'lucide-react';
import { Modal, ModalFooter, ModalButton } from '../components/Modal';
import { FormField, Input, Select } from '../components/FormFields';
import { listNetworks, listSubnets, createSubnet, deleteSubnet } from '../api/networking';
import { validateCIDR, calculateUsableIPs, getGatewayIP, isSubnetWithinVPC } from '../utils/cidr';

interface Subnet {
  id: string;
  name: string;
  network: string;
  region: string;
  ipCidrRange: string;
  gatewayAddress?: string;
  privateIpGoogleAccess?: boolean;
  creationTimestamp?: string;
}

interface NetworkOption {
  name: string;
  selfLink: string;
  IPv4Range?: string;
}

const SubnetsPage = () => {
  const { currentProject } = useProject();
  const [searchParams] = useSearchParams();
  const networkFilter = searchParams.get('network');
  const [subnets, setSubnets] = useState<Subnet[]>([]);
  const [networks, setNetworks] = useState<NetworkOption[]>([]);
  const [loading, setLoading] = useState(true);
  const [showCreateModal, setShowCreateModal] = useState(false);
  const [createLoading, setCreateLoading] = useState(false);
  const [deleteLoading, setDeleteLoading] = useState<string | null>(null);
  const [formData, setFormData] = useState({
    name: '',
    network: '',
    region: 'us-central1',
    ipCidrRange: '',
    privateIpGoogleAccess: false,
  });
  const [error, setError] = useState<string | null>(null);
  const [cidrError, setCidrError] = useState<string | null>(null);
  const [cidrValid, setCidrValid] = useState<boolean>(false);

  // Pre-select network if coming from Networks page
  useEffect(() => {
    if (networkFilter && networks.length > 0) {
      const matchingNetwork = networks.find(n => n.name === networkFilter);
      if (matchingNetwork) {
        setFormData(prev => ({ ...prev, network: matchingNetwork.selfLink }));
      }
    }
  }, [networkFilter, networks]);

  const regions = [
    'us-central1', 'us-east1', 'us-west1', 'us-west2',
    'europe-west1', 'europe-west2', 'asia-east1', 'asia-southeast1'
  ];

  useEffect(() => {
    loadData();
  }, [currentProject]);

  const loadData = async () => {
    try {
      setLoading(true);
      setError(null);

      // Load networks
      const networksList = await listNetworks(currentProject);
      setNetworks(networksList as any);

      // Load subnets from all regions
      const subnetsList = await listSubnets(currentProject);
      const allSubnets = subnetsList as any;
      
      // Filter by network if specified in URL
      if (networkFilter) {
        const filtered = allSubnets.filter((s: Subnet) => {
          const subnetNetwork = s.network.split('/').pop();
          return subnetNetwork === networkFilter;
        });
        setSubnets(filtered);
      } else {
        setSubnets(allSubnets);
      }
    } catch (error: any) {
      console.error('Failed to load subnets:', error);
      setError('Failed to load subnets. Please try again.');
    } finally {
      setLoading(false);
    }
  };

  const handleCreate = async (e: React.FormEvent) => {
    e.preventDefault();
    setCreateLoading(true);
    setError(null);
    setCidrError(null);

    // Validate CIDR
    const validation = validateCIDR(formData.ipCidrRange);
    if (!validation.valid) {
      setCidrError(validation.error || 'Invalid CIDR');
      setCreateLoading(false);
      return;
    }

    // Check if subnet is within VPC CIDR
    const selectedNetwork = networks.find(n => n.selfLink === formData.network);
    if (selectedNetwork?.IPv4Range) {
      if (!isSubnetWithinVPC(selectedNetwork.IPv4Range, formData.ipCidrRange)) {
        setCidrError(`Subnet must be within VPC CIDR range ${selectedNetwork.IPv4Range}`);
        setCreateLoading(false);
        return;
      }
    }

    try {
      await createSubnet(currentProject, formData.region, {
        name: formData.name,
        network: formData.network,
        region: formData.region,
        ipCidrRange: formData.ipCidrRange,
      });

      setShowCreateModal(false);
      setFormData({
        name: '',
        network: '',
        region: 'us-central1',
        ipCidrRange: '',
        privateIpGoogleAccess: false,
      });
      setCidrError(null);
      setCidrValid(false);
      await loadData();
    } catch (error: any) {
      console.error('Failed to create subnet:', error);
      setError(error.response?.data?.detail || error.message || 'Failed to create subnet');
    } finally {
      setCreateLoading(false);
    }
  };

  const handleDelete = async (region: string, subnetName: string) => {
    if (!confirm(`Are you sure you want to delete subnet "${subnetName}"?`)) {
      return;
    }

    setDeleteLoading(subnetName);
    setError(null);

    try {
      await deleteSubnet(currentProject, region, subnetName);
      await loadData();
    } catch (error: any) {
      console.error('Failed to delete subnet:', error);
      setError(error.response?.data?.detail || error.message || 'Failed to delete subnet');
    } finally {
      setDeleteLoading(null);
    }
  };

  const extractNetworkName = (networkUrl: string): string => {
    if (!networkUrl) return '-';
    const parts = networkUrl.split('/');
    return parts[parts.length - 1] || networkUrl;
  };

  return (
    <div className="h-full flex flex-col bg-gray-50">
      {/* Header */}
      <div className="bg-white border-b border-gray-200 px-8 py-6">
        <div className="flex items-center justify-between">
          <div>
            <div className="flex items-center gap-3 mb-2">
              <Link to="/services/vpc/networks" className="text-gray-500 hover:text-gray-700">
                <ArrowLeft className="w-5 h-5" />
              </Link>
              <h1 className="text-2xl font-semibold text-gray-900">Subnets</h1>
            </div>
            <p className="text-sm text-gray-500">
              {networkFilter ? (
                <>
                  Showing subnets for network: <span className="font-semibold text-gray-900">{networkFilter}</span> • <Link to="/services/vpc/subnets" className="text-blue-600 hover:underline">Show all</Link>
                </>
              ) : (
                <>
                  Manage subnet IP ranges for your VPC networks • <Link to="/services/vpc/networks" className="text-blue-600 hover:underline">View Networks</Link>
                </>
              )}
            </p>
          </div>
          <div className="flex items-center gap-3">
            <button
              onClick={loadData}
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
              Create Subnet
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
            <div className="text-gray-500">Loading subnets...</div>
          </div>
        ) : subnets.length === 0 ? (
          <div className="flex flex-col items-center justify-center h-64 bg-white rounded-lg border border-gray-200">
            <Network className="w-12 h-12 text-gray-400 mb-4" />
            <h3 className="text-lg font-medium text-gray-900 mb-2">No subnets found</h3>
            <p className="text-sm text-gray-500 mb-4">Create your first subnet to get started</p>
            <button
              onClick={() => setShowCreateModal(true)}
              className="flex items-center gap-2 px-4 py-2 text-sm font-medium text-white bg-blue-600 rounded-lg hover:bg-blue-700"
            >
              <Plus className="w-4 h-4" />
              Create Subnet
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
                    Network
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Region
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    IP Range
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Available IPs
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Gateway
                  </th>
                  <th className="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Actions
                  </th>
                </tr>
              </thead>
              <tbody className="bg-white divide-y divide-gray-200">
                {subnets.map((subnet) => (
                  <tr key={subnet.id} className="hover:bg-gray-50">
                    <td className="px-6 py-4 whitespace-nowrap">
                      <div className="flex items-center">
                        <Network className="w-5 h-5 text-green-600 mr-3" />
                        <div>
                          <div className="text-sm font-medium text-gray-900">{subnet.name}</div>
                          <div className="text-xs text-gray-500">{subnet.id}</div>
                        </div>
                      </div>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap">
                      <div className="text-sm text-gray-900">{extractNetworkName(subnet.network)}</div>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap">
                      <div className="text-sm text-gray-900">{subnet.region}</div>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap">
                      <div className="text-sm font-mono text-gray-900">{subnet.ipCidrRange}</div>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap">
                      <div className="text-sm text-gray-900">
                        {calculateUsableIPs(subnet.ipCidrRange).toLocaleString()}
                      </div>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap">
                      <div className="text-sm font-mono text-gray-900">{subnet.gatewayAddress || getGatewayIP(subnet.ipCidrRange)}</div>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-right text-sm font-medium">
                      <button
                        onClick={() => handleDelete(subnet.region, subnet.name)}
                        disabled={deleteLoading === subnet.name}
                        className="text-red-600 hover:text-red-900 disabled:opacity-50"
                      >
                        <Trash2 className="w-4 h-4" />
                      </button>
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
        title="Create Subnet"
        description="Add a new subnet to your VPC network"
        size="lg"
      >
        <form onSubmit={handleCreate} className="space-y-5">
          <FormField
            label="Name"
            required
            help="Lowercase letters, numbers, and hyphens only"
          >
            <Input
              type="text"
              value={formData.name}
              onChange={(e) => setFormData({ ...formData, name: e.target.value })}
              placeholder="my-subnet"
              pattern="[a-z]([-a-z0-9]*[a-z0-9])?"
              required
            />
          </FormField>

          <FormField
            label="Network"
            required
            error={networks.length === 0 ? 'No networks available. Create a network first.' : undefined}
          >
            <Select
              value={formData.network}
              onChange={(e) => setFormData({ ...formData, network: e.target.value })}
              required
            >
              <option value="">Select a network</option>
              {networks.map((network) => (
                <option key={network.name} value={network.selfLink}>
                  {network.name}
                </option>
              ))}
            </Select>
          </FormField>

          <FormField label="Region" required>
            <Select
              value={formData.region}
              onChange={(e) => setFormData({ ...formData, region: e.target.value })}
              required
            >
              {regions.map((region) => (
                <option key={region} value={region}>
                  {region}
                </option>
              ))}
            </Select>
          </FormField>

          <FormField
            label="IP CIDR Range"
            required
            help="Example: 10.0.0.0/24, 192.168.1.0/24"
            error={cidrError || undefined}
          >
            <Input
              type="text"
              value={formData.ipCidrRange}
              onChange={(e) => {
                setFormData({ ...formData, ipCidrRange: e.target.value });
                setCidrError(null);
                setCidrValid(false);
              }}
              placeholder="10.0.0.0/24"
              className="font-mono"
              required
              onBlur={() => {
                if (formData.ipCidrRange) {
                  const validation = validateCIDR(formData.ipCidrRange);
                  if (!validation.valid) {
                    setCidrError(validation.error || null);
                    setCidrValid(false);
                  } else {
                    setCidrError(null);
                    setCidrValid(true);
                  }
                }
              }}
            />
            {cidrValid && formData.ipCidrRange && (
              <div className="mt-2 flex items-center gap-2 text-xs text-green-600">
                <CheckCircle className="w-4 h-4" />
                Gateway: {getGatewayIP(formData.ipCidrRange)} • {calculateUsableIPs(formData.ipCidrRange).toLocaleString()} usable IPs
              </div>
            )}
          </FormField>

          <div className="flex items-start gap-3 p-4 border-2 border-gray-200 rounded-xl hover:border-gray-300 transition-all">
            <input
              type="checkbox"
              id="privateIpGoogleAccess"
              checked={formData.privateIpGoogleAccess}
              onChange={(e) => setFormData({ ...formData, privateIpGoogleAccess: e.target.checked })}
              className="mt-0.5 text-blue-600 focus:ring-blue-500"
            />
            <label htmlFor="privateIpGoogleAccess" className="cursor-pointer flex-1">
              <div className="text-sm font-semibold text-gray-900">Private Google Access</div>
              <div className="text-xs text-gray-600 mt-0.5">
                Enable VMs without external IPs to reach Google APIs
              </div>
            </label>
          </div>

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
              disabled={networks.length === 0}
            >
              Create
            </ModalButton>
          </ModalFooter>
        </form>
      </Modal>
    </div>
  );
};

export default SubnetsPage;
