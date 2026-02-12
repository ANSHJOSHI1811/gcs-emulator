import React, { useEffect, useState } from 'react';
import { useProject } from '../contexts/ProjectContext';
import { useNavigate } from 'react-router-dom';
import { Plus, Trash2, RefreshCw, AlertCircle, Share2, ChevronDown, ChevronRight, Route } from 'lucide-react';
import { apiClient } from '../api/client';
import { Modal, ModalFooter, ModalButton } from '../components/Modal';
import { FormField, Input, Select } from '../components/FormFields';

interface VPCPeering {
  id: string;
  name: string;
  network: string;  // Local network URL
  state: string;
  stateDetails?: string;
  peeredNetwork: string;
  autoCreateRoutes: boolean;
  exportCustomRoutes: boolean;
  importCustomRoutes: boolean;
  creationTimestamp?: string;
  routes?: PeeringRoute[];
}

interface PeeringRoute {
  name: string;
  destRange: string;
  nextHopNetwork: string;
  priority: number;
}

interface NetworkOption {
  id: string;
  name: string;
  selfLink: string;
  cidrRange?: string;
}

interface ProjectOption {
  id: string;
  name: string;
}

const VPCPeeringPage = () => {
  const { currentProject } = useProject();
  const navigate = useNavigate();
  const [peerings, setPeerings] = useState<VPCPeering[]>([]);
  const [networks, setNetworks] = useState<NetworkOption[]>([]);
  const [allNetworks, setAllNetworks] = useState<NetworkOption[]>([]);
  const [loading, setLoading] = useState(true);
  const [showCreateModal, setShowCreateModal] = useState(false);
  const [expandedPeering, setExpandedPeering] = useState<string | null>(null);
  const [expandedPeeringDetails, setExpandedPeeringDetails] = useState<VPCPeering | null>(null);
  const [loadingExpanded, setLoadingExpanded] = useState(false);
  const [createLoading, setCreateLoading] = useState(false);
  const [deleteLoading, setDeleteLoading] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [formData, setFormData] = useState({
    localNetwork: '',
    targetNetwork: '',
    peeringName: '',
    autoCreateRoutes: true,
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
      const networksList = networksRes?.data?.items || [];
      setNetworks(networksList);
      setAllNetworks(networksList);

      // Load all peerings for all networks (in multi-tenant scenario, peerings could be in any network)
      const allPeerings: VPCPeering[] = [];
      for (const net of networksList) {
        try {
          const peeringsRes = await apiClient.get(
            `/compute/v1/projects/${currentProject}/global/networks/${net.name}/peerings`
          );
          const items = peeringsRes?.data?.items || [];
          allPeerings.push(...items);
        } catch (e) {
          // Network might not have peerings
        }
      }
      setPeerings(allPeerings);
    } catch (error: any) {
      console.error('Failed to load peerings:', error);
      setError('Failed to load VPC peerings. Please try again.');
    } finally {
      setLoading(false);
    }
  };

  const loadPeeringDetails = async (localNetwork: string, peeringName: string) => {
    try {
      setLoadingExpanded(true);
      const res = await apiClient.get(
        `/compute/v1/projects/${currentProject}/global/networks/${localNetwork}/peerings/${peeringName}`
      );
      setExpandedPeeringDetails(res?.data || null);
    } catch (error: any) {
      console.error('Failed to load peering details:', error);
      setError('Failed to load peering details. Please try again.');
    } finally {
      setLoadingExpanded(false);
    }
  };

  const handleExpandPeering = async (peeringId: string, localNetwork: string, peeringName: string) => {
    if (expandedPeering === peeringId) {
      setExpandedPeering(null);
      setExpandedPeeringDetails(null);
    } else {
      setExpandedPeering(peeringId);
      await loadPeeringDetails(localNetwork, peeringName);
    }
  };

  const extractNetworkName = (url: string) => {
    const match = url.match(/\/networks\/(.+?)(?:\/|$)/);
    return match ? match[1] : url;
  };

  const handleCreate = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!formData.localNetwork || !formData.targetNetwork) {
      setError('Please select both local and target networks');
      return;
    }

    setCreateLoading(true);
    setError(null);

    try {
      const peeringName = formData.peeringName || `${formData.localNetwork}-${formData.targetNetwork}`;
      
      const peeringBody = {
        name: peeringName,
        targetNetwork: formData.targetNetwork,
        autoCreateRoutes: formData.autoCreateRoutes,
      };

      await apiClient.post(
        `/compute/v1/projects/${currentProject}/global/networks/${formData.localNetwork}/peerings`,
        peeringBody
      );

      // Reset form and reload
      setFormData({
        localNetwork: '',
        targetNetwork: '',
        peeringName: '',
        autoCreateRoutes: true,
      });
      setShowCreateModal(false);
      await loadData();
    } catch (error: any) {
      console.error('Failed to create peering:', error);
      setError(error.response?.data?.detail || 'Failed to create peering. Please try again.');
    } finally {
      setCreateLoading(false);
    }
  };

  const handleDelete = async (localNetwork: string, peeringName: string) => {
    if (!confirm(`Are you sure you want to delete peering "${peeringName}"?`)) return;

    setDeleteLoading(peeringName);
    setError(null);

    try {
      await apiClient.delete(
        `/compute/v1/projects/${currentProject}/global/networks/${localNetwork}/peerings/${peeringName}`
      );
      await loadData();
    } catch (error: any) {
      console.error('Failed to delete peering:', error);
      setError(error.response?.data?.detail || 'Failed to delete peering. Please try again.');
    } finally {
      setDeleteLoading(null);
    }
  };

  const getState = (peering: VPCPeering) => {
    switch (peering.state) {
      case 'ACTIVE':
        return <span className="inline-block px-2 py-0.5 text-xs font-medium bg-green-100 text-green-700 rounded">Active</span>;
      case 'INACTIVE':
        return <span className="inline-block px-2 py-0.5 text-xs font-medium bg-gray-100 text-gray-700 rounded">Inactive</span>;
      case 'DELETING':
        return <span className="inline-block px-2 py-0.5 text-xs font-medium bg-red-100 text-red-700 rounded">Deleting</span>;
      default:
        return <span className="inline-block px-2 py-0.5 text-xs font-medium bg-gray-100 text-gray-700 rounded">{peering.state}</span>;
    }
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="text-center">
          <div className="inline-block animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600 mb-4"></div>
          <p className="text-gray-600">Loading VPC peerings...</p>
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
              <Share2 className="w-6 h-6 text-blue-600" />
            </div>
            <div>
              <h1 className="text-2xl font-bold text-gray-900">VPC Peering</h1>
              <p className="text-sm text-gray-600 mt-1">Manage VPC peering connections between networks</p>
            </div>
          </div>
          <div className="flex items-center gap-3">
            <button
              onClick={() => navigate('/services/vpc/routes')}
              className="flex items-center gap-2 px-4 py-2 bg-gray-100 text-gray-700 rounded-lg hover:bg-gray-200 transition-colors"
              title="View all routes managed by peerings"
            >
              <Route className="w-4 h-4" />
              View Routes
            </button>
            <button
              onClick={() => setShowCreateModal(true)}
              className="flex items-center gap-2 px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors"
            >
              <Plus className="w-4 h-4" />
              Create Peering
            </button>
          </div>
        </div>
      </div>

      {/* Error Message */}
      {error && (
        <div className="bg-red-50 border border-red-200 text-red-700 px-6 py-4 rounded-lg m-6 flex items-start gap-3">
          <AlertCircle className="w-5 h-5 flex-shrink-0 mt-0.5" />
          <p>{error}</p>
        </div>
      )}

      {/* Peerings List */}
      <div className="p-6">
        {peerings.length === 0 ? (
          <div className="text-center py-12 bg-gray-50 rounded-lg border-2 border-dashed border-gray-300">
            <Share2 className="w-12 h-12 text-gray-400 mx-auto mb-3" />
            <h3 className="text-lg font-medium text-gray-900 mb-1">No peerings</h3>
            <p className="text-gray-600 mb-4">Create a peering to connect VPC networks</p>
            <button
              onClick={() => setShowCreateModal(true)}
              className="inline-flex items-center gap-2 px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors"
            >
              <Plus className="w-4 h-4" />
              Create Peering
            </button>
          </div>
        ) : (
          <div className="overflow-x-auto border border-gray-200 rounded-lg">
            <table className="w-full">
              <thead>
                <tr className="bg-gray-50 border-b border-gray-200">
                  <th className="px-6 py-3 text-left text-xs font-semibold text-gray-700 w-8"></th>
                  <th className="px-6 py-3 text-left text-xs font-semibold text-gray-700">Peering Name</th>
                  <th className="px-6 py-3 text-left text-xs font-semibold text-gray-700">Local Network</th>
                  <th className="px-6 py-3 text-left text-xs font-semibold text-gray-700">Peered Network</th>
                  <th className="px-6 py-3 text-center text-xs font-semibold text-gray-700">Status</th>
                  <th className="px-6 py-3 text-left text-xs font-semibold text-gray-700">Routes</th>
                  <th className="px-6 py-3 text-left text-xs font-semibold text-gray-700">Created</th>
                  <th className="px-6 py-3 text-right text-xs font-semibold text-gray-700">Actions</th>
                </tr>
              </thead>
              <tbody>
                {peerings.map((peering) => (
                  <React.Fragment key={peering.id}>
                    {/* Peering Row */}
                    <tr className="border-b border-gray-200 hover:bg-gray-50 transition-colors">
                      <td className="px-6 py-4 w-8">
                        <button
                          onClick={() =>
                            handleExpandPeering(
                              peering.id,
                              extractNetworkName(peering.network),
                              peering.name
                            )
                          }
                          className="text-gray-400 hover:text-gray-600 transition-colors"
                        >
                          {expandedPeering === peering.id ? (
                            <ChevronDown className="w-4 h-4" />
                          ) : (
                            <ChevronRight className="w-4 h-4" />
                          )}
                        </button>
                      </td>
                      <td className="px-6 py-4">
                        <div className="font-medium text-gray-900">{peering.name}</div>
                      </td>
                      <td className="px-6 py-4 text-sm text-gray-600">
                        {extractNetworkName(peering.network)}
                      </td>
                      <td className="px-6 py-4 text-sm text-gray-600">
                        {extractNetworkName(peering.peeredNetwork)}
                      </td>
                      <td className="px-6 py-4 text-center">
                        {getState(peering)}
                      </td>
                      <td className="px-6 py-4 text-sm text-gray-600">
                        {peering.autoCreateRoutes ? '✓ Auto' : 'Manual'}
                      </td>
                      <td className="px-6 py-4 text-sm text-gray-600">
                        {peering.creationTimestamp ? new Date(peering.creationTimestamp).toLocaleDateString() : 'Unknown'}
                      </td>
                      <td className="px-6 py-4 text-right">
                        <button
                          onClick={() =>
                            handleDelete(
                              extractNetworkName(peering.network),
                              peering.name
                            )
                          }
                          disabled={deleteLoading === peering.name}
                          className="inline-flex items-center gap-1 px-3 py-1.5 text-sm font-medium text-red-600 hover:bg-red-50 rounded transition-colors disabled:opacity-50"
                          title="Delete peering"
                        >
                          <Trash2 className="w-4 h-4" />
                        </button>
                      </td>
                    </tr>

                    {/* Expanded Peering Details */}
                    {expandedPeering === peering.id && (
                      <tr className="bg-gray-50 border-b border-gray-200">
                        <td colSpan={8} className="px-6 py-4">
                          {loadingExpanded ? (
                            <div className="flex items-center justify-center py-8">
                              <div className="inline-block animate-spin rounded-full h-6 w-6 border-b-2 border-blue-600 mr-3"></div>
                              <span className="text-gray-600">Loading peering details...</span>
                            </div>
                          ) : expandedPeeringDetails ? (
                            <div className="space-y-6">
                              {/* Network Information */}
                              <div className="grid grid-cols-2 gap-6">
                                <div>
                                  <label className="text-xs font-semibold text-gray-600 uppercase tracking-wide">Local Network</label>
                                  <div className="mt-2 space-y-1">
                                    <p className="text-sm font-medium text-gray-900">{extractNetworkName(expandedPeeringDetails.network)}</p>
                                    {expandedPeeringDetails.routes?.[0]?.destRange && (
                                      <p className="text-sm text-gray-600 font-mono bg-gray-100 px-2 py-1 rounded">
                                        {expandedPeeringDetails.routes[0].destRange}
                                      </p>
                                    )}
                                  </div>
                                </div>
                                <div>
                                  <label className="text-xs font-semibold text-gray-600 uppercase tracking-wide">Peered Network</label>
                                  <div className="mt-2 space-y-1">
                                    <p className="text-sm font-medium text-gray-900">{extractNetworkName(expandedPeeringDetails.peeredNetwork)}</p>
                                    {expandedPeeringDetails.routes?.[1]?.destRange && (
                                      <p className="text-sm text-gray-600 font-mono bg-gray-100 px-2 py-1 rounded">
                                        {expandedPeeringDetails.routes[1].destRange}
                                      </p>
                                    )}
                                  </div>
                                </div>
                              </div>

                              {/* Routes Table */}
                              {expandedPeeringDetails.routes && expandedPeeringDetails.routes.length > 0 ? (
                                <div>
                                  <label className="text-xs font-semibold text-gray-600 uppercase tracking-wide mb-3 block">
                                    Routes ({expandedPeeringDetails.routes.length})
                                  </label>
                                  <div className="overflow-x-auto border border-gray-300 rounded bg-white">
                                    <table className="w-full">
                                      <thead>
                                        <tr className="bg-gray-100 border-b border-gray-300">
                                          <th className="px-4 py-2 text-left text-xs font-semibold text-gray-700">Name</th>
                                          <th className="px-4 py-2 text-left text-xs font-semibold text-gray-700">Destination</th>
                                          <th className="px-4 py-2 text-left text-xs font-semibold text-gray-700">Next Hop Network</th>
                                          <th className="px-4 py-2 text-center text-xs font-semibold text-gray-700">Priority</th>
                                        </tr>
                                      </thead>
                                      <tbody>
                                        {expandedPeeringDetails.routes.map((route) => (
                                          <tr key={route.name} className="border-b border-gray-200 hover:bg-gray-50">
                                            <td className="px-4 py-2 text-sm font-medium text-gray-900">{route.name}</td>
                                            <td className="px-4 py-2 text-sm text-gray-600 font-mono">{route.destRange}</td>
                                            <td className="px-4 py-2 text-sm text-gray-600">{route.nextHopNetwork}</td>
                                            <td className="px-4 py-2 text-center text-sm">
                                              <span className="inline-block px-2 py-1 text-xs font-medium bg-amber-100 text-amber-800 rounded">
                                                {route.priority}
                                              </span>
                                            </td>
                                          </tr>
                                        ))}
                                      </tbody>
                                    </table>
                                  </div>
                                </div>
                              ) : (
                                <div className="p-3 bg-white border border-gray-300 rounded text-sm text-gray-600">
                                  No routes in this peering
                                </div>
                              )}

                              {/* Configuration Settings */}
                              <div className="bg-white border border-gray-300 rounded p-4 space-y-3">
                                <label className="text-xs font-semibold text-gray-600 uppercase tracking-wide block">Configuration</label>
                                <div className="space-y-2">
                                  <label className="flex items-center gap-2 text-sm text-gray-700">
                                    <input
                                      type="checkbox"
                                      checked={expandedPeeringDetails.autoCreateRoutes}
                                      disabled
                                      className="w-4 h-4 rounded"
                                    />
                                    Auto Create Routes
                                  </label>
                                  <label className="flex items-center gap-2 text-sm text-gray-700">
                                    <input
                                      type="checkbox"
                                      checked={expandedPeeringDetails.exportCustomRoutes}
                                      disabled
                                      className="w-4 h-4 rounded"
                                    />
                                    Export Custom Routes
                                  </label>
                                  <label className="flex items-center gap-2 text-sm text-gray-700">
                                    <input
                                      type="checkbox"
                                      checked={expandedPeeringDetails.importCustomRoutes}
                                      disabled
                                      className="w-4 h-4 rounded"
                                    />
                                    Import Custom Routes
                                  </label>
                                </div>
                              </div>
                            </div>
                          ) : (
                            <div className="p-3 bg-white border border-gray-300 rounded text-sm text-red-600">
                              Failed to load peering details
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

      {/* Create Peering Modal */}
      <Modal
        isOpen={showCreateModal}
        onClose={() => setShowCreateModal(false)}
        title="Create VPC Peering"
      >
        <form onSubmit={handleCreate} className="space-y-4">
          <FormField label="Local Network" required>
            <Select
              value={formData.localNetwork}
              onChange={(e) => setFormData({ ...formData, localNetwork: e.target.value })}
              required
            >
              <option value="">Select local network</option>
              {networks.map((net) => (
                <option key={net.id} value={net.name}>
                  {net.name}
                </option>
              ))}
            </Select>
          </FormField>

          <FormField label="Target Network" required>
            <Select
              value={formData.targetNetwork}
              onChange={(e) => setFormData({ ...formData, targetNetwork: e.target.value })}
              required
            >
              <option value="">Select target network</option>
              {networks
                .filter((net) => net.name !== formData.localNetwork)
                .map((net) => (
                  <option key={net.id} value={`projects/${currentProject}/global/networks/${net.name}`}>
                    {net.name}
                  </option>
                ))}
            </Select>
          </FormField>

          <FormField label="Peering Name (Optional)">
            <Input
              type="text"
              value={formData.peeringName}
              onChange={(e) => setFormData({ ...formData, peeringName: e.target.value })}
              placeholder={`${formData.localNetwork}-${formData.targetNetwork.split('/').pop() || 'network'}`}
            />
          </FormField>

          <FormField label="Configuration">
            <label className="flex items-center gap-2 text-sm text-gray-700">
              <input
                type="checkbox"
                checked={formData.autoCreateRoutes}
                onChange={(e) => setFormData({ ...formData, autoCreateRoutes: e.target.checked })}
                className="w-4 h-4 rounded border-gray-300"
              />
              Auto Create Routes
            </label>
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
              {createLoading ? 'Creating...' : 'Create Peering'}
            </ModalButton>
          </ModalFooter>
        </form>
      </Modal>
    </div>
  );
};

export default VPCPeeringPage;
