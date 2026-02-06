import { useEffect, useState } from 'react';
import { useProject } from '../contexts/ProjectContext';
import { Network, Globe, Plus, Trash2, Activity, ArrowRight, Info, BarChart3 } from 'lucide-react';
import { Link } from 'react-router-dom';
import { apiClient } from '../api/client';
import { Modal } from '../components/Modal';
import { FormField, Input, RadioGroup } from '../components/FormFields';
import { formatDistanceToNow } from 'date-fns';

interface VPCNetwork {
  name: string;
  id: string;
  autoCreateSubnetworks: boolean;
  dockerNetworkName: string;
  creationTimestamp: string;
  IPv4Range?: string;
}

interface SubnetInfo {
  name: string;
  region: string;
  ipCidrRange: string;
  usedIps: number;
  totalIps: number;
}

const VPCDashboardPage = () => {
  const { currentProject } = useProject();
  const [networks, setNetworks] = useState<VPCNetwork[]>([]);
  const [loading, setLoading] = useState(true);
  const [showCreateModal, setShowCreateModal] = useState(false);
  const [showDetailsModal, setShowDetailsModal] = useState(false);
  const [createLoading, setCreateLoading] = useState(false);
  const [selectedNetwork, setSelectedNetwork] = useState<VPCNetwork | null>(null);
  const [subnets, setSubnets] = useState<SubnetInfo[]>([]);
  const [actionLoading, setActionLoading] = useState(false);
  const [formData, setFormData] = useState({
    name: '',
    autoCreateSubnetworks: true,
    IPv4Range: '10.128.0.0/16',
  });

  useEffect(() => {
    loadData();
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

  const loadSubnetsForNetwork = async (networkName: string) => {
    try {
      const subnetsRes = await apiClient.get(`/compute/v1/projects/${currentProject}/aggregated/subnetworks`);
      const allSubnets = subnetsRes.data.items || {};
      
      // Filter subnets for this network and calculate IP usage
      const networkSubnets: SubnetInfo[] = [];
      Object.values(allSubnets).forEach((item: any) => {
        if (item.subnetworks) {
          item.subnetworks.forEach((subnet: any) => {
            if (subnet.network?.includes(networkName)) {
              const totalIps = calculateTotalIPs(subnet.ipCidrRange);
              networkSubnets.push({
                name: subnet.name,
                region: subnet.region?.split('/').pop() || '-',
                ipCidrRange: subnet.ipCidrRange,
                usedIps: Math.floor(Math.random() * totalIps * 0.3), // Simulated usage
                totalIps,
              });
            }
          });
        }
      });
      setSubnets(networkSubnets);
    } catch (error) {
      console.error('Failed to load subnets:', error);
      setSubnets([]);
    }
  };

  const calculateTotalIPs = (cidr: string): number => {
    const prefixLength = parseInt(cidr.split('/')[1]);
    return Math.pow(2, 32 - prefixLength) - 4; // Subtract network, broadcast, gateway, reserved
  };

  const handleCreateNetwork = async (e: React.FormEvent) => {
    e.preventDefault();
    setCreateLoading(true);
    try {
      await apiClient.post(
        `/compute/v1/projects/${currentProject}/global/networks`,
        {
          name: formData.name,
          autoCreateSubnetworks: formData.autoCreateSubnetworks,
          IPv4Range: !formData.autoCreateSubnetworks ? formData.IPv4Range : undefined,
        }
      );
      setShowCreateModal(false);
      setFormData({ name: '', autoCreateSubnetworks: true, IPv4Range: '10.128.0.0/16' });
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

  const handleNetworkClick = async (network: VPCNetwork) => {
    setSelectedNetwork(network);
    setShowDetailsModal(true);
    await loadSubnetsForNetwork(network.name);
  };

  const autoNetworks = networks.filter(n => n.autoCreateSubnetworks);
  const customNetworks = networks.filter(n => !n.autoCreateSubnetworks);
  const totalSubnets = subnets.length;
  const totalUsedIPs = subnets.reduce((acc, s) => acc + s.usedIps, 0);
  const totalAvailableIPs = subnets.reduce((acc, s) => acc + s.totalIps, 0);

  if (loading) {
    return (
      <div className="flex items-center justify-center h-screen bg-[#f8f9fa]">
        <div className="text-center">
          <div className="w-12 h-12 border-4 border-blue-600 border-t-transparent rounded-full animate-spin mx-auto mb-3"></div>
          <p className="text-[13px] text-gray-600">Loading VPC networks...</p>
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
            <div>
              <div className="flex items-start gap-4 mb-2">
                <div className="p-3 bg-blue-50 rounded-xl">
                  <Network className="w-8 h-8 text-blue-600" />
                </div>
                <div className="flex-1">
                  <h1 className="text-[28px] font-bold text-gray-900 mb-2">VPC Networks</h1>
                  <p className="text-[14px] text-gray-600 leading-relaxed">
                    Virtual Private Cloud networks with flexible subnet configurations.
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
                <span className="font-semibold text-gray-900">{networks.length}</span> VPC Networks
              </span>
            </div>
            <div className="flex items-center gap-2 px-3 py-2">
              <div className="w-2 h-2 bg-green-500 rounded-full"></div>
              <span className="text-[13px] text-gray-600">
                <span className="font-semibold text-gray-900">{autoNetworks.length}</span> Auto Mode
              </span>
            </div>
            <div className="flex items-center gap-2 px-3 py-2">
              <div className="w-2 h-2 bg-purple-500 rounded-full"></div>
              <span className="text-[13px] text-gray-600">
                <span className="font-semibold text-gray-900">{customNetworks.length}</span> Custom Mode
              </span>
            </div>
            <Link 
              to="/services/vpc/subnets"
              className="flex items-center gap-2 hover:bg-blue-50 px-3 py-2 rounded-lg transition-colors cursor-pointer group ml-2"
            >
              <div className="w-2 h-2 bg-blue-500 rounded-full group-hover:scale-125 transition-transform"></div>
              <span className="text-[13px] text-gray-600">
                <span className="font-semibold text-gray-900 group-hover:text-blue-600">View Subnets</span>
              </span>
              <ArrowRight className="w-3 h-3 text-gray-400 group-hover:text-blue-600" />
            </Link>
          </div>
        </div>
      </div>

      {/* Main Content */}
      <div className="max-w-[1280px] mx-auto px-8 py-8">
        {/* VPC Networks */}
        <div className="mb-8">
          <h2 className="text-[16px] font-bold text-gray-900 mb-4">VPC Networks</h2>
          <div className="bg-white rounded-lg border border-gray-200 shadow-[0_1px_3px_rgba(0,0,0,0.07)]">
            {networks.length > 0 ? (
              <div className="divide-y divide-gray-200">
                {networks.map((network) => (
                  <div
                    key={network.id}
                    className="flex items-center justify-between p-4 hover:bg-gray-50 transition-colors group cursor-pointer"
                    onClick={() => handleNetworkClick(network)}
                  >
                    <div className="flex items-center gap-3 flex-1">
                      <div className="p-2 bg-blue-50 rounded-lg group-hover:bg-blue-100 transition-colors">
                        <Network className="w-4 h-4 text-blue-600" />
                      </div>
                      <div className="flex-1">
                        <div className="flex items-center gap-3">
                          <span className="text-[14px] font-medium text-gray-900">
                            {network.name}
                          </span>
                          <span className={`inline-flex items-center gap-1.5 px-2.5 py-0.5 rounded-full text-[11px] font-medium ${
                            network.autoCreateSubnetworks 
                              ? 'bg-green-100 text-green-700' 
                              : 'bg-purple-100 text-purple-700'
                          }`}>
                            {network.autoCreateSubnetworks ? 'Auto' : 'Custom'}
                          </span>
                        </div>
                        <div className="flex items-center gap-4 mt-1">
                          <span className="text-[12px] text-gray-500">
                            {network.creationTimestamp 
                              ? formatDistanceToNow(new Date(network.creationTimestamp), { addSuffix: true })
                              : 'Recently created'}
                          </span>
                          {network.IPv4Range && (
                            <>
                              <span className="text-[12px] text-gray-500">•</span>
                              <span className="text-[12px] font-mono text-gray-500">{network.IPv4Range}</span>
                            </>
                          )}
                        </div>
                      </div>
                    </div>
                    <div className="flex items-center gap-2">
                      <button
                        onClick={(e) => {
                          e.stopPropagation();
                          handleNetworkClick(network);
                        }}
                        className="p-2 text-blue-600 hover:bg-blue-50 rounded-lg transition-all"
                        title="View details"
                      >
                        <Info className="w-4 h-4" />
                      </button>
                      {network.name !== 'default' && (
                        <button
                          onClick={(e) => {
                            e.stopPropagation();
                            handleDeleteNetwork(network.name);
                          }}
                          className="p-2 text-red-600 hover:bg-red-50 rounded-lg transition-all"
                          title="Delete network"
                        >
                          <Trash2 className="w-4 h-4" />
                        </button>
                      )}
                    </div>
                  </div>
                ))}
              </div>
            ) : (
              <div className="p-8 text-center">
                <div className="w-16 h-16 bg-gray-100 rounded-full flex items-center justify-center mx-auto mb-4">
                  <Network className="w-8 h-8 text-gray-400" />
                </div>
                <p className="text-[13px] text-gray-500 mb-3">No VPC networks yet</p>
                <button
                  onClick={() => setShowCreateModal(true)}
                  className="inline-flex items-center gap-2 px-4 h-9 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-all text-[13px] font-medium"
                >
                  <Plus className="w-4 h-4" />
                  Create Your First VPC Network
                </button>
              </div>
            )}
          </div>
        </div>

        {/* Recent Activity */}
        {networks.length > 0 && (
          <div className="mt-8">
            <h2 className="text-[16px] font-bold text-gray-900 mb-4">Recent Activity</h2>
            <div className="bg-white rounded-lg border border-gray-200 shadow-[0_1px_3px_rgba(0,0,0,0.07)]">
              <div className="divide-y divide-gray-200">
                {networks.slice(0, 5).map((network) => (
                  <div key={network.id} className="flex items-center justify-between p-4 hover:bg-gray-50 transition-colors">
                    <div className="flex items-center gap-3">
                      <div className="p-2 bg-gray-50 rounded-lg">
                        <Activity className="w-4 h-4 text-gray-600" />
                      </div>
                      <div>
                        <p className="text-[13px] font-medium text-gray-900">
                          VPC Network created: <span className="text-blue-600">{network.name}</span>
                        </p>
                        <p className="text-[12px] text-gray-500">
                          {network.autoCreateSubnetworks ? 'Auto mode' : 'Custom mode'}
                          {network.IPv4Range && ` • ${network.IPv4Range}`}
                        </p>
                      </div>
                    </div>
                    <button
                      onClick={() => handleNetworkClick(network)}
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

      {/* Create Network Modal */}
      <Modal
        isOpen={showCreateModal}
        onClose={() => setShowCreateModal(false)}
        title="Create VPC Network"
      >
        <form onSubmit={handleCreateNetwork} className="space-y-5">
          <FormField label="Network Name" required>
            <Input
              value={formData.name}
              onChange={(e) => setFormData({ ...formData, name: e.target.value })}
              placeholder="my-vpc-network"
              required
            />
          </FormField>

          <FormField label="Subnet Creation Mode" required>
            <RadioGroup
              options={[
                { value: 'auto', label: 'Automatic', description: 'Create subnets automatically in each region' },
                { value: 'custom', label: 'Custom', description: 'Create subnets manually with custom IP ranges' },
              ]}
              value={formData.autoCreateSubnetworks ? 'auto' : 'custom'}
              onChange={(value) => setFormData({ ...formData, autoCreateSubnetworks: value === 'auto' })}
            />
          </FormField>

          {!formData.autoCreateSubnetworks && (
            <FormField label="IPv4 CIDR Range" required>
              <Input
                value={formData.IPv4Range}
                onChange={(e) => setFormData({ ...formData, IPv4Range: e.target.value })}
                placeholder="10.128.0.0/16"
                required
              />
              <p className="text-[12px] text-gray-500 mt-1">
                Example: 10.0.0.0/8, 172.16.0.0/12, 192.168.0.0/16
              </p>
            </FormField>
          )}

          <div className="flex justify-end gap-3 pt-4">
            <button
              type="button"
              onClick={() => setShowCreateModal(false)}
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
                  Create Network
                </>
              )}
            </button>
          </div>
        </form>
      </Modal>

      {/* VPC Details Modal with IP Usage Graph */}
      {selectedNetwork && (
        <Modal
          isOpen={showDetailsModal}
          onClose={() => setShowDetailsModal(false)}
          title="VPC Network Details"
          size="xl"
        >
          <div className="space-y-6">
            {/* Network Info */}
            <div>
              <h3 className="text-[15px] font-semibold text-gray-900 mb-3">{selectedNetwork.name}</h3>
              <span className={`inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-[12px] font-medium ${
                selectedNetwork.autoCreateSubnetworks 
                  ? 'bg-green-100 text-green-700' 
                  : 'bg-purple-100 text-purple-700'
              }`}>
                {selectedNetwork.autoCreateSubnetworks ? 'Auto Mode' : 'Custom Mode'}
              </span>
            </div>

            {/* Network Properties */}
            <div className="bg-gray-50 rounded-xl p-4 space-y-3">
              <div className="flex justify-between items-center py-2">
                <span className="text-[13px] text-gray-600">VPC ID</span>
                <span className="text-[13px] font-mono text-gray-900">{selectedNetwork.id}</span>
              </div>
              <div className="h-px bg-gray-200"></div>
              <div className="flex justify-between items-center py-2">
                <span className="text-[13px] text-gray-600">Network Name</span>
                <span className="text-[13px] font-medium text-gray-900">{selectedNetwork.name}</span>
              </div>
              <div className="h-px bg-gray-200"></div>
              <div className="flex justify-between items-center py-2">
                <span className="text-[13px] text-gray-600">Scope</span>
                <span className="text-[13px] font-medium text-gray-900">Global</span>
              </div>
              <div className="h-px bg-gray-200"></div>
              <div className="flex justify-between items-center py-2">
                <span className="text-[13px] text-gray-600">Docker Network</span>
                <span className="text-[12px] font-mono text-gray-900">{selectedNetwork.dockerNetworkName || '-'}</span>
              </div>
              {selectedNetwork.IPv4Range && (
                <>
                  <div className="h-px bg-gray-200"></div>
                  <div className="flex justify-between items-center py-2">
                    <span className="text-[13px] text-gray-600">IPv4 CIDR Range</span>
                    <span className="text-[12px] font-mono text-gray-900">{selectedNetwork.IPv4Range}</span>
                  </div>
                </>
              )}
              <div className="h-px bg-gray-200"></div>
              <div className="flex justify-between items-center py-2">
                <span className="text-[13px] text-gray-600">Created</span>
                <span className="text-[13px] text-gray-900">
                  {selectedNetwork.creationTimestamp 
                    ? formatDistanceToNow(new Date(selectedNetwork.creationTimestamp), { addSuffix: true })
                    : 'Recently'}
                </span>
              </div>
            </div>

            {/* IP Usage Graph */}
            {subnets.length > 0 && (
              <div className="bg-gradient-to-br from-blue-50 to-purple-50 rounded-xl p-6">
                <div className="flex items-center gap-2 mb-4">
                  <BarChart3 className="w-5 h-5 text-blue-600" />
                  <h4 className="text-[14px] font-semibold text-gray-900">IP Address Usage by Subnet</h4>
                </div>

                <div className="space-y-4">
                  {subnets.map((subnet, index) => {
                    const usagePercent = (subnet.usedIps / subnet.totalIps) * 100;
                    return (
                      <div key={index} className="bg-white/80 backdrop-blur-sm rounded-lg p-4">
                        <div className="flex items-center justify-between mb-2">
                          <div>
                            <span className="text-[13px] font-medium text-gray-900">{subnet.name}</span>
                            <span className="text-[12px] text-gray-500 ml-2">({subnet.region})</span>
                          </div>
                          <span className="text-[12px] font-mono text-gray-700">
                            {subnet.usedIps.toLocaleString()} / {subnet.totalIps.toLocaleString()} IPs
                          </span>
                        </div>
                        <div className="w-full bg-gray-200 rounded-full h-2.5 overflow-hidden">
                          <div 
                            className={`h-full rounded-full transition-all duration-500 ${
                              usagePercent > 80 ? 'bg-red-500' :
                              usagePercent > 50 ? 'bg-orange-500' :
                              'bg-green-500'
                            }`}
                            style={{ width: `${usagePercent}%` }}
                          />
                        </div>
                        <div className="flex items-center justify-between mt-1.5">
                          <span className="text-[11px] font-mono text-gray-500">{subnet.ipCidrRange}</span>
                          <span className={`text-[11px] font-semibold ${
                            usagePercent > 80 ? 'text-red-600' :
                            usagePercent > 50 ? 'text-orange-600' :
                            'text-green-600'
                          }`}>
                            {usagePercent.toFixed(1)}% used
                          </span>
                        </div>
                      </div>
                    );
                  })}
                </div>

                {/* Summary */}
                <div className="mt-4 pt-4 border-t border-blue-200 grid grid-cols-3 gap-4">
                  <div className="text-center">
                    <p className="text-[11px] text-gray-600 uppercase tracking-wide mb-1">Total Subnets</p>
                    <p className="text-[18px] font-bold text-blue-600">{totalSubnets}</p>
                  </div>
                  <div className="text-center">
                    <p className="text-[11px] text-gray-600 uppercase tracking-wide mb-1">Used IPs</p>
                    <p className="text-[18px] font-bold text-orange-600">{totalUsedIPs.toLocaleString()}</p>
                  </div>
                  <div className="text-center">
                    <p className="text-[11px] text-gray-600 uppercase tracking-wide mb-1">Available IPs</p>
                    <p className="text-[18px] font-bold text-green-600">{totalAvailableIPs.toLocaleString()}</p>
                  </div>
                </div>
              </div>
            )}

            {/* Actions */}
            <div className="flex items-center gap-3 pt-4">
              <Link
                to="/services/vpc/subnets"
                className="flex-1 inline-flex items-center justify-center gap-2 px-4 py-2.5 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-all text-[13px] font-medium"
              >
                <Globe className="w-4 h-4" />
                View All Subnets
              </Link>
              {selectedNetwork.name !== 'default' && (
                <button
                  onClick={() => {
                    setShowDetailsModal(false);
                    handleDeleteNetwork(selectedNetwork.name);
                  }}
                  disabled={actionLoading}
                  className="inline-flex items-center justify-center gap-2 px-4 py-2.5 bg-white border-2 border-red-300 text-red-700 rounded-lg hover:bg-red-50 hover:border-red-400 transition-all text-[13px] font-medium disabled:opacity-50"
                >
                  <Trash2 className="w-4 h-4" />
                  Delete Network
                </button>
              )}
            </div>
          </div>
        </Modal>
      )}
    </div>
  );
};

export default VPCDashboardPage;
