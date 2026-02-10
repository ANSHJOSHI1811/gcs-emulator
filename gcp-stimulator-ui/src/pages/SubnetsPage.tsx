import { useEffect, useState } from 'react';
import { useProject } from '../contexts/ProjectContext';
import { Link, useSearchParams } from 'react-router-dom';
import { Network, Plus, Trash2, Globe, ArrowRight, Activity, BarChart3 } from 'lucide-react';
import { Modal } from '../components/Modal';
import { FormField, Input, Select } from '../components/FormFields';
import { listNetworks, listSubnets, createSubnet, deleteSubnet } from '../api/networking';
import { validateCIDR, calculateUsableIPs, isSubnetWithinVPC } from '../utils/cidr';
import { formatDistanceToNow } from 'date-fns';

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
  const [searchParams, setSearchParams] = useSearchParams();
  const networkFilter = searchParams.get('network');
  const [subnets, setSubnets] = useState<Subnet[]>([]);
  const [allSubnets, setAllSubnets] = useState<Subnet[]>([]);
  const [networks, setNetworks] = useState<NetworkOption[]>([]);
  const [selectedNetworkFilter, setSelectedNetworkFilter] = useState<string>(networkFilter || '');
  const [loading, setLoading] = useState(true);
  const [showCreateModal, setShowCreateModal] = useState(false);
  const [showDetailsModal, setShowDetailsModal] = useState(false);
  const [selectedSubnet, setSelectedSubnet] = useState<Subnet | null>(null);
  const [createLoading, setCreateLoading] = useState(false);
  const [actionLoading, setActionLoading] = useState(false);
  const [formData, setFormData] = useState({
    name: '',
    network: '',
    region: 'us-central1',
    ipCidrRange: '',
    privateIpGoogleAccess: false,
  });
  const [error, setError] = useState<string | null>(null);
  const [cidrError, setCidrError] = useState<string | null>(null);

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

      const networksList = await listNetworks(currentProject);
      setNetworks(networksList as any);

      const subnetsList = await listSubnets(currentProject);
      const fetchedSubnets = subnetsList as any;
      setAllSubnets(fetchedSubnets);
      
      // Apply filter
      filterSubnets(fetchedSubnets, selectedNetworkFilter);
    } catch (error: any) {
      console.error('Failed to load subnets:', error);
      setError('Failed to load subnets');
    } finally {
      setLoading(false);
    }
  };

  const filterSubnets = (subnetsToFilter: Subnet[], networkName: string) => {
    if (networkName) {
      const filtered = subnetsToFilter.filter((s: Subnet) => {
        const subnetNetwork = s.network.split('/').pop();
        return subnetNetwork === networkName;
      });
      setSubnets(filtered);
    } else {
      setSubnets(subnetsToFilter);
    }
  };

  const handleNetworkFilterChange = (networkName: string) => {
    setSelectedNetworkFilter(networkName);
    if (networkName) {
      setSearchParams({ network: networkName });
    } else {
      setSearchParams({});
    }
    filterSubnets(allSubnets, networkName);
  };

  const handleCreate = async (e: React.FormEvent) => {
    e.preventDefault();
    setCreateLoading(true);
    setError(null);
    setCidrError(null);

    const validation = validateCIDR(formData.ipCidrRange);
    if (!validation.valid) {
      setCidrError(validation.error || 'Invalid CIDR');
      setCreateLoading(false);
      return;
    }

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
      await loadData();
    } catch (error: any) {
      console.error('Failed to create subnet:', error);
      setError(error.response?.data?.detail || 'Failed to create subnet');
    } finally {
      setCreateLoading(false);
    }
  };

  const handleDelete = async (region: string, subnetName: string) => {
    if (!confirm(`Delete subnet "${subnetName}"?`)) return;

    try {
      setActionLoading(true);
      await deleteSubnet(currentProject, region, subnetName);
      await loadData();
    } catch (error: any) {
      console.error('Failed to delete subnet:', error);
      alert(error.response?.data?.detail || 'Failed to delete subnet');
    } finally {
      setActionLoading(false);
    }
  };

  const handleSubnetClick = (subnet: Subnet) => {
    setSelectedSubnet(subnet);
    setShowDetailsModal(true);
  };

  const extractNetworkName = (url: string) => url?.split('/').pop() || '-';
  const totalIPs = subnets.reduce((sum, s) => sum + calculateUsableIPs(s.ipCidrRange), 0);

  if (loading) {
    return (
      <div className="flex items-center justify-center h-screen bg-[#f8f9fa]">
        <div className="text-center">
          <div className="w-12 h-12 border-4 border-blue-600 border-t-transparent rounded-full animate-spin mx-auto mb-3"></div>
          <p className="text-[13px] text-gray-600">Loading subnets...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-[#f8f9fa]">
      {/* Hero Header */}
      <div className="bg-white border-b border-gray-200">
        <div className="max-w-[1280px] mx-auto px-8 py-6">
          <div className="flex items-center justify-between mb-4">
            <div className="flex-1">
              <div className="flex items-start gap-4 mb-2">
                <div className="p-3 bg-blue-50 rounded-xl">
                  <Globe className="w-8 h-8 text-blue-600" />
                </div>
                <div className="flex-1">
                  <h1 className="text-[28px] font-bold text-gray-900 mb-2">Subnets</h1>
                  <p className="text-[14px] text-gray-600 leading-relaxed">
                    Manage subnets within your VPC networks across different regions.
                  </p>
                </div>
              </div>
            </div>
            <button
              onClick={() => setShowCreateModal(true)}
              className="inline-flex items-center gap-2 px-4 h-10 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-all shadow-sm hover:shadow-md text-[13px] font-medium"
            >
              <Plus className="w-4 h-4" />
              Create Subnet
            </button>
          </div>

          {/* Quick Stats */}
          <div className="flex items-center gap-6 pt-4 border-t border-gray-200">
            <div className="flex items-center gap-2 px-3 py-2">
              <div className="w-2 h-2 bg-blue-500 rounded-full"></div>
              <span className="text-[13px] text-gray-600">
                <span className="font-semibold text-gray-900">{subnets.length}</span> Subnets
              </span>
            </div>
            <div className="flex items-center gap-2 px-3 py-2">
              <div className="w-2 h-2 bg-green-500 rounded-full"></div>
              <span className="text-[13px] text-gray-600">
                <span className="font-semibold text-gray-900">{totalIPs.toLocaleString()}</span> Total IPs
              </span>
            </div>
            <div className="flex items-center gap-2 px-3 py-2">
              <div className="w-2 h-2 bg-purple-500 rounded-full"></div>
              <span className="text-[13px] text-gray-600">
                <span className="font-semibold text-gray-900">{regions.length}</span> Regions
              </span>
            </div>
            <Link 
              to="/services/vpc"
              className="flex items-center gap-2 hover:bg-blue-50 px-3 py-2 rounded-lg transition-colors cursor-pointer group ml-2"
            >
              <div className="w-2 h-2 bg-blue-500 rounded-full group-hover:scale-125 transition-transform"></div>
              <span className="text-[13px] text-gray-600">
                <span className="font-semibold text-gray-900 group-hover:text-blue-600">View VPC Networks</span>
              </span>
              <ArrowRight className="w-3 h-3 text-gray-400 group-hover:text-blue-600" />
            </Link>
          </div>
        </div>
      </div>

      {/* Main Content */}
      <div className="max-w-[1280px] mx-auto px-8 py-8">
        {/* Subnets List */}
        <div className="mb-8">
          <div className="flex items-center justify-between mb-4">
            <h2 className="text-[16px] font-bold text-gray-900">Subnets</h2>
            <select
              value={selectedNetworkFilter}
              onChange={(e) => handleNetworkFilterChange(e.target.value)}
              className="px-3 py-2 text-[13px] border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500 bg-white"
            >
              <option value="">All VPC Networks</option>
              {networks.map((network) => (
                <option key={network.name} value={network.name}>
                  {network.name}
                </option>
              ))}
            </select>
          </div>
          <div className="bg-white rounded-lg border border-gray-200 shadow-[0_1px_3px_rgba(0,0,0,0.07)]">
            {subnets.length > 0 ? (
              <div className="divide-y divide-gray-200">
                {subnets.map((subnet) => (
                  <div
                    key={subnet.id}
                    className="flex items-center justify-between p-4 hover:bg-gray-50 transition-colors group cursor-pointer"
                    onClick={() => handleSubnetClick(subnet)}
                  >
                    <div className="flex items-center gap-3 flex-1">
                      <div className="p-2 bg-blue-50 rounded-lg group-hover:bg-blue-100 transition-colors">
                        <Globe className="w-4 h-4 text-blue-600" />
                      </div>
                      <div className="flex-1">
                        <div className="flex items-center gap-3">
                          <span className="text-[14px] font-medium text-gray-900">
                            {subnet.name}
                          </span>
                          <span className="inline-flex items-center gap-1.5 px-2.5 py-0.5 rounded-full text-[11px] font-medium bg-blue-100 text-blue-700">
                            {subnet.region}
                          </span>
                        </div>
                        <div className="flex items-center gap-4 mt-1">
                          <span className="text-[12px] font-mono text-gray-500">{subnet.ipCidrRange}</span>
                          <span className="text-[12px] text-gray-500">•</span>
                          <span className="text-[12px] text-gray-500">
                            {calculateUsableIPs(subnet.ipCidrRange).toLocaleString()} usable IPs
                          </span>
                          <span className="text-[12px] text-gray-500">•</span>
                          <span className="text-[12px] text-gray-500">
                            Network: {extractNetworkName(subnet.network)}
                          </span>
                        </div>
                      </div>
                    </div>
                    <div className="flex items-center gap-2">
                      <button
                        onClick={(e) => {
                          e.stopPropagation();
                          handleSubnetClick(subnet);
                        }}
                        className="p-2 text-blue-600 hover:bg-blue-50 rounded-lg transition-all"
                        title="View details"
                      >
                        <BarChart3 className="w-4 h-4" />
                      </button>
                      <button
                        onClick={(e) => {
                          e.stopPropagation();
                          handleDelete(subnet.region, subnet.name);
                        }}
                        className="p-2 text-red-600 hover:bg-red-50 rounded-lg transition-all"
                        title="Delete subnet"
                      >
                        <Trash2 className="w-4 h-4" />
                      </button>
                    </div>
                  </div>
                ))}
              </div>
            ) : (
              <div className="p-8 text-center">
                <div className="w-16 h-16 bg-gray-100 rounded-full flex items-center justify-center mx-auto mb-4">
                  <Globe className="w-8 h-8 text-gray-400" />
                </div>
                <p className="text-[13px] text-gray-500 mb-3">No subnets yet</p>
                <button
                  onClick={() => setShowCreateModal(true)}
                  className="inline-flex items-center gap-2 px-4 h-9 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-all text-[13px] font-medium"
                >
                  <Plus className="w-4 h-4" />
                  Create Your First Subnet
                </button>
              </div>
            )}
          </div>
        </div>

        {/* Recent Activity */}
        {subnets.length > 0 && (
          <div className="mt-8">
            <h2 className="text-[16px] font-bold text-gray-900 mb-4">Recent Activity</h2>
            <div className="bg-white rounded-lg border border-gray-200 shadow-[0_1px_3px_rgba(0,0,0,0.07)]">
              <div className="divide-y divide-gray-200">
                {subnets.slice(0, 5).map((subnet) => (
                  <div key={subnet.id} className="flex items-center justify-between p-4 hover:bg-gray-50 transition-colors">
                    <div className="flex items-center gap-3">
                      <div className="p-2 bg-gray-50 rounded-lg">
                        <Activity className="w-4 h-4 text-gray-600" />
                      </div>
                      <div>
                        <p className="text-[13px] font-medium text-gray-900">
                          Subnet created: <span className="text-blue-600">{subnet.name}</span>
                        </p>
                        <p className="text-[12px] text-gray-500">
                          {subnet.region} • {subnet.ipCidrRange} • {extractNetworkName(subnet.network)}
                        </p>
                      </div>
                    </div>
                    <button
                      onClick={() => handleSubnetClick(subnet)}
                      className="text-[12px] text-blue-600 hover:text-blue-800 font-medium flex items-center gap-1"
                    >
                      View details
                      <ArrowRight className="w-3 h-3" />
                    </button>
                  </div>
                ))}
              </div>
            </div>
          </div>
        )}
      </div>

      {/* Create Subnet Modal */}
      <Modal
        isOpen={showCreateModal}
        onClose={() => { setShowCreateModal(false); setCidrError(null); }}
        title="Create Subnet"
      >
        <form onSubmit={handleCreate} className="space-y-5">
          <FormField label="Subnet Name" required>
            <Input
              value={formData.name}
              onChange={(e) => setFormData({ ...formData, name: e.target.value })}
              placeholder="my-subnet"
              required
            />
          </FormField>

          <FormField label="Network" required>
            <Select
              value={formData.network}
              onChange={(e) => setFormData({ ...formData, network: e.target.value })}
              required
            >
              <option value="">Select a network</option>
              {networks.map((network) => (
                <option key={network.selfLink} value={network.selfLink}>
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

          <FormField label="IP CIDR Range" required>
            <Input
              value={formData.ipCidrRange}
              onChange={(e) => setFormData({ ...formData, ipCidrRange: e.target.value })}
              placeholder="10.128.0.0/20"
              required
            />
            {cidrError && (
              <p className="text-[12px] text-red-600 mt-1">{cidrError}</p>
            )}
            {formData.ipCidrRange && !cidrError && (
              <p className="text-[12px] text-green-600 mt-1">
                {calculateUsableIPs(formData.ipCidrRange).toLocaleString()} usable IP addresses
              </p>
            )}
          </FormField>

          <div className="flex justify-end gap-3 pt-4">
            <button
              type="button"
              onClick={() => { setShowCreateModal(false); setCidrError(null); }}
              className="px-4 py-2 text-[13px] font-medium text-gray-700 bg-white border-2 border-gray-300 rounded-lg hover:bg-gray-50 hover:border-gray-400 transition-all"
            >
              Cancel
            </button>
            <button
              type="submit"
              disabled={createLoading}
              className="inline-flex items-center gap-2 px-4 py-2 text-[13px] font-medium text-white bg-blue-600 rounded-lg hover:bg-blue-700 transition-all disabled:opacity-50"
            >
              {createLoading ? (
                <>
                  <div className="w-4 h-4 border-2 border-white border-t-transparent rounded-full animate-spin"></div>
                  Creating...
                </>
              ) : (
                <>
                  <Plus className="w-4 h-4" />
                  Create Subnet
                </>
              )}
            </button>
          </div>
        </form>
      </Modal>

      {/* Subnet Details Modal */}
      {selectedSubnet && (
        <Modal
          isOpen={showDetailsModal}
          onClose={() => setShowDetailsModal(false)}
          title="Subnet Details"
          size="lg"
        >
          <div className="space-y-6">
            <div>
              <h3 className="text-[15px] font-semibold text-gray-900 mb-3">{selectedSubnet.name}</h3>
              <span className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-[12px] font-medium bg-blue-100 text-blue-700">
                {selectedSubnet.region}
              </span>
            </div>

            <div className="bg-gray-50 rounded-xl p-4 space-y-3">
              <div className="flex justify-between items-center py-2">
                <span className="text-[13px] text-gray-600">Subnet ID</span>
                <span className="text-[12px] font-mono text-gray-900">{selectedSubnet.id}</span>
              </div>
              <div className="h-px bg-gray-200"></div>
              <div className="flex justify-between items-center py-2">
                <span className="text-[13px] text-gray-600">IP CIDR Range</span>
                <span className="text-[12px] font-mono text-gray-900">{selectedSubnet.ipCidrRange}</span>
              </div>
              <div className="h-px bg-gray-200"></div>
              <div className="flex justify-between items-center py-2">
                <span className="text-[13px] text-gray-600">Usable IPs</span>
                <span className="text-[13px] font-semibold text-gray-900">
                  {calculateUsableIPs(selectedSubnet.ipCidrRange).toLocaleString()}
                </span>
              </div>
              <div className="h-px bg-gray-200"></div>
              <div className="flex justify-between items-center py-2">
                <span className="text-[13px] text-gray-600">Gateway Address</span>
                <span className="text-[12px] font-mono text-gray-900">{selectedSubnet.gatewayAddress || '-'}</span>
              </div>
              <div className="h-px bg-gray-200"></div>
              <div className="flex justify-between items-center py-2">
                <span className="text-[13px] text-gray-600">Network</span>
                <span className="text-[13px] font-medium text-gray-900">{extractNetworkName(selectedSubnet.network)}</span>
              </div>
              <div className="h-px bg-gray-200"></div>
              <div className="flex justify-between items-center py-2">
                <span className="text-[13px] text-gray-600">Region</span>
                <span className="text-[13px] font-medium text-gray-900">{selectedSubnet.region}</span>
              </div>
              {selectedSubnet.creationTimestamp && (
                <>
                  <div className="h-px bg-gray-200"></div>
                  <div className="flex justify-between items-center py-2">
                    <span className="text-[13px] text-gray-600">Created</span>
                    <span className="text-[13px] text-gray-900">
                      {formatDistanceToNow(new Date(selectedSubnet.creationTimestamp), { addSuffix: true })}
                    </span>
                  </div>
                </>
              )}
            </div>

            {/* IP Usage Visualization */}
            <div className="bg-gradient-to-br from-blue-50 to-purple-50 rounded-xl p-6">
              <div className="flex items-center gap-2 mb-4">
                <BarChart3 className="w-5 h-5 text-blue-600" />
                <h4 className="text-[14px] font-semibold text-gray-900">IP Address Usage</h4>
              </div>

              <div className="bg-white/80 backdrop-blur-sm rounded-lg p-4">
                <div className="flex items-center justify-between mb-3">
                  <span className="text-[13px] font-medium text-gray-900">Address Space</span>
                  <span className="text-[12px] font-mono text-gray-700">
                    {Math.floor(Math.random() * 50)} / {calculateUsableIPs(selectedSubnet.ipCidrRange).toLocaleString()} IPs
                  </span>
                </div>
                <div className="w-full bg-gray-200 rounded-full h-3 overflow-hidden">
                  <div 
                    className="h-full rounded-full bg-gradient-to-r from-blue-500 to-purple-500 transition-all duration-500"
                    style={{ width: `${Math.random() * 30}%` }}
                  />
                </div>
                <div className="flex items-center justify-between mt-2">
                  <span className="text-[11px] font-mono text-gray-500">{selectedSubnet.ipCidrRange}</span>
                  <span className="text-[11px] font-semibold text-blue-600">
                    {(Math.random() * 30).toFixed(1)}% used
                  </span>
                </div>
              </div>
            </div>

            <div className="flex items-center gap-3 pt-4">
              <Link
                to={`/services/vpc?network=${extractNetworkName(selectedSubnet.network)}`}
                className="flex-1 inline-flex items-center justify-center gap-2 px-4 py-2.5 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-all text-[13px] font-medium"
              >
                <Network className="w-4 h-4" />
                View Network
              </Link>
              <button
                onClick={() => {
                  setShowDetailsModal(false);
                  handleDelete(selectedSubnet.region, selectedSubnet.name);
                }}
                disabled={actionLoading}
                className="inline-flex items-center justify-center gap-2 px-4 py-2.5 bg-white border-2 border-red-300 text-red-700 rounded-lg hover:bg-red-50 hover:border-red-400 transition-all text-[13px] font-medium disabled:opacity-50"
              >
                <Trash2 className="w-4 h-4" />
                Delete
              </button>
            </div>
          </div>
        </Modal>
      )}
    </div>
  );
};

export default SubnetsPage;
