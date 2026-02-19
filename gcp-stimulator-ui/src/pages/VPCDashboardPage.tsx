import { useEffect, useState } from 'react';
import { useProject } from '../contexts/ProjectContext';
import { Network, Globe, Plus, Trash2, Activity, ArrowRight, Info, BarChart3, Route, Router, Share2, X } from 'lucide-react';
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

interface CloudRouter {
  id: number;
  name: string;
  region: string;
  network: string;
  bgp_asn?: number;
  description?: string;
  created_at?: string;
}

interface CloudNAT {
  id: number;
  name: string;
  router_name: string;
  region: string;
  nat_ip_allocate_option?: string;
  source_subnetwork_option?: string;
}

interface VPCPeering {
  id: number;
  name: string;
  network: string;
  peer_network: string;
  state: string;
  exchange_subnet_routes?: boolean;
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

  // Sprint 2 state
  const [activeTab, setActiveTab] = useState<'networks' | 'routers' | 'nat' | 'peering'>('networks');
  const [routers, setRouters] = useState<CloudRouter[]>([]);
  const [nats, setNats] = useState<CloudNAT[]>([]);
  const [peerings, setPeerings] = useState<VPCPeering[]>([]);

  // Router form
  const [showCreateRouter, setShowCreateRouter] = useState(false);
  const [routerForm, setRouterForm] = useState({ name: '', region: 'us-central1', network: 'default', bgp_asn: 64512 });
  const [creatingRouter, setCreatingRouter] = useState(false);

  // NAT form
  const [showCreateNAT, setShowCreateNAT] = useState(false);
  const [natForm, setNatForm] = useState({ name: '', router_name: '', region: 'us-central1' });
  const [creatingNAT, setCreatingNAT] = useState(false);

  // Peering form
  const [showCreatePeering, setShowCreatePeering] = useState(false);
  const [peeringForm, setPeeringForm] = useState({ name: '', network: 'default', peer_network: '' });
  const [creatingPeering, setCreatingPeering] = useState(false);

  useEffect(() => {
    loadData();
    loadRouters();
    loadPeerings();
    const interval = setInterval(() => {
      loadData();
    }, 5000);
    return () => clearInterval(interval);
  }, [currentProject]);

  const loadRouters = async () => {
    try {
      const res = await apiClient.get(`/compute/v1/projects/${currentProject}/regions/us-central1/routers`);
      setRouters(res.data.items || []);
    } catch { /* silent */ }
  };

  const loadNATsForRouter = async (routerName: string, region: string) => {
    try {
      const res = await apiClient.get(`/compute/v1/projects/${currentProject}/regions/${region}/routers/${routerName}/nats`);
      setNats(res.data.items || []);
    } catch { /* silent */ }
  };

  const loadPeerings = async () => {
    try {
      const res = await apiClient.get(`/compute/v1/projects/${currentProject}/global/networks/default/peerings`);
      setPeerings(res.data.items || []);
    } catch { /* silent */ }
  };

  const handleCreateRouter = async () => {
    if (!routerForm.name.trim()) return;
    try {
      setCreatingRouter(true);
      await apiClient.post(`/compute/v1/projects/${currentProject}/regions/${routerForm.region}/routers`, routerForm);
      setShowCreateRouter(false);
      setRouterForm({ name: '', region: 'us-central1', network: 'default', bgp_asn: 64512 });
      loadRouters();
    } catch (err: any) {
      alert(err.response?.data?.detail || 'Failed to create router');
    } finally {
      setCreatingRouter(false);
    }
  };

  const handleDeleteRouter = async (router: CloudRouter) => {
    if (!confirm(`Delete Cloud Router "${router.name}"?`)) return;
    try {
      await apiClient.delete(`/compute/v1/projects/${currentProject}/regions/${router.region}/routers/${router.name}`);
      loadRouters();
    } catch (err: any) {
      alert(err.response?.data?.detail || 'Failed to delete router');
    }
  };

  const handleCreateNAT = async () => {
    if (!natForm.name.trim() || !natForm.router_name.trim()) return;
    try {
      setCreatingNAT(true);
      await apiClient.post(
        `/compute/v1/projects/${currentProject}/regions/${natForm.region}/routers/${natForm.router_name}/nats`,
        { name: natForm.name, region: natForm.region, router_name: natForm.router_name, nat_ip_allocate_option: 'AUTO_ONLY', source_subnetwork_option: 'ALL_SUBNETWORKS_ALL_IP_RANGES' }
      );
      setShowCreateNAT(false);
      setNatForm({ name: '', router_name: '', region: 'us-central1' });
      loadNATsForRouter(natForm.router_name, natForm.region);
    } catch (err: any) {
      alert(err.response?.data?.detail || 'Failed to create NAT');
    } finally {
      setCreatingNAT(false);
    }
  };

  const handleDeleteNAT = async (nat: CloudNAT) => {
    if (!confirm(`Delete Cloud NAT "${nat.name}"?`)) return;
    try {
      await apiClient.delete(`/compute/v1/projects/${currentProject}/regions/${nat.region}/routers/${nat.router_name}/nats/${nat.name}`);
      loadNATsForRouter(nat.router_name, nat.region);
    } catch (err: any) {
      alert(err.response?.data?.detail || 'Failed to delete NAT');
    }
  };

  const handleAddPeering = async () => {
    if (!peeringForm.name.trim() || !peeringForm.peer_network.trim()) return;
    try {
      setCreatingPeering(true);
      await apiClient.post(
        `/compute/v1/projects/${currentProject}/global/networks/${peeringForm.network}/addPeering`,
        { name: peeringForm.name, network: peeringForm.network, peer_network: peeringForm.peer_network, exchange_subnet_routes: true }
      );
      setShowCreatePeering(false);
      setPeeringForm({ name: '', network: 'default', peer_network: '' });
      loadPeerings();
    } catch (err: any) {
      alert(err.response?.data?.detail || 'Failed to add peering');
    } finally {
      setCreatingPeering(false);
    }
  };

  const handleRemovePeering = async (peering: VPCPeering) => {
    if (!confirm(`Remove VPC peering "${peering.name}"?`)) return;
    try {
      await apiClient.post(
        `/compute/v1/projects/${currentProject}/global/networks/${peering.network}/removePeering`,
        { name: peering.name }
      );
      loadPeerings();
    } catch (err: any) {
      alert(err.response?.data?.detail || 'Failed to remove peering');
    }
  };

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

          {/* Tab Navigation */}
          <div className="flex gap-1 pt-4 border-t border-gray-200">
            {([
              { key: 'networks', label: 'Networks', icon: Network },
              { key: 'routers', label: 'Cloud Routers', icon: Router },
              { key: 'nat', label: 'Cloud NAT', icon: Globe },
              { key: 'peering', label: 'VPC Peering', icon: Share2 },
            ] as const).map(({ key, label, icon: Icon }) => (
              <button key={key} onClick={() => setActiveTab(key)}
                className={`flex items-center gap-2 px-4 py-2 rounded-lg text-[13px] font-medium transition-colors ${
                  activeTab === key ? 'bg-blue-50 text-blue-700' : 'text-gray-600 hover:bg-gray-100'
                }`}>
                <Icon className="w-4 h-4" /> {label}
              </button>
            ))}
          </div>
        </div>
      </div>

      {/* Main Content */}
      <div className="max-w-[1280px] mx-auto px-8 py-8">
        {/* Networks Tab */}
        {activeTab === 'networks' && (
        <>
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
                    <div className="flex items-center gap-4">
                      <Link
                        to={`/services/vpc/subnets?network=${network.name}`}
                        onClick={(e) => e.stopPropagation()}
                        className="flex items-center gap-1.5 text-[13px] text-blue-600 hover:text-blue-800 font-medium group/link"
                      >
                        <span>Subnets</span>
                        <ArrowRight className="w-3.5 h-3.5 group-hover/link:translate-x-0.5 transition-transform" />
                      </Link>
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

        {/* Networking Resources Quick Links */}
        {networks.length > 0 && (
          <div className="mt-8">
            <h2 className="text-[16px] font-bold text-gray-900 mb-4">Networking Resources</h2>
            <div className="grid grid-cols-2 gap-4">
              {/* Routes Card */}
              <Link
                to="/services/vpc/routes"
                className="group"
              >
                <div className="bg-white rounded-lg border border-gray-200 shadow-[0_1px_3px_rgba(0,0,0,0.07)] hover:shadow-[0_8px_16px_rgba(0,0,0,0.1)] transition-all p-5 h-full hover:border-blue-300 cursor-pointer">
                  <div className="flex items-center justify-between mb-4">
                    <div className="p-2.5 bg-blue-50 rounded-lg group-hover:bg-blue-100 transition-colors">
                      <Route className="w-5 h-5 text-blue-600" />
                    </div>
                    <ArrowRight className="w-4 h-4 text-gray-400 group-hover:text-blue-600 group-hover:translate-x-0.5 transition-all" />
                  </div>
                  <h3 className="text-[14px] font-semibold text-gray-900 mb-1">Routes</h3>
                  <p className="text-[12px] text-gray-500">Manage traffic routing configuration</p>
                </div>
              </Link>

              {/* Firewall Rules Card */}
              <Link
                to="/services/vpc/firewalls"
                className="group"
              >
                <div className="bg-white rounded-lg border border-gray-200 shadow-[0_1px_3px_rgba(0,0,0,0.07)] hover:shadow-[0_8px_16px_rgba(0,0,0,0.1)] transition-all p-5 h-full hover:border-red-300 cursor-pointer">
                  <div className="flex items-center justify-between mb-4">
                    <div className="p-2.5 bg-red-50 rounded-lg group-hover:bg-red-100 transition-colors">
                      <Info className="w-5 h-5 text-red-600" />
                    </div>
                    <ArrowRight className="w-4 h-4 text-gray-400 group-hover:text-red-600 group-hover:translate-x-0.5 transition-all" />
                  </div>
                  <h3 className="text-[14px] font-semibold text-gray-900 mb-1">Firewall Rules</h3>
                  <p className="text-[12px] text-gray-500">Control traffic between resources</p>
                </div>
              </Link>

              {/* Subnets Card */}
              <Link
                to="/services/vpc/subnets"
                className="group"
              >
                <div className="bg-white rounded-lg border border-gray-200 shadow-[0_1px_3px_rgba(0,0,0,0.07)] hover:shadow-[0_8px_16px_rgba(0,0,0,0.1)] transition-all p-5 h-full hover:border-green-300 cursor-pointer">
                  <div className="flex items-center justify-between mb-4">
                    <div className="p-2.5 bg-green-50 rounded-lg group-hover:bg-green-100 transition-colors">
                      <Network className="w-5 h-5 text-green-600" />
                    </div>
                    <ArrowRight className="w-4 h-4 text-gray-400 group-hover:text-green-600 group-hover:translate-x-0.5 transition-all" />
                  </div>
                  <h3 className="text-[14px] font-semibold text-gray-900 mb-1">Subnets</h3>
                  <p className="text-[12px] text-gray-500">Create and manage subnets</p>
                </div>
              </Link>
            </div>
          </div>
        )}

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
        </>
        )} {/* end networks tab */}

        {/* Cloud Routers Tab */}
        {activeTab === 'routers' && (
          <div className="mb-8">
            <div className="flex items-center justify-between mb-4">
              <h2 className="text-[16px] font-bold text-gray-900">Cloud Routers</h2>
              <button onClick={() => setShowCreateRouter(true)}
                className="inline-flex items-center gap-2 px-3 h-9 bg-blue-600 text-white rounded-lg hover:bg-blue-700 text-[13px] font-medium">
                <Plus className="w-4 h-4" /> Create Router
              </button>
            </div>

            {showCreateRouter && (
              <div className="bg-blue-50 border border-blue-200 rounded-xl p-4 mb-4">
                <div className="grid grid-cols-2 gap-3 mb-3">
                  <div>
                    <label className="text-[12px] font-medium text-gray-700 block mb-1">Name</label>
                    <input value={routerForm.name} onChange={e => setRouterForm(f => ({ ...f, name: e.target.value }))}
                      placeholder="my-router" className="w-full px-3 py-2 text-[13px] border border-gray-300 rounded-lg focus:outline-none focus:border-blue-400" />
                  </div>
                  <div>
                    <label className="text-[12px] font-medium text-gray-700 block mb-1">Network</label>
                    <select value={routerForm.network} onChange={e => setRouterForm(f => ({ ...f, network: e.target.value }))}
                      className="w-full px-3 py-2 text-[13px] border border-gray-300 rounded-lg focus:outline-none focus:border-blue-400">
                      {networks.map(n => <option key={n.name} value={n.name}>{n.name}</option>)}
                    </select>
                  </div>
                  <div>
                    <label className="text-[12px] font-medium text-gray-700 block mb-1">Region</label>
                    <select value={routerForm.region} onChange={e => setRouterForm(f => ({ ...f, region: e.target.value }))}
                      className="w-full px-3 py-2 text-[13px] border border-gray-300 rounded-lg focus:outline-none focus:border-blue-400">
                      {['us-central1','us-east1','us-west1','europe-west1'].map(r => <option key={r} value={r}>{r}</option>)}
                    </select>
                  </div>
                  <div>
                    <label className="text-[12px] font-medium text-gray-700 block mb-1">BGP ASN</label>
                    <input value={routerForm.bgp_asn} onChange={e => setRouterForm(f => ({ ...f, bgp_asn: parseInt(e.target.value) || 64512 }))}
                      type="number" className="w-full px-3 py-2 text-[13px] border border-gray-300 rounded-lg focus:outline-none focus:border-blue-400" />
                  </div>
                </div>
                <div className="flex gap-2">
                  <button onClick={handleCreateRouter} disabled={creatingRouter || !routerForm.name}
                    className="px-4 py-2 bg-blue-600 text-white rounded-lg text-[13px] font-medium hover:bg-blue-700 disabled:opacity-50">
                    {creatingRouter ? 'Creating...' : 'Create'}
                  </button>
                  <button onClick={() => setShowCreateRouter(false)} className="px-4 py-2 text-gray-600 border border-gray-300 rounded-lg text-[13px] hover:bg-white">Cancel</button>
                </div>
              </div>
            )}

            <div className="bg-white rounded-lg border border-gray-200 shadow-sm">
              {routers.length === 0 ? (
                <div className="p-10 text-center">
                  <Router className="w-8 h-8 text-gray-300 mx-auto mb-2" />
                  <p className="text-[13px] text-gray-500">No Cloud Routers created yet</p>
                </div>
              ) : (
                <table className="w-full">
                  <thead><tr className="bg-gray-50 border-b border-gray-200">
                    {['Name','Region','Network','BGP ASN',''].map(h => (
                      <th key={h} className="px-4 py-3 text-left text-[12px] font-semibold text-gray-600">{h}</th>
                    ))}
                  </tr></thead>
                  <tbody className="divide-y divide-gray-100">
                    {routers.map(r => (
                      <tr key={r.id} className="hover:bg-gray-50">
                        <td className="px-4 py-3 text-[13px] font-medium text-gray-900">{r.name}</td>
                        <td className="px-4 py-3 text-[13px] text-gray-600">{r.region}</td>
                        <td className="px-4 py-3 text-[13px] text-gray-600">{r.network}</td>
                        <td className="px-4 py-3 text-[13px] font-mono text-gray-700">AS{r.bgp_asn || 64512}</td>
                        <td className="px-4 py-3 text-right">
                          <button onClick={() => handleDeleteRouter(r)} className="p-1.5 text-red-400 hover:text-red-600 hover:bg-red-50 rounded">
                            <Trash2 className="w-4 h-4" />
                          </button>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              )}
            </div>
          </div>
        )}

        {/* Cloud NAT Tab */}
        {activeTab === 'nat' && (
          <div className="mb-8">
            <div className="flex items-center justify-between mb-4">
              <h2 className="text-[16px] font-bold text-gray-900">Cloud NAT</h2>
              <button onClick={() => setShowCreateNAT(true)}
                className="inline-flex items-center gap-2 px-3 h-9 bg-blue-600 text-white rounded-lg hover:bg-blue-700 text-[13px] font-medium">
                <Plus className="w-4 h-4" /> Create NAT Gateway
              </button>
            </div>

            {showCreateNAT && (
              <div className="bg-blue-50 border border-blue-200 rounded-xl p-4 mb-4">
                <div className="grid grid-cols-2 gap-3 mb-3">
                  <div>
                    <label className="text-[12px] font-medium text-gray-700 block mb-1">NAT Name</label>
                    <input value={natForm.name} onChange={e => setNatForm(f => ({ ...f, name: e.target.value }))}
                      placeholder="my-nat-gateway" className="w-full px-3 py-2 text-[13px] border border-gray-300 rounded-lg focus:outline-none focus:border-blue-400" />
                  </div>
                  <div>
                    <label className="text-[12px] font-medium text-gray-700 block mb-1">Cloud Router</label>
                    <select value={natForm.router_name} onChange={e => setNatForm(f => ({ ...f, router_name: e.target.value }))}
                      className="w-full px-3 py-2 text-[13px] border border-gray-300 rounded-lg focus:outline-none focus:border-blue-400">
                      <option value="">Select router...</option>
                      {routers.map(r => <option key={r.name} value={r.name}>{r.name} ({r.region})</option>)}
                    </select>
                  </div>
                  <div>
                    <label className="text-[12px] font-medium text-gray-700 block mb-1">Region</label>
                    <select value={natForm.region} onChange={e => setNatForm(f => ({ ...f, region: e.target.value }))}
                      className="w-full px-3 py-2 text-[13px] border border-gray-300 rounded-lg focus:outline-none focus:border-blue-400">
                      {['us-central1','us-east1','us-west1','europe-west1'].map(r => <option key={r} value={r}>{r}</option>)}
                    </select>
                  </div>
                </div>
                <div className="flex gap-2">
                  <button onClick={handleCreateNAT} disabled={creatingNAT || !natForm.name || !natForm.router_name}
                    className="px-4 py-2 bg-blue-600 text-white rounded-lg text-[13px] font-medium hover:bg-blue-700 disabled:opacity-50">
                    {creatingNAT ? 'Creating...' : 'Create NAT Gateway'}
                  </button>
                  <button onClick={() => setShowCreateNAT(false)} className="px-4 py-2 text-gray-600 border border-gray-300 rounded-lg text-[13px] hover:bg-white">Cancel</button>
                </div>
              </div>
            )}

            <div className="bg-white rounded-lg border border-gray-200 shadow-sm">
              {nats.length === 0 ? (
                <div className="p-10 text-center">
                  <Globe className="w-8 h-8 text-gray-300 mx-auto mb-2" />
                  <p className="text-[13px] text-gray-500">No Cloud NAT gateways configured</p>
                  <p className="text-[12px] text-gray-400 mt-1">Select a Cloud Router above to create a NAT gateway, or create a router first</p>
                </div>
              ) : (
                <table className="w-full">
                  <thead><tr className="bg-gray-50 border-b border-gray-200">
                    {['Name','Router','Region','NAT IP Allocation',''].map(h => (
                      <th key={h} className="px-4 py-3 text-left text-[12px] font-semibold text-gray-600">{h}</th>
                    ))}
                  </tr></thead>
                  <tbody className="divide-y divide-gray-100">
                    {nats.map(n => (
                      <tr key={n.id} className="hover:bg-gray-50">
                        <td className="px-4 py-3 text-[13px] font-medium text-gray-900">{n.name}</td>
                        <td className="px-4 py-3 text-[13px] text-blue-600">{n.router_name}</td>
                        <td className="px-4 py-3 text-[13px] text-gray-600">{n.region}</td>
                        <td className="px-4 py-3 text-[13px] text-gray-600">{n.nat_ip_allocate_option || 'AUTO_ONLY'}</td>
                        <td className="px-4 py-3 text-right">
                          <button onClick={() => handleDeleteNAT(n)} className="p-1.5 text-red-400 hover:text-red-600 hover:bg-red-50 rounded">
                            <Trash2 className="w-4 h-4" />
                          </button>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              )}
            </div>
          </div>
        )}

        {/* VPC Peering Tab */}
        {activeTab === 'peering' && (
          <div className="mb-8">
            <div className="flex items-center justify-between mb-4">
              <h2 className="text-[16px] font-bold text-gray-900">VPC Peering</h2>
              <button onClick={() => setShowCreatePeering(true)}
                className="inline-flex items-center gap-2 px-3 h-9 bg-blue-600 text-white rounded-lg hover:bg-blue-700 text-[13px] font-medium">
                <Plus className="w-4 h-4" /> Add Peering
              </button>
            </div>

            {showCreatePeering && (
              <div className="bg-blue-50 border border-blue-200 rounded-xl p-4 mb-4">
                <div className="grid grid-cols-2 gap-3 mb-3">
                  <div>
                    <label className="text-[12px] font-medium text-gray-700 block mb-1">Peering Name</label>
                    <input value={peeringForm.name} onChange={e => setPeeringForm(f => ({ ...f, name: e.target.value }))}
                      placeholder="peer-to-project-b" className="w-full px-3 py-2 text-[13px] border border-gray-300 rounded-lg focus:outline-none focus:border-blue-400" />
                  </div>
                  <div>
                    <label className="text-[12px] font-medium text-gray-700 block mb-1">Your Network</label>
                    <select value={peeringForm.network} onChange={e => setPeeringForm(f => ({ ...f, network: e.target.value }))}
                      className="w-full px-3 py-2 text-[13px] border border-gray-300 rounded-lg focus:outline-none focus:border-blue-400">
                      {networks.map(n => <option key={n.name} value={n.name}>{n.name}</option>)}
                    </select>
                  </div>
                  <div className="col-span-2">
                    <label className="text-[12px] font-medium text-gray-700 block mb-1">Peer Network (projects/PROJECT/global/networks/NETWORK)</label>
                    <input value={peeringForm.peer_network} onChange={e => setPeeringForm(f => ({ ...f, peer_network: e.target.value }))}
                      placeholder="projects/peer-project/global/networks/default"
                      className="w-full px-3 py-2 text-[13px] border border-gray-300 rounded-lg focus:outline-none focus:border-blue-400" />
                  </div>
                </div>
                <div className="flex gap-2">
                  <button onClick={handleAddPeering} disabled={creatingPeering || !peeringForm.name || !peeringForm.peer_network}
                    className="px-4 py-2 bg-blue-600 text-white rounded-lg text-[13px] font-medium hover:bg-blue-700 disabled:opacity-50">
                    {creatingPeering ? 'Adding...' : 'Add Peering'}
                  </button>
                  <button onClick={() => setShowCreatePeering(false)} className="px-4 py-2 text-gray-600 border border-gray-300 rounded-lg text-[13px] hover:bg-white">Cancel</button>
                </div>
              </div>
            )}

            <div className="bg-white rounded-lg border border-gray-200 shadow-sm">
              {peerings.length === 0 ? (
                <div className="p-10 text-center">
                  <Share2 className="w-8 h-8 text-gray-300 mx-auto mb-2" />
                  <p className="text-[13px] text-gray-500">No VPC peering connections</p>
                </div>
              ) : (
                <table className="w-full">
                  <thead><tr className="bg-gray-50 border-b border-gray-200">
                    {['Name','Network','Peer Network','State',''].map(h => (
                      <th key={h} className="px-4 py-3 text-left text-[12px] font-semibold text-gray-600">{h}</th>
                    ))}
                  </tr></thead>
                  <tbody className="divide-y divide-gray-100">
                    {peerings.map(p => (
                      <tr key={p.id} className="hover:bg-gray-50">
                        <td className="px-4 py-3 text-[13px] font-medium text-gray-900">{p.name}</td>
                        <td className="px-4 py-3 text-[13px] text-gray-600">{p.network}</td>
                        <td className="px-4 py-3 text-[13px] font-mono text-gray-600 text-xs">{p.peer_network}</td>
                        <td className="px-4 py-3">
                          <span className={`inline-flex px-2 py-0.5 rounded text-[11px] font-medium ${
                            p.state === 'ACTIVE' ? 'bg-green-100 text-green-700' : 'bg-yellow-100 text-yellow-700'
                          }`}>{p.state}</span>
                        </td>
                        <td className="px-4 py-3 text-right">
                          <button onClick={() => handleRemovePeering(p)} className="p-1.5 text-red-400 hover:text-red-600 hover:bg-red-50 rounded">
                            <Trash2 className="w-4 h-4" />
                          </button>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              )}
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
              name="subnet-mode"
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
              <Link
                to="/services/vpc/routes"
                className="flex-1 inline-flex items-center justify-center gap-2 px-4 py-2.5 bg-purple-600 text-white rounded-lg hover:bg-purple-700 transition-all text-[13px] font-medium"
              >
                <Route className="w-4 h-4" />
                View Routes
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
