import { useEffect, useState } from 'react';
import { Route, Plus, Trash2, RefreshCw, AlertCircle, Navigation } from 'lucide-react';
import { apiClient } from '../api/client';

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
  const [routes, setRoutes] = useState<RouteRule[]>([]);
  const [networks, setNetworks] = useState<NetworkOption[]>([]);
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
    loadData();
  }, []);

  const loadData = async () => {
    try {
      setLoading(true);
      setError(null);

      // Load networks
      const networksRes = await apiClient.get('/compute/v1/projects/demo-project/global/networks');
      setNetworks(networksRes.data.items || []);

      // Load routes
      const routesRes = await apiClient.get('/compute/v1/projects/demo-project/global/routes');
      setRoutes(routesRes.data.items || []);
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
        network: formData.network,
        destRange: formData.destRange,
        priority: formData.priority,
      };

      if (formData.description) {
        routeData.description = formData.description;
      }

      // Set next hop based on type
      switch (formData.nextHopType) {
        case 'gateway':
          routeData.nextHopGateway = `projects/demo-project/global/gateways/${formData.nextHopValue}`;
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

      await apiClient.post('/compute/v1/projects/demo-project/global/routes', routeData);

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
      setError(error.response?.data?.error?.message || 'Failed to create route');
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
      await apiClient.delete(`/compute/v1/projects/demo-project/global/routes/${routeName}`);
      await loadData();
    } catch (error: any) {
      console.error('Failed to delete route:', error);
      setError(error.response?.data?.error?.message || 'Failed to delete route');
    } finally {
      setDeleteLoading(null);
    }
  };

  const extractNetworkName = (networkUrl: string): string => {
    if (!networkUrl) return '-';
    const parts = networkUrl.split('/');
    return parts[parts.length - 1] || networkUrl;
  };

  const getNextHop = (route: RouteRule): string => {
    if (route.nextHopGateway) {
      const parts = route.nextHopGateway.split('/');
      return `Gateway: ${parts[parts.length - 1]}`;
    }
    if (route.nextHopIp) return `IP: ${route.nextHopIp}`;
    if (route.nextHopInstance) return `Instance: ${extractNetworkName(route.nextHopInstance)}`;
    if (route.nextHopNetwork) return `Network: ${extractNetworkName(route.nextHopNetwork)}`;
    return '-';
  };

  return (
    <div className="h-full flex flex-col bg-gray-50">
      {/* Header */}
      <div className="bg-white border-b border-gray-200 px-8 py-6">
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-2xl font-semibold text-gray-900">Routes</h1>
            <p className="text-sm text-gray-500 mt-1">
              Define custom routing paths for your VPC networks
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
              Create Route
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
            <div className="text-gray-500">Loading routes...</div>
          </div>
        ) : routes.length === 0 ? (
          <div className="flex flex-col items-center justify-center h-64 bg-white rounded-lg border border-gray-200">
            <Navigation className="w-12 h-12 text-gray-400 mb-4" />
            <h3 className="text-lg font-medium text-gray-900 mb-2">No routes found</h3>
            <p className="text-sm text-gray-500 mb-4">Create your first custom route</p>
            <button
              onClick={() => setShowCreateModal(true)}
              className="flex items-center gap-2 px-4 py-2 text-sm font-medium text-white bg-blue-600 rounded-lg hover:bg-blue-700"
            >
              <Plus className="w-4 h-4" />
              Create Route
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
                    Destination Range
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Next Hop
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Priority
                  </th>
                  <th className="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Actions
                  </th>
                </tr>
              </thead>
              <tbody className="bg-white divide-y divide-gray-200">
                {routes.map((route) => (
                  <tr key={route.id} className="hover:bg-gray-50">
                    <td className="px-6 py-4 whitespace-nowrap">
                      <div className="flex items-center">
                        <Navigation className="w-5 h-5 text-purple-600 mr-3" />
                        <div>
                          <div className="text-sm font-medium text-gray-900">{route.name}</div>
                          {route.description && (
                            <div className="text-xs text-gray-500">{route.description}</div>
                          )}
                        </div>
                      </div>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap">
                      <div className="text-sm text-gray-900">{extractNetworkName(route.network)}</div>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap">
                      <div className="text-sm font-mono text-gray-900">{route.destRange}</div>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap">
                      <div className="text-sm text-gray-900">{getNextHop(route)}</div>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap">
                      <div className="text-sm text-gray-900">{route.priority}</div>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-right text-sm font-medium">
                      <button
                        onClick={() => handleDelete(route.name)}
                        disabled={deleteLoading === route.name}
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
      {showCreateModal && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
          <div className="bg-white rounded-lg shadow-xl max-w-2xl w-full max-h-[90vh] overflow-y-auto">
            <div className="px-6 py-4 border-b border-gray-200">
              <h2 className="text-lg font-semibold text-gray-900">Create Route</h2>
            </div>
            <form onSubmit={handleCreate} className="p-6 space-y-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Name *
                </label>
                <input
                  type="text"
                  value={formData.name}
                  onChange={(e) => setFormData({ ...formData, name: e.target.value })}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                  placeholder="my-route"
                  pattern="[a-z]([-a-z0-9]*[a-z0-9])?"
                  required
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Description
                </label>
                <input
                  type="text"
                  value={formData.description}
                  onChange={(e) => setFormData({ ...formData, description: e.target.value })}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                  placeholder="Optional description"
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Network *
                </label>
                <select
                  value={formData.network}
                  onChange={(e) => setFormData({ ...formData, network: e.target.value })}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                  required
                >
                  <option value="">Select a network</option>
                  {networks.map((network) => (
                    <option key={network.name} value={network.selfLink}>
                      {network.name}
                    </option>
                  ))}
                </select>
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Destination IP Range *
                </label>
                <input
                  type="text"
                  value={formData.destRange}
                  onChange={(e) => setFormData({ ...formData, destRange: e.target.value })}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500 font-mono"
                  placeholder="0.0.0.0/0"
                  required
                />
                <p className="mt-1 text-xs text-gray-500">
                  CIDR notation (e.g., 0.0.0.0/0 for internet, 10.0.0.0/8 for private)
                </p>
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Priority *
                </label>
                <input
                  type="number"
                  value={formData.priority}
                  onChange={(e) => setFormData({ ...formData, priority: parseInt(e.target.value) })}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                  min="0"
                  max="65535"
                  required
                />
                <p className="mt-1 text-xs text-gray-500">
                  0-65535 (lower = higher priority)
                </p>
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Next Hop Type *
                </label>
                <select
                  value={formData.nextHopType}
                  onChange={(e) => {
                    const type = e.target.value;
                    setFormData({
                      ...formData,
                      nextHopType: type,
                      nextHopValue: type === 'gateway' ? 'default-internet-gateway' : '',
                    });
                  }}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                >
                  <option value="gateway">Gateway</option>
                  <option value="ip">IP Address</option>
                  <option value="instance">Instance</option>
                  <option value="network">Network</option>
                </select>
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Next Hop Value *
                </label>
                {formData.nextHopType === 'gateway' ? (
                  <select
                    value={formData.nextHopValue}
                    onChange={(e) => setFormData({ ...formData, nextHopValue: e.target.value })}
                    className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                    required
                  >
                    <option value="default-internet-gateway">Default Internet Gateway</option>
                  </select>
                ) : (
                  <input
                    type="text"
                    value={formData.nextHopValue}
                    onChange={(e) => setFormData({ ...formData, nextHopValue: e.target.value })}
                    className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                    placeholder={
                      formData.nextHopType === 'ip'
                        ? '192.168.1.1'
                        : formData.nextHopType === 'instance'
                        ? 'instance-name or full URL'
                        : 'network-name or full URL'
                    }
                    required
                  />
                )}
                <p className="mt-1 text-xs text-gray-500">
                  {formData.nextHopType === 'gateway' && 'The default gateway for internet access'}
                  {formData.nextHopType === 'ip' && 'IP address of the next hop'}
                  {formData.nextHopType === 'instance' && 'Instance name or full resource URL'}
                  {formData.nextHopType === 'network' && 'Network name or full resource URL'}
                </p>
              </div>

              <div className="flex justify-end gap-3 pt-4 border-t">
                <button
                  type="button"
                  onClick={() => setShowCreateModal(false)}
                  disabled={createLoading}
                  className="px-4 py-2 text-sm font-medium text-gray-700 bg-white border border-gray-300 rounded-lg hover:bg-gray-50 disabled:opacity-50"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  disabled={createLoading || networks.length === 0}
                  className="px-4 py-2 text-sm font-medium text-white bg-blue-600 rounded-lg hover:bg-blue-700 disabled:opacity-50"
                >
                  {createLoading ? 'Creating...' : 'Create'}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
};

export default RoutesPage;
