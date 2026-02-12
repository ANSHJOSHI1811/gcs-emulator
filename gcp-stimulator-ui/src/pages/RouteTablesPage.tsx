import React, { useEffect, useState } from 'react';
import { useProject } from '../contexts/ProjectContext';
import { Plus, Trash2, RefreshCw, AlertCircle, Network, Route, Globe, ArrowRight, MapPin, Zap } from 'lucide-react';
import { apiClient } from '../api/client';
import { Modal, ModalFooter, ModalButton } from '../components/Modal';
import { FormField, Input, Select } from '../components/FormFields';

interface RouteData {
  kind: string;
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
  tags?: string[];
  creationTimestamp?: string;
}

interface NetworkOption {
  name: string;
  selfLink: string;
}

const RouteTablesPage = () => {
  const { currentProject } = useProject();
  const [routes, setRoutes] = useState<RouteData[]>([]);
  const [networks, setNetworks] = useState<NetworkOption[]>([]);
  const [selectedNetwork, setSelectedNetwork] = useState<string>('all');
  const [loading, setLoading] = useState(true);
  const [showCreateModal, setShowCreateModal] = useState(false);
  const [createLoading, setCreateLoading] = useState(false);
  const [deleteLoading, setDeleteLoading] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [formData, setFormData] = useState({
    name: '',
    network: '',
    destRange: '',
    priority: '1000',
    nextHopType: 'gateway',
    nextHopValue: 'default-internet-gateway',
    description: '',
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
      setLoading(true);
      setError(null);

      // Load networks
      const networksRes = await apiClient.get(`/compute/v1/projects/${currentProject}/global/networks`);
      setNetworks(networksRes?.data?.items || []);

      // Load routes
      const routesRes = await apiClient.get(`/compute/v1/projects/${currentProject}/global/routes`);
      setRoutes(routesRes?.data?.items || []);
    } catch (error: any) {
      console.error('Failed to load routes:', error);
      setError('Failed to load routes. Please try again.');
    } finally {
      setLoading(false);
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
        priority: parseInt(formData.priority),
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
      
      // Reset form and reload
      setFormData({
        name: '',
        network: '',
        destRange: '',
        priority: '1000',
        nextHopType: 'gateway',
        nextHopValue: 'default-internet-gateway',
        description: '',
      });
      setShowCreateModal(false);
      await loadData();
    } catch (error: any) {
      console.error('Failed to create route:', error);
      setError(error.response?.data?.detail || 'Failed to create route. Please try again.');
    } finally {
      setCreateLoading(false);
    }
  };

  const handleDelete = async (routeName: string) => {
    if (!confirm(`Are you sure you want to delete route "${routeName}"?`)) return;

    setDeleteLoading(routeName);
    setError(null);

    try {
      await apiClient.delete(`/compute/v1/projects/${currentProject}/global/routes/${routeName}`);
      await loadData();
    } catch (error: any) {
      console.error('Failed to delete route:', error);
      setError(error.response?.data?.detail || 'Failed to delete route. Please try again.');
    } finally {
      setDeleteLoading(null);
    }
  };

  const getNetworkName = (network: string) => {
    const match = network.match(/\/networks\/(.+?)(?:\/|$)/);
    return match ? match[1] : network;
  };

  const getNextHopDisplay = (route: RouteData) => {
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
        <div className="max-w-[1400px] mx-auto px-8 py-6">
          <div className="flex items-center justify-between mb-4">
            <div className="flex items-center gap-4">
              <div className="p-3 bg-gradient-to-br from-purple-500 to-purple-600 rounded-xl shadow-lg">
                <Route className="w-7 h-7 text-white" />
              </div>
              <div>
                <h1 className="text-[28px] font-bold text-gray-900">Routes</h1>
                <p className="text-[14px] text-gray-600 mt-0.5">
                  {routes.length} {routes.length === 1 ? 'route' : 'routes'} across {networks.length} {networks.length === 1 ? 'network' : 'networks'}
                </p>
              </div>
            </div>
            <button
              onClick={() => setShowCreateModal(true)}
              className="flex items-center gap-2 px-5 py-2.5 bg-purple-600 text-white rounded-lg hover:bg-purple-700 transition-all shadow-md hover:shadow-lg text-[14px] font-medium"
            >
              <Plus className="w-4 h-4" />
              Create Route
            </button>
          </div>
          
          {/* Network Filter */}
          {networks.length > 0 && (
            <div className="flex items-center gap-4 bg-gradient-to-r from-purple-50 to-blue-50 px-5 py-4 rounded-xl border border-purple-100">
              <Network className="w-5 h-5 text-purple-600" />
              <span className="text-[14px] font-semibold text-gray-900">Filter by VPC:</span>
              <select
                value={selectedNetwork}
                onChange={(e) => setSelectedNetwork(e.target.value)}
                className="px-4 py-2.5 border-2 border-purple-300 rounded-lg text-[14px] font-medium focus:outline-none focus:ring-2 focus:ring-purple-500 focus:border-purple-500 bg-white min-w-[280px] shadow-sm"
              >
                <option value="all">All Networks ({routes.length} {routes.length === 1 ? 'route' : 'routes'})</option>
                {networks.map((network) => {
                  const count = routesByNetwork[network.name] || 0;
                  return (
                    <option key={network.name} value={network.name}>
                      {network.name} ({count} {count === 1 ? 'route' : 'routes'})
                    </option>
                  );
                })}
              </select>
              {selectedNetwork !== 'all' && (
                <button
                  onClick={() => setSelectedNetwork('all')}
                  className="px-4 py-2 text-[13px] text-purple-700 hover:text-purple-800 font-semibold bg-white hover:bg-purple-50 rounded-lg transition-all border border-purple-200 shadow-sm"
                >
                  Clear filter
                </button>
              )}
            </div>
          )}
        </div>
      </div>

      {/* Error Message */}
      {error && (
        <div className="max-w-[1400px] mx-auto px-8 pt-6">
          <div className="bg-red-50 border-2 border-red-200 text-red-700 px-6 py-4 rounded-xl flex items-start gap-3 shadow-sm">
            <AlertCircle className="w-5 h-5 flex-shrink-0 mt-0.5" />
            <p className="text-[14px]">{error}</p>
          </div>
        </div>
      )}

      {/* Routes Grid */}
      <div className="max-w-[1400px] mx-auto px-8 py-6">
        {filteredRoutes.length === 0 ? (
          <div className="text-center py-16 bg-white rounded-xl border-2 border-dashed border-gray-300 shadow-sm">
            <div className="w-20 h-20 bg-gradient-to-br from-purple-100 to-blue-100 rounded-full flex items-center justify-center mx-auto mb-4">
              <Route className="w-10 h-10 text-purple-600" />
            </div>
            <h3 className="text-[18px] font-semibold text-gray-900 mb-2">
              {selectedNetwork === 'all' ? 'No routes yet' : `No routes for ${selectedNetwork}`}
            </h3>
            <p className="text-[14px] text-gray-600 mb-6">
              {selectedNetwork === 'all'
                ? 'Create your first route to control traffic flow in your VPC networks'
                : 'Try selecting a different network or create a new route for this network'
              }
            </p>
            {routes.length === 0 && (
              <button
                onClick={() => setShowCreateModal(true)}
                className="inline-flex items-center gap-2 px-5 py-2.5 bg-purple-600 text-white rounded-lg hover:bg-purple-700 transition-all shadow-md text-[14px] font-medium"
              >
                <Plus className="w-4 h-4" />
                Create Your First Route
              </button>
            )}
          </div>
        ) : (
          <div className="grid grid-cols-1 lg:grid-cols-2 xl:grid-cols-3 gap-5">
            {filteredRoutes.map((route) => {
              const nextHop = getNextHopDisplay(route);
              const networkName = getNetworkName(route.network);
              
              return (
                <div
                  key={route.id}
                  className="bg-white rounded-xl border border-gray-200 shadow-sm hover:shadow-lg transition-all group overflow-hidden"
                >
                  {/* Card Header */}
                  <div className="p-5 border-b border-gray-100 bg-gradient-to-r from-purple-50 to-blue-50">
                    <div className="flex items-start justify-between mb-3">
                      <div className="flex items-start gap-3 flex-1 min-w-0">
                        <div className="p-2 bg-purple-600 rounded-lg shadow-sm flex-shrink-0">
                          <Route className="w-5 h-5 text-white" />
                        </div>
                        <div className="flex-1 min-w-0">
                          <h3 className="text-[15px] font-bold text-gray-900 truncate mb-1" title={route.name}>
                            {route.name}
                          </h3>
                          <span className="inline-block px-2.5 py-1 bg-white rounded-full text-[11px] font-medium text-gray-700 shadow-sm">
                            Priority: {route.priority}
                          </span>
                        </div>
                      </div>
                      <button
                        onClick={() => handleDelete(route.name)}
                        disabled={deleteLoading === route.name}
                        className="p-2 text-red-600 hover:bg-red-50 rounded-lg transition-all flex-shrink-0 disabled:opacity-50"
                        title="Delete route"
                      >
                        {deleteLoading === route.name ? (
                          <RefreshCw className="w-4 h-4 animate-spin" />
                        ) : (
                          <Trash2 className="w-4 h-4" />
                        )}
                      </button>
                    </div>
                  </div>

                  {/* Card Body */}
                  <div className="p-5 space-y-4">
                    {/* Network */}
                    <div className="flex items-center gap-3 p-3 bg-gradient-to-r from-blue-50 to-purple-50 rounded-lg">
                      <div className="p-2 bg-white rounded-lg shadow-sm">
                        <Network className="w-4 h-4 text-blue-600" />
                      </div>
                      <div className="flex-1 min-w-0">
                        <div className="text-[11px] text-gray-600 mb-0.5">Network</div>
                        <div className={`text-[13px] font-semibold truncate ${
                          networkName === 'default' ? 'text-gray-900' :
                          networkName === 'vpc-prod' ? 'text-purple-700' :
                          networkName === 'vpc-dev' ? 'text-green-700' :
                          'text-blue-700'
                        }`} title={networkName}>
                          {networkName}
                        </div>
                      </div>
                    </div>

                    {/* Destination Range */}
                    <div className="flex items-center gap-3 p-3 bg-gray-50 rounded-lg">
                      <div className="p-2 bg-white rounded-lg shadow-sm">
                        <Globe className="w-4 h-4 text-green-600" />
                      </div>
                      <div className="flex-1 min-w-0">
                        <div className="text-[11px] text-gray-600 mb-0.5">Destination</div>
                        <div className="text-[13px] font-mono font-semibold text-gray-900" title={route.destRange}>
                          {route.destRange}
                        </div>
                      </div>
                    </div>

                    {/* Next Hop */}
                    <div className="flex items-center gap-3 p-3 bg-gradient-to-r from-orange-50 to-yellow-50 rounded-lg">
                      <div className="p-2 bg-white rounded-lg shadow-sm">
                        <ArrowRight className="w-4 h-4 text-orange-600" />
                      </div>
                      <div className="flex-1 min-w-0">
                        <div className="text-[11px] text-gray-600 mb-0.5">Next Hop ({nextHop.type})</div>
                        <div className="text-[13px] font-semibold text-gray-900 truncate" title={nextHop.value}>
                          {nextHop.value}
                        </div>
                      </div>
                    </div>

                    {/* Description (if exists) */}
                    {route.description && (
                      <div className="pt-3 border-t border-gray-100">
                        <div className="text-[11px] text-gray-600 mb-1">Description</div>
                        <div className="text-[12px] text-gray-700 leading-relaxed">
                          {route.description}
                        </div>
                      </div>
                    )}
                  </div>
                </div>
              );
            })}
          </div>
        )}
      </div>

      {/* Create Route Modal */}
      <Modal
        isOpen={showCreateModal}
        onClose={() => setShowCreateModal(false)}
        title="Create New Route"
        size="lg"
      >
        <form onSubmit={handleCreate} className="space-y-5">
          <FormField label="Route Name" required>
            <Input
              type="text"
              value={formData.name}
              onChange={(e) => setFormData({ ...formData, name: e.target.value })}
              placeholder="my-custom-route"
              required
            />
            <p className="text-[12px] text-gray-500 mt-1">
              Unique name for this route
            </p>
          </FormField>

          <FormField label="Network" required>
            <Select
              value={formData.network}
              onChange={(e) => setFormData({ ...formData, network: e.target.value })}
              required
            >
              <option value="">Select a network</option>
              {networks.map((net) => (
                <option key={net.name} value={net.name}>
                  {net.name}
                </option>
              ))}
            </Select>
            <p className="text-[12px] text-gray-500 mt-1">
              VPC network this route will belong to
            </p>
          </FormField>

          <FormField label="Destination IP Range" required>
            <Input
              type="text"
              value={formData.destRange}
              onChange={(e) => setFormData({ ...formData, destRange: e.target.value })}
              placeholder="0.0.0.0/0 or 192.168.0.0/24"
              required
            />
            <p className="text-[12px] text-gray-500 mt-1">
              Traffic destination range in CIDR notation (e.g., 0.0.0.0/0 for internet)
            </p>
          </FormField>

          <FormField label="Priority" required>
            <Input
              type="number"
              value={formData.priority}
              onChange={(e) => setFormData({ ...formData, priority: e.target.value })}
              min="0"
              max="65535"
              required
            />
            <p className="text-[12px] text-gray-500 mt-1">
              Lower values have higher priority (0-65535)
            </p>
          </FormField>

          <FormField label="Next Hop Type" required>
            <Select
              value={formData.nextHopType}
              onChange={(e) => {
                const newType = e.target.value;
                let newValue = 'default-internet-gateway';
                if (newType === 'ip') newValue = '10.0.0.1';
                if (newType === 'instance') newValue = 'my-instance';
                if (newType === 'network') newValue = 'default';
                setFormData({ ...formData, nextHopType: newType, nextHopValue: newValue });
              }}
            >
              <option value="gateway">Gateway (Internet)</option>
              <option value="ip">IP Address</option>
              <option value="instance">Instance</option>
              <option value="network">Network</option>
            </Select>
          </FormField>

          <FormField label="Next Hop Value" required>
            <Input
              type="text"
              value={formData.nextHopValue}
              onChange={(e) => setFormData({ ...formData, nextHopValue: e.target.value })}
              placeholder={
                formData.nextHopType === 'gateway'
                  ? 'default-internet-gateway'
                  : formData.nextHopType === 'ip'
                  ? '10.0.0.1'
                  : formData.nextHopType === 'instance'
                  ? 'instance-name'
                  : 'network-name'
              }
              required
            />
            <p className="text-[12px] text-gray-500 mt-1">
              {formData.nextHopType === 'gateway' && 'Use "default-internet-gateway" for internet access'}
              {formData.nextHopType === 'ip' && 'IP address to route traffic to'}
              {formData.nextHopType === 'instance' && 'Name of the instance to route traffic to'}
              {formData.nextHopType === 'network' && 'Name of the network to route traffic to'}
            </p>
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
              onClick={() => setShowCreateModal(false)}
              variant="secondary"
            >
              Cancel
            </ModalButton>
            <ModalButton
              type="submit"
              disabled={createLoading}
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

export default RouteTablesPage;
