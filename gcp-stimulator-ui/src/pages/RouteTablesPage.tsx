import React, { useEffect, useState } from 'react';
import { useProject } from '../contexts/ProjectContext';
import { Plus, Trash2, RefreshCw, AlertCircle, Network, Route, ChevronDown, ChevronRight } from 'lucide-react';
import { apiClient } from '../api/client';
import { Modal, ModalFooter, ModalButton } from '../components/Modal';
import { FormField, Input, Select } from '../components/FormFields';

interface RouteTable {
  id: string;
  name: string;
  network: string;
  description?: string;
  isDefault: boolean;
  routeCount: number;
  subnetCount: number;
  creationTimestamp?: string;
  routes?: RouteRule[];
  associations?: SubnetAssociation[];
}

interface RouteRule {
  kind: string;
  name: string;
  destRange: string;
  priority: number;
  nextHopGateway?: string;
  nextHopIp?: string;
  nextHopInstance?: string;
  nextHopNetwork?: string;
  description?: string;
}

interface SubnetAssociation {
  id: string;
  subnetName: string;
  creationTimestamp?: string;
}

interface NetworkOption {
  name: string;
  selfLink: string;
}

const RouteTablesPage = () => {
  const { currentProject } = useProject();
  const [routeTables, setRouteTables] = useState<RouteTable[]>([]);
  const [networks, setNetworks] = useState<NetworkOption[]>([]);
  const [loading, setLoading] = useState(true);
  const [showCreateModal, setShowCreateModal] = useState(false);
  const [showAddRouteModal, setShowAddRouteModal] = useState(false);
  const [selectedTable, setSelectedTable] = useState<string | null>(null);
  const [expandedTable, setExpandedTable] = useState<string | null>(null);
  const [expandedTableDetails, setExpandedTableDetails] = useState<RouteTable | null>(null);
  const [loadingExpanded, setLoadingExpanded] = useState(false);
  const [createLoading, setCreateLoading] = useState(false);
  const [deleteLoading, setDeleteLoading] = useState<string | null>(null);
  const [addRouteLoading, setAddRouteLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [formData, setFormData] = useState({
    name: '',
    network: '',
    description: '',
  });
  const [routeFormData, setRouteFormData] = useState({
    destRange: '',
    priority: '1000',
    nextHopType: 'gateway',
    nextHopValue: 'default-internet-gateway',
    description: '',
  });

  useEffect(() => {
    loadData();
  }, [currentProject]);

  const loadData = async () => {
    try {
      setLoading(true);
      setError(null);

      // Load networks
      const networksRes = await apiClient.get(`/compute/v1/projects/${currentProject}/global/networks`);
      setNetworks(networksRes?.data?.items || []);

      // Load route tables
      const tablesRes = await apiClient.get(`/compute/v1/projects/${currentProject}/global/routeTables`);
      setRouteTables(tablesRes?.data?.items || []);
    } catch (error: any) {
      console.error('Failed to load route tables:', error);
      setError('Failed to load route tables. Please try again.');
    } finally {
      setLoading(false);
    }
  };

  const loadTableDetails = async (tableName: string) => {
    try {
      setLoadingExpanded(true);
      const res = await apiClient.get(`/compute/v1/projects/${currentProject}/global/routeTables/${tableName}`);
      setExpandedTableDetails(res?.data || null);
    } catch (error: any) {
      console.error('Failed to load table details:', error);
      setError('Failed to load routes. Please try again.');
    } finally {
      setLoadingExpanded(false);
    }
  };

  const handleExpandTable = async (tableId: string, tableName: string) => {
    if (expandedTable === tableId) {
      setExpandedTable(null);
      setExpandedTableDetails(null);
    } else {
      setExpandedTable(tableId);
      await loadTableDetails(tableName);
    }
  };

  const handleCreate = async (e: React.FormEvent) => {
    e.preventDefault();
    setCreateLoading(true);
    setError(null);

    try {
      const tableData: any = {
        name: formData.name,
        network: formData.network,
      };

      if (formData.description) {
        tableData.description = formData.description;
      }

      await apiClient.post(`/compute/v1/projects/${currentProject}/global/routeTables`, tableData);
      
      // Reset form and reload
      setFormData({ name: '', network: '', description: '' });
      setShowCreateModal(false);
      await loadData();
    } catch (error: any) {
      console.error('Failed to create route table:', error);
      setError(error.response?.data?.detail || 'Failed to create route table. Please try again.');
    } finally {
      setCreateLoading(false);
    }
  };

  const handleAddRoute = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!selectedTable) return;

    setAddRouteLoading(true);
    setError(null);

    try {
      const routeData: any = {
        destRange: routeFormData.destRange,
        priority: parseInt(routeFormData.priority),
      };

      if (routeFormData.description) {
        routeData.description = routeFormData.description;
      }

      // Set next hop based on type
      switch (routeFormData.nextHopType) {
        case 'gateway':
          routeData.nextHopGateway = routeFormData.nextHopValue;
          break;
        case 'ip':
          routeData.nextHopIp = routeFormData.nextHopValue;
          break;
        case 'instance':
          routeData.nextHopInstance = routeFormData.nextHopValue;
          break;
        case 'network':
          routeData.nextHopNetwork = routeFormData.nextHopValue;
          break;
      }

      await apiClient.post(
        `/compute/v1/projects/${currentProject}/global/routeTables/${selectedTable}/addRoute`,
        routeData
      );

      // Reset form and reload
      setRouteFormData({
        destRange: '',
        priority: '1000',
        nextHopType: 'gateway',
        nextHopValue: 'default-internet-gateway',
        description: '',
      });
      setShowAddRouteModal(false);
      await loadData();
    } catch (error: any) {
      console.error('Failed to add route:', error);
      setError(error.response?.data?.detail || 'Failed to add route. Please try again.');
    } finally {
      setAddRouteLoading(false);
    }
  };

  const handleDelete = async (tableName: string) => {
    if (!confirm(`Are you sure you want to delete route table "${tableName}"?`)) return;

    setDeleteLoading(tableName);
    setError(null);

    try {
      await apiClient.delete(`/compute/v1/projects/${currentProject}/global/routeTables/${tableName}`);
      await loadData();
    } catch (error: any) {
      console.error('Failed to delete route table:', error);
      setError(error.response?.data?.detail || 'Failed to delete route table. Please try again.');
    } finally {
      setDeleteLoading(null);
    }
  };

  const getNetworkName = (network: string) => {
    const match = network.match(/\/networks\/(.+?)(?:\/|$)/);
    return match ? match[1] : network;
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="text-center">
          <div className="inline-block animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600 mb-4"></div>
          <p className="text-gray-600">Loading route tables...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="max-w-7xl mx-auto">
      {/* Header */}
      <div className="bg-white border-b border-gray-200 p-6">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="p-2 bg-blue-100 rounded-lg">
              <Route className="w-6 h-6 text-blue-600" />
            </div>
            <div>
              <h1 className="text-2xl font-bold text-gray-900">Route Tables</h1>
              <p className="text-sm text-gray-600 mt-1">Manage route tables and their routes</p>
            </div>
          </div>
          <button
            onClick={() => setShowCreateModal(true)}
            className="flex items-center gap-2 px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors"
          >
            <Plus className="w-4 h-4" />
            Create Route Table
          </button>
        </div>
      </div>

      {/* Error Message */}
      {error && (
        <div className="bg-red-50 border border-red-200 text-red-700 px-6 py-4 rounded-lg m-6 flex items-start gap-3">
          <AlertCircle className="w-5 h-5 flex-shrink-0 mt-0.5" />
          <p>{error}</p>
        </div>
      )}

      {/* Route Tables List */}
      <div className="p-6">
        {routeTables.length === 0 ? (
          <div className="text-center py-12 bg-gray-50 rounded-lg border-2 border-dashed border-gray-300">
            <Network className="w-12 h-12 text-gray-400 mx-auto mb-3" />
            <h3 className="text-lg font-medium text-gray-900 mb-1">No route tables</h3>
            <p className="text-gray-600 mb-4">Create a route table to manage your VPC routes</p>
            <button
              onClick={() => setShowCreateModal(true)}
              className="inline-flex items-center gap-2 px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors"
            >
              <Plus className="w-4 h-4" />
              Create Route Table
            </button>
          </div>
        ) : (
          <div className="overflow-x-auto border border-gray-200 rounded-lg">
            <table className="w-full">
              <thead>
                <tr className="bg-gray-50 border-b border-gray-200">
                  <th className="px-6 py-3 text-left text-xs font-semibold text-gray-700 w-8"></th>
                  <th className="px-6 py-3 text-left text-xs font-semibold text-gray-700">Name</th>
                  <th className="px-6 py-3 text-left text-xs font-semibold text-gray-700">Network</th>
                  <th className="px-6 py-3 text-center text-xs font-semibold text-gray-700">Routes</th>
                  <th className="px-6 py-3 text-center text-xs font-semibold text-gray-700">Subnets</th>
                  <th className="px-6 py-3 text-left text-xs font-semibold text-gray-700">Created</th>
                  <th className="px-6 py-3 text-right text-xs font-semibold text-gray-700">Actions</th>
                </tr>
              </thead>
              <tbody>
                {routeTables.map((table) => (
                  <React.Fragment key={table.id}>
                    {/* Table Row */}
                    <tr className="border-b border-gray-200 hover:bg-gray-50 transition-colors">
                      <td className="px-6 py-4 w-8">
                        <button
                          onClick={() => handleExpandTable(table.id, table.name)}
                          className="text-gray-400 hover:text-gray-600 transition-colors"
                        >
                          {expandedTable === table.id ? (
                            <ChevronDown className="w-4 h-4" />
                          ) : (
                            <ChevronRight className="w-4 h-4" />
                          )}
                        </button>
                      </td>
                      <td className="px-6 py-4">
                        <div className="flex items-center gap-2">
                          <div className="font-medium text-gray-900">{table.name}</div>
                          {table.isDefault && (
                            <span className="inline-block px-2 py-0.5 text-xs font-medium bg-blue-100 text-blue-700 rounded">Default</span>
                          )}
                        </div>
                      </td>
                      <td className="px-6 py-4 text-sm text-gray-600">
                        {getNetworkName(table.network)}
                      </td>
                      <td className="px-6 py-4 text-center text-sm font-medium text-gray-900">
                        {table.routeCount}
                      </td>
                      <td className="px-6 py-4 text-center text-sm text-gray-600">
                        {table.subnetCount}
                      </td>
                      <td className="px-6 py-4 text-sm text-gray-600">
                        {table.creationTimestamp ? new Date(table.creationTimestamp).toLocaleDateString() : 'Unknown'}
                      </td>
                      <td className="px-6 py-4 text-right">
                        <div className="flex items-center justify-end gap-2">
                          <button
                            onClick={() => {
                              setSelectedTable(table.name);
                              setShowAddRouteModal(true);
                            }}
                            className="inline-flex items-center gap-1 px-3 py-1.5 text-sm font-medium text-blue-600 hover:bg-blue-50 rounded transition-colors"
                            title="Add route"
                          >
                            <Plus className="w-4 h-4" />
                          </button>
                          {!table.isDefault && (
                            <button
                              onClick={() => handleDelete(table.name)}
                              disabled={deleteLoading === table.name}
                              className="inline-flex items-center gap-1 px-3 py-1.5 text-sm font-medium text-red-600 hover:bg-red-50 rounded transition-colors disabled:opacity-50"
                              title="Delete"
                            >
                              <Trash2 className="w-4 h-4" />
                            </button>
                          )}
                        </div>
                      </td>
                    </tr>

                    {/* Expanded Routes Table */}
                    {expandedTable === table.id && (
                      <tr className="bg-gray-50 border-b border-gray-200">
                        <td colSpan={7} className="px-6 py-4">
                          {loadingExpanded ? (
                            <div className="flex items-center justify-center py-8">
                              <div className="inline-block animate-spin rounded-full h-6 w-6 border-b-2 border-blue-600 mr-3"></div>
                              <span className="text-gray-600">Loading routes...</span>
                            </div>
                          ) : expandedTableDetails ? (
                            <div className="space-y-4">
                              {/* Table Description */}
                              {expandedTableDetails.description && (
                                <div>
                                  <label className="text-xs font-semibold text-gray-600 uppercase tracking-wide">Description</label>
                                  <p className="text-sm text-gray-900 mt-1">{expandedTableDetails.description}</p>
                                </div>
                              )}

                              {/* Routes Table */}
                              {expandedTableDetails.routes && expandedTableDetails.routes.length > 0 ? (
                                <div>
                                  <label className="text-xs font-semibold text-gray-600 uppercase tracking-wide mb-3 block">Routes ({expandedTableDetails.routes.length})</label>
                                  <div className="overflow-x-auto border border-gray-300 rounded bg-white">
                                    <table className="w-full">
                                      <thead>
                                        <tr className="bg-gray-100 border-b border-gray-300">
                                          <th className="px-4 py-2 text-left text-xs font-semibold text-gray-700">Name</th>
                                          <th className="px-4 py-2 text-left text-xs font-semibold text-gray-700">Destination</th>
                                          <th className="px-4 py-2 text-center text-xs font-semibold text-gray-700">Priority</th>
                                          <th className="px-4 py-2 text-left text-xs font-semibold text-gray-700">Next Hop Type</th>
                                          <th className="px-4 py-2 text-left text-xs font-semibold text-gray-700">Next Hop</th>
                                        </tr>
                                      </thead>
                                      <tbody>
                                        {expandedTableDetails.routes.map((route) => (
                                          <tr key={route.name} className="border-b border-gray-200 hover:bg-gray-50">
                                            <td className="px-4 py-2 text-sm font-medium text-gray-900">
                                              {route.name}
                                            </td>
                                            <td className="px-4 py-2 text-sm text-gray-600 font-mono">
                                              {route.destRange}
                                            </td>
                                            <td className="px-4 py-2 text-center text-sm">
                                              <span className="inline-block px-2 py-1 text-xs font-medium bg-amber-100 text-amber-800 rounded">
                                                {route.priority}
                                              </span>
                                            </td>
                                            <td className="px-4 py-2 text-sm text-gray-600">
                                              {route.nextHopGateway ? 'Gateway' : route.nextHopIp ? 'IP' : route.nextHopInstance ? 'Instance' : route.nextHopNetwork ? 'Network' : 'Unknown'}
                                            </td>
                                            <td className="px-4 py-2 text-sm text-gray-600 font-mono">
                                              {route.nextHopGateway || route.nextHopIp || route.nextHopInstance || route.nextHopNetwork || '-'}
                                            </td>
                                          </tr>
                                        ))}
                                      </tbody>
                                    </table>
                                  </div>
                                </div>
                              ) : (
                                <div className="p-3 bg-white border border-gray-300 rounded text-sm text-gray-600">
                                  No routes in this table
                                </div>
                              )}
                            </div>
                          ) : (
                            <div className="p-3 bg-white border border-gray-300 rounded text-sm text-red-600">
                              Failed to load routes
                            </div>
                          )}
                        </td>
                      </tr>
                    )}
                  </React.Fragment>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>

      {/* Create Route Table Modal */}
      <Modal
        isOpen={showCreateModal}
        onClose={() => setShowCreateModal(false)}
        title="Create Route Table"
      >
        <form onSubmit={handleCreate} className="space-y-4">
          <FormField label="Name" required>
            <Input
              type="text"
              value={formData.name}
              onChange={(e) => setFormData({ ...formData, name: e.target.value })}
              placeholder="prod-routes"
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
              {networks.map((net) => (
                <option key={net.name} value={net.name}>
                  {net.name}
                </option>
              ))}
            </Select>
          </FormField>

          <FormField label="Description (Optional)">
            <Input
              type="text"
              value={formData.description}
              onChange={(e) => setFormData({ ...formData, description: e.target.value })}
              placeholder="Production route table"
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
              {createLoading ? 'Creating...' : 'Create Route Table'}
            </ModalButton>
          </ModalFooter>
        </form>
      </Modal>

      {/* Add Route Modal */}
      <Modal
        isOpen={showAddRouteModal}
        onClose={() => setShowAddRouteModal(false)}
        title={`Add Route to ${selectedTable}`}
      >
        <form onSubmit={handleAddRoute} className="space-y-4">
          <FormField label="Destination Range" required>
            <Input
              type="text"
              value={routeFormData.destRange}
              onChange={(e) => setRouteFormData({ ...routeFormData, destRange: e.target.value })}
              placeholder="192.168.0.0/24"
              required
            />
          </FormField>

          <FormField label="Priority" required>
            <Input
              type="number"
              value={routeFormData.priority}
              onChange={(e) => setRouteFormData({ ...routeFormData, priority: e.target.value })}
              min="0"
              max="65535"
              required
            />
          </FormField>

          <FormField label="Next Hop Type" required>
            <Select
              value={routeFormData.nextHopType}
              onChange={(e) => setRouteFormData({ ...routeFormData, nextHopType: e.target.value })}
            >
              <option value="gateway">Gateway</option>
              <option value="ip">IP Address</option>
              <option value="instance">Instance</option>
              <option value="network">Network</option>
            </Select>
          </FormField>

          <FormField label="Next Hop Value" required>
            <Input
              type="text"
              value={routeFormData.nextHopValue}
              onChange={(e) => setRouteFormData({ ...routeFormData, nextHopValue: e.target.value })}
              placeholder={
                routeFormData.nextHopType === 'gateway'
                  ? 'default-internet-gateway'
                  : 'Value'
              }
              required
            />
          </FormField>

          <FormField label="Description (Optional)">
            <Input
              type="text"
              value={routeFormData.description}
              onChange={(e) => setRouteFormData({ ...routeFormData, description: e.target.value })}
              placeholder="Route to office network"
            />
          </FormField>

          <ModalFooter>
            <ModalButton
              onClick={() => setShowAddRouteModal(false)}
              variant="secondary"
            >
              Cancel
            </ModalButton>
            <ModalButton
              type="submit"
              disabled={addRouteLoading}
            >
              {addRouteLoading ? 'Adding...' : 'Add Route'}
            </ModalButton>
          </ModalFooter>
        </form>
      </Modal>
    </div>
  );
};

export default RouteTablesPage;
