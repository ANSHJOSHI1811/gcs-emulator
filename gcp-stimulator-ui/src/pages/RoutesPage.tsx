import { useEffect, useState } from 'react';
import { useProject } from '../contexts/ProjectContext';
import { useNavigate } from 'react-router-dom';
import { Plus, Trash2, RefreshCw, AlertCircle, Network, Route, Globe, ArrowRight } from 'lucide-react';
import { apiClient } from '../api/client';
import { Modal, ModalFooter, ModalButton } from '../components/Modal';
import { FormField, Input, Select } from '../components/FormFields';

interface RouteRule {
  id: string;
  name: string;
  network: string;
  destRange: string;
  priority: number;
  nextHopGateway?: string;
  nextHopIp?: string;
  nextHopInstance?: string;
  nextHopNetwork?: string;
  description?: string;
  creationTimestamp?: string;
}

interface NetworkOption {
  name: string;
  selfLink: string;
}

const RoutesPage = () => {
  const { currentProject } = useProject();
  const navigate = useNavigate();
  const [routes, setRoutes] = useState<RouteRule[]>([]);
  const [networks, setNetworks] = useState<NetworkOption[]>([]);
  const [selectedNetwork, setSelectedNetwork] = useState<string>('all');
  const [loading, setLoading] = useState(true);
  const [showCreateModal, setShowCreateModal] = useState(false);
  const [createLoading, setCreateLoading] = useState(false);
  const [deleteLoading, setDeleteLoading] = useState<string | null>(null);
  const [formData, setFormData] = useState({
    name: '',
    network: '',
    destRange: '',
    priority: 1000,
    nextHopType: 'gateway',
    nextHopValue: 'default-internet-gateway',
    description: '',
  });
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    loadData(true); // Initial load with loading indicator
    const interval = setInterval(() => {
      loadData(false); // Auto-refresh without loading indicator
    }, 30000); // Changed to 30 seconds
    return () => clearInterval(interval);
  }, [currentProject]);

  const loadData = async (showLoading = true) => {
    try {
      if (showLoading) {
        setLoading(true);
      }
      setError(null);

      // Load networks
      const networksRes = await apiClient.get(`/compute/v1/projects/${currentProject}/global/networks`);
      setNetworks(networksRes.data.items || []);

      // Load routes
      const routesRes = await apiClient.get(`/compute/v1/projects/${currentProject}/global/routes`);
      setRoutes(routesRes.data.items || []);
    } catch (error: any) {
      console.error('Failed to load routes:', error);
      setError('Failed to load routes. Please try again.');
    } finally {
      if (showLoading) {
        setLoading(false);
      }
    }
  };

  const handleCreate = async (e: React.FormEvent) => {
    e.preventDefault();
    setCreateLoading(true);
    setError(null);

    try {
      const routeData: any = {
        name: formData.name,
        network: `https://www.googleapis.com/compute/v1/projects/${currentProject}/global/networks/${formData.network}`,
        destRange: formData.destRange,
        priority: formData.priority,
      };

      if (formData.description) {
        routeData.description = formData.description;
      }

      // Set next hop based on type
      switch (formData.nextHopType) {
        case 'gateway':
          routeData.nextHopGateway = formData.nextHopValue;
          break;
        case 'ip':
          routeData.nextHopIp = formData.nextHopValue;
          break;
        case 'instance':
          routeData.nextHopInstance = formData.nextHopValue;
          break;
        case 'network':
          routeData.nextHopNetwork = formData.nextHopValue;
          break;
      }

      await apiClient.post(`/compute/v1/projects/${currentProject}/global/routes`, routeData);

      setShowCreateModal(false);
      setFormData({
        name: '',
        network: '',
        destRange: '',
        priority: 1000,
        nextHopType: 'gateway',
        nextHopValue: 'default-internet-gateway',
        description: '',
      });
      await loadData();
    } catch (error: any) {
      console.error('Failed to create route:', error);
      setError(error.response?.data?.detail || 'Failed to create route');
    } finally {
      setCreateLoading(false);
    }
  };

  const handleDelete = async (routeName: string) => {
    if (!confirm(`Are you sure you want to delete route "${routeName}"?`)) {
      return;
    }

    setDeleteLoading(routeName);
    setError(null);

    try {
      await apiClient.delete(`/compute/v1/projects/${currentProject}/global/routes/${routeName}`);
      await loadData();
    } catch (error: any) {
      console.error('Failed to delete route:', error);
      setError(error.response?.data?.detail || 'Failed to delete route');
    } finally {
      setDeleteLoading(null);
    }
  };

  const getNetworkName = (network: string) => {
    const match = network.match(/\/networks\/(.+?)(?:\/|$)/);
    return match ? match[1] : network;
  };

  const getNextHopDisplay = (route: RouteRule) => {
    if (route.nextHopGateway) return { type: 'Gateway', value: route.nextHopGateway };
    if (route.nextHopIp) return { type: 'IP Address', value: route.nextHopIp };
    if (route.nextHopInstance) return { type: 'Instance', value: route.nextHopInstance.split('/').pop() || route.nextHopInstance };
    if (route.nextHopNetwork) return { type: 'Network', value: route.nextHopNetwork.split('/').pop() || route.nextHopNetwork };
    return { type: 'Unknown', value: '-' };
  };

  // Filter routes by selected network
  const filteredRoutes = routes.filter(route => {
    if (selectedNetwork === 'all') return true;
    return getNetworkName(route.network) === selectedNetwork;
  });

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="text-center">
          <div className="inline-block animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600 mb-4"></div>
          <p className="text-gray-600">Loading routes...</p>
        </div>
      </div>
    );
  }

  // Count routes by network
  const routesByNetwork = routes.reduce((acc, route) => {
    const netName = getNetworkName(route.network);
    acc[netName] = (acc[netName] || 0) + 1;
    return acc;
  }, {} as Record<string, number>);

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <div className="bg-white border-b border-gray-200">
        <div className="max-w-[1400px] mx-auto px-8 py-5">
          <div className="flex items-center justify-between mb-4">
            <div>
              <h1 className="text-[22px] font-normal text-gray-900">Routes</h1>
              <p className="text-[13px] text-gray-600 mt-1">
                Routes define paths for network traffic in your VPC networks
              </p>
            </div>
            <button
              onClick={() => setShowCreateModal(true)}
              className="flex items-center gap-2 px-4 py-2 bg-blue-600 text-white rounded hover:bg-blue-700 transition-colors text-[13px] font-medium shadow-sm"
            >
              <Plus className="w-4 h-4" />
              CREATE ROUTE
            </button>
          </div>
          
          {/* Network Filter */}
          {networks.length > 0 && (
            <div className="flex items-center gap-3 pt-3 border-t border-gray-100">
              <label className="text-[13px] font-medium text-gray-700 min-w-[80px]">
                Filter by network:
              </label>
              <select
                value={selectedNetwork}
                onChange={(e) => setSelectedNetwork(e.target.value)}
                className="px-3 py-1.5 border border-gray-300 rounded text-[13px] focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent bg-white"
              >
                <option value="all">All networks</option>
                {networks.map((network) => {
                  const count = routesByNetwork[network.name] || 0;
                  return (
                    <option key={network.name} value={network.name}>
                      {network.name} ({count})
                    </option>
                  );
                })}
              </select>
              {selectedNetwork !== 'all' && (
                <button
                  onClick={() => setSelectedNetwork('all')}
                  className="text-[13px] text-blue-600 hover:text-blue-700 font-medium"
                >
                  Clear
                </button>
              )}
            </div>
          )}
        </div>
      </div>

      {/* Error Message */}
      {error && (
        <div className="max-w-[1400px] mx-auto px-8 pt-6">
          <div className="bg-red-50 border border-red-200 text-red-800 px-4 py-3 rounded flex items-start gap-2">
            <AlertCircle className="w-5 h-5 flex-shrink-0 mt-0.5" />
            <div className="flex-1">
              <p className="text-[13px]">{error}</p>
              <button
                onClick={loadData}
                className="mt-2 text-[13px] text-blue-600 hover:underline font-medium"
              >
                Try again
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Routes Grid */}
      <div className="max-w-[1400px] mx-auto px-8 py-6">
        {loading ? (
          <div className="flex items-center justify-center py-20 bg-white rounded border border-gray-300">
            <RefreshCw className="w-6 h-6 text-blue-600 animate-spin" />
          </div>
        ) : filteredRoutes.length === 0 ? (
          <div className="text-center py-16 bg-white rounded border border-gray-300">
            <Route className="w-12 h-12 text-gray-400 mx-auto mb-3" />
            <h3 className="text-[16px] font-medium text-gray-900 mb-1">
              {selectedNetwork === 'all' ? 'No routes' : `No routes in ${selectedNetwork}`}
            </h3>
            <p className="text-[13px] text-gray-600 mb-4">
              {selectedNetwork === 'all'
                ? 'Create a route to get started'
                : 'This network has no routes'}
            </p>
            {routes.length === 0 && (
              <button
                onClick={() => setShowCreateModal(true)}
                className="inline-flex items-center gap-2 px-4 py-2 bg-blue-600 text-white rounded hover:bg-blue-700 text-[13px] font-medium"
              >
                <Plus className="w-4 h-4" />
                CREATE ROUTE
              </button>
            )}
          </div>
        ) : (
          <div className="bg-white rounded border border-gray-300 overflow-hidden">
            <div className="overflow-x-auto">
              <table className="min-w-full divide-y divide-gray-200">
                <thead className="bg-gray-50">
                  <tr>
                    <th scope="col" className="px-4 py-3 text-left text-[11px] font-medium text-gray-700 uppercase tracking-wide">
                      Name
                    </th>
                    <th scope="col" className="px-4 py-3 text-left text-[11px] font-medium text-gray-700 uppercase tracking-wide">
                      Description
                    </th>
                    <th scope="col" className="px-4 py-3 text-left text-[11px] font-medium text-gray-700 uppercase tracking-wide">
                      Destination IP range
                    </th>
                    <th scope="col" className="px-4 py-3 text-left text-[11px] font-medium text-gray-700 uppercase tracking-wide">
                      Priority
                    </th>
                    <th scope="col" className="px-4 py-3 text-left text-[11px] font-medium text-gray-700 uppercase tracking-wide">
                      Network
                    </th>
                    <th scope="col" className="px-4 py-3 text-left text-[11px] font-medium text-gray-700 uppercase tracking-wide">
                      Next hop
                    </th>
                    <th scope="col" className="relative px-4 py-3">
                      <span className="sr-only">Actions</span>
                    </th>
                  </tr>
                </thead>
                <tbody className="bg-white divide-y divide-gray-200">
                  {filteredRoutes.map((route) => {
                    const nextHop = getNextHopDisplay(route);
                    const networkName = getNetworkName(route.network);
                    
                    return (
                      <tr key={route.id} className="hover:bg-blue-50 transition-colors group">
                        <td className="px-4 py-3 whitespace-nowrap">
                          <div className="flex items-center gap-2">
                            <Route className="w-4 h-4 text-gray-400 flex-shrink-0" />
                            <button className="text-[13px] text-blue-600 hover:underline font-normal">
                              {route.name}
                            </button>
                          </div>
                        </td>
                        <td className="px-4 py-3">
                          <span className="text-[13px] text-gray-700 max-w-xs block truncate" title={route.description}>
                            {route.description || '—'}
                          </span>
                        </td>
                        <td className="px-4 py-3 whitespace-nowrap">
                          <code className="text-[13px] text-gray-900 font-mono">
                            {route.destRange}
                          </code>
                        </td>
                        <td className="px-4 py-3 whitespace-nowrap">
                          <span className="text-[13px] text-gray-900">{route.priority}</span>
                        </td>
                        <td className="px-4 py-3 whitespace-nowrap">
                          <span className="text-[13px] text-gray-900">{networkName}</span>
                        </td>
                        <td className="px-4 py-3">
                          <div className="text-[13px]">
                            <div className="text-gray-900">{nextHop.type}</div>
                            <div className="text-gray-600 text-[12px] mt-0.5">{nextHop.value}</div>
                          </div>
                        </td>
                        <td className="px-4 py-3 whitespace-nowrap text-right">
                          <button
                            onClick={() => handleDelete(route.name)}
                            disabled={deleteLoading === route.name}
                            className="opacity-0 group-hover:opacity-100 inline-flex items-center gap-1 p-1.5 text-gray-500 hover:text-red-600 hover:bg-red-50 rounded transition-all disabled:opacity-100"
                            title="Delete route"
                          >
                            {deleteLoading === route.name ? (
                              <RefreshCw className="w-4 h-4 animate-spin" />
                            ) : (
                              <Trash2 className="w-4 h-4" />
                            )}
                          </button>
                        </td>
                      </tr>
                    );
                  })}
                </tbody>
              </table>
            </div>
            
            {/* Table Footer with Count */}
            <div className="bg-white border-t border-gray-200 px-4 py-3">
              <p className="text-[13px] text-gray-700">
                {filteredRoutes.length} {filteredRoutes.length === 1 ? 'item' : 'items'}
              </p>
            </div>
          </div>
        )}
      </div>

      {/* Create Modal */}
      <Modal
        isOpen={showCreateModal}
        onClose={() => setShowCreateModal(false)}
        title="Create New Route"
        size="lg"
      >
        <form onSubmit={handleCreate} className="space-y-5">
          <FormField label="Route Name" required help="Lowercase letters, numbers, and hyphens only">
            <Input
              type="text"
              value={formData.name}
              onChange={(e) => setFormData({ ...formData, name: e.target.value.toLowerCase() })}
              placeholder="my-custom-route"
              required
            />
          </FormField>

          <FormField label="Network" required help="VPC network this route will belong to">
            <Select
              value={formData.network}
              onChange={(e) => setFormData({ ...formData, network: e.target.value })}
              required
            >
              <option value="">Select a network</option>
              {networks.map((network) => (
                <option key={network.name} value={network.name}>
                  {network.name}
                </option>
              ))}
            </Select>
          </FormField>

          <FormField label="Destination IP Range" required help="Traffic destination range in CIDR notation (e.g., 0.0.0.0/0 for internet)">
            <Input
              type="text"
              value={formData.destRange}
              onChange={(e) => setFormData({ ...formData, destRange: e.target.value })}
              placeholder="0.0.0.0/0 or 192.168.0.0/24"
              className="font-mono"
              required
            />
          </FormField>

          <FormField label="Priority" required help="Lower values have higher priority (0-65535)">
            <Input
              type="number"
              value={formData.priority}
              onChange={(e) => setFormData({ ...formData, priority: parseInt(e.target.value) })}
              min="0"
              max="65535"
              required
            />
          </FormField>

          <FormField label="Next Hop Type" required>
            <Select
              value={formData.nextHopType}
              onChange={(e) => {
                const type = e.target.value;
                setFormData({
                  ...formData,
                  nextHopType: type,
                  nextHopValue: type === 'gateway' ? 'default-internet-gateway' : '',
                });
              }}
            >
              <option value="gateway">Gateway (Internet)</option>
              <option value="ip">IP Address</option>
              <option value="instance">Instance</option>
              <option value="network">Network</option>
            </Select>
          </FormField>

          <FormField
            label="Next Hop Value"
            required
            help={
              formData.nextHopType === 'gateway' ? 'Use "default-internet-gateway" for internet access' :
              formData.nextHopType === 'ip' ? 'IP address to route traffic to' :
              formData.nextHopType === 'instance' ? 'Name of the instance to route traffic to' :
              'Name of the network to route traffic to'
            }
          >
            {formData.nextHopType === 'gateway' ? (
              <Select
                value={formData.nextHopValue}
                onChange={(e) => setFormData({ ...formData, nextHopValue: e.target.value })}
                required
              >
                <option value="default-internet-gateway">Default Internet Gateway</option>
              </Select>
            ) : (
              <Input
                type="text"
                value={formData.nextHopValue}
                onChange={(e) => setFormData({ ...formData, nextHopValue: e.target.value })}
                placeholder={
                  formData.nextHopType === 'ip'
                    ? '10.0.0.1'
                    : formData.nextHopType === 'instance'
                    ? 'instance-name'
                    : 'network-name'
                }
                required
              />
            )}
          </FormField>

          <FormField label="Description (Optional)">
            <Input
              type="text"
              value={formData.description}
              onChange={(e) => setFormData({ ...formData, description: e.target.value })}
              placeholder="Route for production traffic"
            />
          </FormField>

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
              {createLoading ? (
                <>
                  <RefreshCw className="w-4 h-4 animate-spin mr-2" />
                  Creating...
                </>
              ) : (
                <>
                  <Plus className="w-4 h-4 mr-2" />
                  Create Route
                </>
              )}
            </ModalButton>
          </ModalFooter>
        </form>
      </Modal>
    </div>
  );
};

export default RoutesPage;
