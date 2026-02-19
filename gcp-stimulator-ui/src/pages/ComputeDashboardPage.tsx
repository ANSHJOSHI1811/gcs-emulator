import { useEffect, useState } from 'react';
import { Cpu, Server, Plus, StopCircle, Play, Trash2, Activity, ArrowRight, Network, HardDrive, Container, MapPin, Globe, Tag, Terminal, RefreshCw, X, ExternalLink } from 'lucide-react';
import { useNavigate } from 'react-router-dom';
import { apiClient } from '../api/client';
import { useProject } from '../contexts/ProjectContext';

interface Instance {
  id: string;
  name: string;
  zone: string;
  machineType: string;
  status: string;
  description?: string;
  tags?: string[];
  labels?: Record<string, string>;
  metadata_items?: Array<{ key: string; value: string }>;
  networkInterfaces?: Array<{
    network?: string;
    subnetwork?: string;
    networkIP: string;
    accessConfigs?: Array<{ natIP: string }>;
  }>;
  dockerContainerId?: string;
  dockerContainerName?: string;
  disks?: Array<{ source?: string; deviceName?: string; boot?: boolean; mode?: string }>;
}

interface Address {
  id: string;
  name: string;
  region: string;
  address: string;
  addressType: string;
  status: string;
  users?: string[];
  createdAt?: string;
}

const ComputeDashboardPage = () => {
  const navigate = useNavigate();
  const [instances, setInstances] = useState<Instance[]>([]);
  const [loading, setLoading] = useState(true);
  const [selectedInstance, setSelectedInstance] = useState<Instance | null>(null);
  const [isModalOpen, setIsModalOpen] = useState(false);
  const [activeTab, setActiveTab] = useState<'overview' | 'networking' | 'tags' | 'serial'>('overview');
  const [actionLoading, setActionLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [statusFilter, setStatusFilter] = useState<'all' | 'running' | 'stopped'>('all');
  const { currentProject } = useProject();

  // Serial console
  const [serialOutput, setSerialOutput] = useState<string>('');
  const [serialLoading, setSerialLoading] = useState(false);

  // Tags editing
  const [editingTags, setEditingTags] = useState(false);
  const [tagInput, setTagInput] = useState('');
  const [pendingTags, setPendingTags] = useState<string[]>([]);

  // Static IPs (addresses)
  const [addresses, setAddresses] = useState<Address[]>([]);
  const [addressesLoading, setAddressesLoading] = useState(false);
  const [showCreateAddress, setShowCreateAddress] = useState(false);
  const [newAddrName, setNewAddrName] = useState('');
  const [newAddrRegion, setNewAddrRegion] = useState('us-central1');
  const [creatingAddress, setCreatingAddress] = useState(false);

  const extractName = (url: string) => url?.split('/').pop() || '-';
  const getInternalIp = (instance: Instance) => instance.networkInterfaces?.[0]?.networkIP || '-';
  const getExternalIp = (instance: Instance) => instance.networkInterfaces?.[0]?.accessConfigs?.[0]?.natIP || '-';
  const getNetworkName = (instance: Instance) => instance.networkInterfaces?.[0]?.network?.split('/').pop() || 'default';
  const getSubnetName = (instance: Instance) => instance.networkInterfaces?.[0]?.subnetwork?.split('/').pop() || '-';
  
  const getMachineTypeDetails = (machineType: string) => {
    const type = extractName(machineType);
    const details: Record<string, { cpu: string; memory: string }> = {
      'e2-micro': { cpu: '2 vCPUs', memory: '1 GB' },
      'e2-small': { cpu: '2 vCPUs', memory: '2 GB' },
      'e2-medium': { cpu: '2 vCPUs', memory: '4 GB' },
      'n1-standard-1': { cpu: '1 vCPU', memory: '3.75 GB' },
      'n1-standard-2': { cpu: '2 vCPUs', memory: '7.5 GB' },
      'n1-standard-4': { cpu: '4 vCPUs', memory: '15 GB' },
    };
    return details[type] || { cpu: '-', memory: '-' };
  };

  useEffect(() => {
    loadData();
    loadAddresses();
    const interval = setInterval(loadData, 3000);
    return () => clearInterval(interval);
  }, [currentProject]);

  const loadAddresses = async () => {
    try {
      setAddressesLoading(true);
      const res = await apiClient.get(`/compute/v1/projects/${currentProject}/regions/us-central1/addresses`);
      setAddresses(res.data.items || []);
    } catch {
      // silent fail
    } finally {
      setAddressesLoading(false);
    }
  };

  const loadData = async () => {
    try {
      const zonesRes = await apiClient.get(`/compute/v1/projects/${currentProject}/zones`);
      const zones = zonesRes.data.items || [];
      
      const instancePromises = zones.map((zone: any) =>
        apiClient.get(`/compute/v1/projects/${currentProject}/zones/${zone.name}/instances`)
          .then(res => res.data.items || [])
          .catch(() => [])
      );
      
      const instancesByZone = await Promise.all(instancePromises);
      setInstances(instancesByZone.flat());
      setError(null);
    } catch (err) {
      setError('Failed to load instances');
    } finally {
      setLoading(false);
    }
  };

  const handleAction = async (action: string, instanceName: string, zone: string) => {
    try {
      setActionLoading(true);
      const zoneName = extractName(zone);
      
      if (action === 'delete') {
        if (!confirm(`Delete instance "${instanceName}"?`)) return;
        await apiClient.delete(`/compute/v1/projects/${currentProject}/zones/${zoneName}/instances/${instanceName}`);
      } else {
        await apiClient.post(`/compute/v1/projects/${currentProject}/zones/${zoneName}/instances/${instanceName}/${action}`);
      }
      
      await loadData();
      setIsModalOpen(false);
    } catch (err: any) {
      alert(err.response?.data?.error?.message || `Failed to ${action} instance`);
    } finally {
      setActionLoading(false);
    }
  };

  const getStatusVariant = (status: string) => {
    const variants: Record<string, string> = {
      RUNNING: 'success',
      STOPPED: 'default',
      TERMINATED: 'default',
      PROVISIONING: 'warning',
      STAGING: 'warning',
      STOPPING: 'warning',
    };
    return variants[status?.toUpperCase()] || 'info';
  };

  const openInstanceModal = (instance: Instance) => {
    setSelectedInstance(instance);
    setActiveTab('overview');
    setPendingTags(instance.tags || []);
    setEditingTags(false);
    setSerialOutput('');
    setIsModalOpen(true);
  };

  const fetchSerialOutput = async (instance: Instance) => {
    const zone = extractName(instance.zone);
    setSerialLoading(true);
    try {
      const res = await apiClient.get(
        `/compute/v1/projects/${currentProject}/zones/${zone}/instances/${instance.name}/serialPort`
      );
      setSerialOutput(res.data.contents || '(no output)');
    } catch {
      setSerialOutput('Error fetching serial port output.');
    } finally {
      setSerialLoading(false);
    }
  };

  const handleSaveTags = async () => {
    if (!selectedInstance) return;
    const zone = extractName(selectedInstance.zone);
    try {
      await apiClient.post(
        `/compute/v1/projects/${currentProject}/zones/${zone}/instances/${selectedInstance.name}/setTags`,
        { tags: pendingTags }
      );
      setEditingTags(false);
      setSelectedInstance({ ...selectedInstance, tags: pendingTags });
      loadData();
    } catch (err: any) {
      alert(err.response?.data?.detail || 'Failed to update tags');
    }
  };

  const handleCreateAddress = async () => {
    if (!newAddrName.trim()) return;
    try {
      setCreatingAddress(true);
      await apiClient.post(
        `/compute/v1/projects/${currentProject}/regions/${newAddrRegion}/addresses`,
        { name: newAddrName.trim(), region: newAddrRegion, addressType: 'EXTERNAL' }
      );
      setShowCreateAddress(false);
      setNewAddrName('');
      loadAddresses();
    } catch (err: any) {
      alert(err.response?.data?.detail || 'Failed to create address');
    } finally {
      setCreatingAddress(false);
    }
  };

  const handleDeleteAddress = async (addr: Address) => {
    if (!confirm(`Release static IP "${addr.name}" (${addr.address})?`)) return;
    try {
      await apiClient.delete(
        `/compute/v1/projects/${currentProject}/regions/${addr.region}/addresses/${addr.name}`
      );
      loadAddresses();
    } catch (err: any) {
      alert(err.response?.data?.detail || 'Failed to release address');
    }
  };

  const runningCount = instances.filter(i => i.status === 'RUNNING').length;
  const stoppedCount = instances.filter(i => i.status === 'TERMINATED' || i.status === 'STOPPED').length;

  const filteredInstances = instances.filter(instance => {
    if (statusFilter === 'running') return instance.status === 'RUNNING';
    if (statusFilter === 'stopped') return instance.status === 'TERMINATED' || instance.status === 'STOPPED';
    return true; // 'all'
  });

  if (loading) {
    return (
      <div className="flex items-center justify-center h-screen bg-[#f8f9fa]">
        <div className="text-center">
          <div className="w-12 h-12 border-4 border-blue-600 border-t-transparent rounded-full animate-spin mx-auto mb-3"></div>
          <p className="text-[13px] text-gray-600">Loading instances...</p>
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
                  <Cpu className="w-8 h-8 text-blue-600" />
                </div>
                <div className="flex-1">
                  <h1 className="text-[28px] font-bold text-gray-900 mb-2">Compute Engine</h1>
                  <p className="text-[14px] text-gray-600 leading-relaxed">
                    Create and manage virtual machine instances with flexible configurations.
                  </p>
                </div>
              </div>
            </div>
            <button
              onClick={() => navigate('/services/compute-engine/instances/create')}
              className="inline-flex items-center gap-2 px-4 h-10 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-all shadow-sm hover:shadow-md text-[13px] font-medium"
            >
              <Plus className="w-4 h-4" />
              Create Instance
            </button>
          </div>

          {/* Quick Stats */}
          <div className="flex items-center gap-6 pt-4 border-t border-gray-200">
            <button
              onClick={() => setStatusFilter('all')}
              className={`flex items-center gap-2 px-3 py-2 rounded-lg transition-all cursor-pointer ${
                statusFilter === 'all' ? 'bg-blue-50' : 'hover:bg-gray-50'
              }`}
            >
              <div className="w-2 h-2 bg-blue-500 rounded-full"></div>
              <span className="text-[13px] text-gray-600">
                <span className={`font-semibold ${
                  statusFilter === 'all' ? 'text-blue-600' : 'text-gray-900'
                }`}>{instances.length}</span> Instances
              </span>
            </button>
            <button
              onClick={() => setStatusFilter('running')}
              className={`flex items-center gap-2 px-3 py-2 rounded-lg transition-all cursor-pointer ${
                statusFilter === 'running' ? 'bg-green-50' : 'hover:bg-gray-50'
              }`}
            >
              <div className="w-2 h-2 bg-green-500 rounded-full"></div>
              <span className="text-[13px] text-gray-600">
                <span className={`font-semibold ${
                  statusFilter === 'running' ? 'text-green-600' : 'text-gray-900'
                }`}>{runningCount}</span> Running
              </span>
            </button>
            <button
              onClick={() => setStatusFilter('stopped')}
              className={`flex items-center gap-2 px-3 py-2 rounded-lg transition-all cursor-pointer ${
                statusFilter === 'stopped' ? 'bg-gray-100' : 'hover:bg-gray-50'
              }`}
            >
              <div className="w-2 h-2 bg-gray-500 rounded-full"></div>
              <span className="text-[13px] text-gray-600">
                <span className={`font-semibold ${
                  statusFilter === 'stopped' ? 'text-gray-900' : 'text-gray-900'
                }`}>{stoppedCount}</span> Stopped
              </span>
            </button>
          </div>
        </div>
      </div>

      {/* Main Content */}
      <div className="max-w-[1280px] mx-auto px-8 py-8">
        {/* Instances Grid */}
        <div className="mb-8">
          <div className="flex items-center justify-between mb-4">
            <h2 className="text-[16px] font-bold text-gray-900">VM Instances</h2>
            {statusFilter !== 'all' && (
              <button
                onClick={() => setStatusFilter('all')}
                className="text-[13px] text-blue-600 hover:text-blue-800 font-medium"
              >
                Show all instances
              </button>
            )}
          </div>
          
          {filteredInstances.length > 0 ? (
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
              {filteredInstances.map((instance) => {
                const machineDetails = getMachineTypeDetails(instance.machineType);
                const networkName = getNetworkName(instance);
                const subnetName = getSubnetName(instance);
                
                return (
                  <div
                    key={instance.id}
                    className="bg-white rounded-lg border border-gray-200 shadow-sm hover:shadow-md transition-all group overflow-hidden"
                  >
                    {/* Card Header */}
                    <div className="p-4 border-b border-gray-100 bg-gradient-to-r from-blue-50 to-white">
                      <div className="flex items-start justify-between">
                        <div className="flex items-start gap-3 flex-1">
                          <div className="p-2.5 bg-blue-600 rounded-lg shadow-sm">
                            <Server className="w-5 h-5 text-white" />
                          </div>
                          <div className="flex-1 min-w-0">
                            <button
                              onClick={() => { openInstanceModal(instance); }}
                              className="text-[15px] font-semibold text-gray-900 hover:text-blue-600 transition-colors mb-1 truncate block"
                            >
                              {instance.name}
                            </button>
                            <div className="flex items-center gap-2 flex-wrap">
                              <span className={`inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-[11px] font-medium ${
                                instance.status === 'RUNNING' 
                                  ? 'bg-green-100 text-green-700' 
                                  : 'bg-gray-100 text-gray-700'
                              }`}>
                                <div className={`w-1.5 h-1.5 rounded-full ${
                                  instance.status === 'RUNNING' ? 'bg-green-500 animate-pulse' : 'bg-gray-500'
                                }`} />
                                {instance.status}
                              </span>
                              <span className="text-[11px] text-gray-500">ID: {String(instance.id).substring(0, 8)}</span>
                            </div>
                          </div>
                        </div>
                        <div className="flex items-center gap-1 ml-2">
                          {instance.status === 'RUNNING' ? (
                            <button 
                              onClick={(e) => { e.stopPropagation(); handleAction('stop', instance.name, instance.zone); }}
                              className="p-2 text-orange-600 hover:bg-orange-50 rounded-lg transition-all"
                              title="Stop instance"
                            >
                              <StopCircle className="w-4 h-4" />
                            </button>
                          ) : (instance.status === 'TERMINATED' || instance.status === 'STOPPED') && (
                            <button 
                              onClick={(e) => { e.stopPropagation(); handleAction('start', instance.name, instance.zone); }}
                              className="p-2 text-green-600 hover:bg-green-50 rounded-lg transition-all"
                              title="Start instance"
                            >
                              <Play className="w-4 h-4" />
                            </button>
                          )}
                          <button 
                            onClick={(e) => { e.stopPropagation(); handleAction('delete', instance.name, instance.zone); }}
                            className="p-2 text-red-600 hover:bg-red-50 rounded-lg transition-all"
                            title="Delete instance"
                          >
                            <Trash2 className="w-4 h-4" />
                          </button>
                        </div>
                      </div>
                    </div>

                    {/* Card Body */}
                    <div className="p-4 space-y-3">
                      {/* Machine Type & Resources */}
                      <div className="flex items-center gap-3 p-3 bg-gray-50 rounded-lg">
                        <div className="p-2 bg-white rounded-lg">
                          <Cpu className="w-4 h-4 text-blue-600" />
                        </div>
                        <div className="flex-1">
                          <div className="text-[12px] text-gray-500 mb-0.5">Machine Type</div>
                          <div className="text-[13px] font-semibold text-gray-900">{extractName(instance.machineType)}</div>
                          <div className="flex items-center gap-2 mt-1">
                            <span className="text-[11px] text-gray-600 bg-white px-2 py-0.5 rounded">{machineDetails.cpu}</span>
                            <span className="text-[11px] text-gray-600 bg-white px-2 py-0.5 rounded">{machineDetails.memory}</span>
                          </div>
                        </div>
                      </div>

                      {/* Network Information */}
                      <div className="flex items-start gap-3 p-3 bg-blue-50 rounded-lg">
                        <div className="p-2 bg-white rounded-lg">
                          <Network className="w-4 h-4 text-blue-600" />
                        </div>
                        <div className="flex-1 min-w-0">
                          <div className="text-[12px] text-gray-500 mb-1">Network Configuration</div>
                          <div className="space-y-1.5">
                            <div className="flex items-center gap-2">
                              <span className="text-[11px] text-gray-500">VPC:</span>
                              <span className={`text-[12px] font-medium px-2 py-0.5 rounded ${
                                networkName === 'default' ? 'bg-gray-100 text-gray-700' : 
                                networkName === 'vpc-prod' ? 'bg-purple-100 text-purple-700' :
                                networkName === 'vpc-dev' ? 'bg-green-100 text-green-700' :
                                'bg-blue-100 text-blue-700'
                              }`}>
                                {networkName}
                              </span>
                            </div>
                            {subnetName !== '-' && (
                              <div className="flex items-center gap-2">
                                <span className="text-[11px] text-gray-500">Subnet:</span>
                                <span className="text-[11px] font-mono text-gray-700">{subnetName}</span>
                              </div>
                            )}
                            <div className="flex items-center gap-2">
                              <span className="text-[11px] text-gray-500">Internal IP:</span>
                              <span className="text-[12px] font-mono text-gray-900 bg-white px-2 py-0.5 rounded">{getInternalIp(instance)}</span>
                            </div>
                          </div>
                        </div>
                      </div>

                      {/* Zone & Container Info */}
                      <div className="grid grid-cols-2 gap-3">
                        <div className="flex items-center gap-2 p-3 bg-gray-50 rounded-lg">
                          <div className="p-1.5 bg-white rounded">
                            <MapPin className="w-3.5 h-3.5 text-gray-600" />
                          </div>
                          <div className="flex-1 min-w-0">
                            <div className="text-[11px] text-gray-500">Zone</div>
                            <div className="text-[12px] font-medium text-gray-900 truncate">{extractName(instance.zone)}</div>
                          </div>
                        </div>
                        {instance.dockerContainerName && (
                          <div className="flex items-center gap-2 p-3 bg-gray-50 rounded-lg">
                            <div className="p-1.5 bg-white rounded">
                              <Container className="w-3.5 h-3.5 text-gray-600" />
                            </div>
                            <div className="flex-1 min-w-0">
                              <div className="text-[11px] text-gray-500">Container</div>
                              <div className="text-[12px] font-mono text-gray-900 truncate" title={instance.dockerContainerName}>
                                {instance.dockerContainerName.replace('gcp-vm-', '')}
                              </div>
                            </div>
                          </div>
                        )}
                      </div>
                    </div>

                    {/* Card Footer */}
                    <div className="px-4 py-3 bg-gray-50 border-t border-gray-100">
                      <button
                        onClick={() => { openInstanceModal(instance); }}
                        className="w-full text-[12px] text-blue-600 hover:text-blue-700 font-medium flex items-center justify-center gap-1 group"
                      >
                        View full details
                        <ArrowRight className="w-3 h-3 group-hover:translate-x-0.5 transition-transform" />
                      </button>
                    </div>
                  </div>
                );
              })}
            </div>
          ) : (
            <div className="bg-white rounded-lg border border-gray-200 p-12 text-center">
              <div className="w-20 h-20 bg-gray-100 rounded-full flex items-center justify-center mx-auto mb-4">
                <Server className="w-10 h-10 text-gray-400" />
              </div>
              <h3 className="text-[15px] font-semibold text-gray-900 mb-2">No instances found</h3>
              <p className="text-[13px] text-gray-500 mb-4">
                {statusFilter === 'running' ? 'No running instances' : 
                 statusFilter === 'stopped' ? 'No stopped instances' : 
                 'Create your first VM instance to get started'}
              </p>
              {statusFilter === 'all' && (
                <button
                  onClick={() => navigate('/services/compute-engine/instances/create')}
                  className="inline-flex items-center gap-2 px-4 h-10 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-all text-[13px] font-medium"
                >
                  <Plus className="w-4 h-4" />
                  Create Instance
                </button>
              )}
            </div>
          )}
        </div>

        {/* Recent Activity */}
        {instances.length > 0 && (
          <div className="mt-8">
            <h2 className="text-[16px] font-bold text-gray-900 mb-4">Recent Activity</h2>
            <div className="bg-white rounded-lg border border-gray-200 shadow-[0_1px_3px_rgba(0,0,0,0.07)]">
              <div className="divide-y divide-gray-200">
                {instances.slice(0, 5).map((instance) => (
                  <div key={instance.id} className="flex items-center justify-between p-4 hover:bg-gray-50 transition-colors">
                    <div className="flex items-center gap-3">
                      <div className="p-2 bg-gray-50 rounded-lg">
                        <Activity className="w-4 h-4 text-gray-600" />
                      </div>
                      <div>
                        <p className="text-[13px] font-medium text-gray-900">
                          Instance: <span className="text-blue-600">{instance.name}</span>
                        </p>
                        <p className="text-[12px] text-gray-500">
                          {extractName(instance.zone)} • {extractName(instance.machineType)}
                        </p>
                      </div>
                    </div>
                    <button
                      onClick={() => { openInstanceModal(instance); }}
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

      {/* Instance Details Drawer */}
      {selectedInstance && isModalOpen && (
        <div className="fixed inset-0 z-50 flex justify-end">
          <div className="absolute inset-0 bg-black/30" onClick={() => setIsModalOpen(false)} />
          <div className="relative w-[600px] bg-white shadow-2xl flex flex-col overflow-hidden">
            {/* Drawer Header */}
            <div className="flex items-center justify-between px-6 py-4 border-b border-gray-200 bg-gradient-to-r from-blue-50 to-white">
              <div className="flex items-center gap-3">
                <div className="p-2 bg-blue-600 rounded-lg">
                  <Server className="w-5 h-5 text-white" />
                </div>
                <div>
                  <h2 className="text-[16px] font-bold text-gray-900">{selectedInstance.name}</h2>
                  <span className={`inline-flex items-center gap-1.5 text-[11px] font-medium ${
                    selectedInstance.status === 'RUNNING' ? 'text-green-600' : 'text-gray-500'
                  }`}>
                    <div className={`w-1.5 h-1.5 rounded-full ${selectedInstance.status === 'RUNNING' ? 'bg-green-500 animate-pulse' : 'bg-gray-400'}`} />
                    {selectedInstance.status}
                  </span>
                </div>
              </div>
              <div className="flex items-center gap-2">
                {selectedInstance.status === 'RUNNING' ? (
                  <button onClick={() => handleAction('stop', selectedInstance.name, selectedInstance.zone)} disabled={actionLoading}
                    className="inline-flex items-center gap-1.5 px-3 py-1.5 text-[12px] font-medium text-orange-700 border border-orange-300 rounded-lg hover:bg-orange-50 disabled:opacity-50">
                    <StopCircle className="w-3.5 h-3.5" /> Stop
                  </button>
                ) : (
                  <button onClick={() => handleAction('start', selectedInstance.name, selectedInstance.zone)} disabled={actionLoading}
                    className="inline-flex items-center gap-1.5 px-3 py-1.5 text-[12px] font-medium text-green-700 border border-green-300 rounded-lg hover:bg-green-50 disabled:opacity-50">
                    <Play className="w-3.5 h-3.5" /> Start
                  </button>
                )}
                <button onClick={() => handleAction('delete', selectedInstance.name, selectedInstance.zone)} disabled={actionLoading}
                  className="inline-flex items-center gap-1.5 px-3 py-1.5 text-[12px] font-medium text-red-700 border border-red-300 rounded-lg hover:bg-red-50 disabled:opacity-50">
                  <Trash2 className="w-3.5 h-3.5" /> Delete
                </button>
                <button onClick={() => setIsModalOpen(false)} className="p-1.5 hover:bg-gray-100 rounded-lg">
                  <X className="w-5 h-5 text-gray-500" />
                </button>
              </div>
            </div>

            {/* Tabs */}
            <div className="flex border-b border-gray-200 px-6">
              {(['overview', 'networking', 'tags', 'serial'] as const).map(tab => (
                <button
                  key={tab}
                  onClick={() => {
                    setActiveTab(tab);
                    if (tab === 'serial') fetchSerialOutput(selectedInstance);
                  }}
                  className={`px-4 py-3 text-[13px] font-medium border-b-2 transition-colors capitalize ${
                    activeTab === tab ? 'border-blue-600 text-blue-600' : 'border-transparent text-gray-500 hover:text-gray-700'
                  }`}
                >
                  {tab === 'serial' ? 'Serial Console' : tab.charAt(0).toUpperCase() + tab.slice(1)}
                </button>
              ))}
            </div>

            {/* Tab Content */}
            <div className="flex-1 overflow-y-auto p-6">
              {/* Overview Tab */}
              {activeTab === 'overview' && (
                <div className="space-y-4">
                  <div className="bg-gray-50 rounded-xl divide-y divide-gray-200">
                    {[
                      { label: 'Instance ID', val: String(selectedInstance.id).substring(0, 16) },
                      { label: 'Zone', val: extractName(selectedInstance.zone) },
                      { label: 'Machine Type', val: extractName(selectedInstance.machineType) },
                      { label: 'Description', val: selectedInstance.description || '—' },
                    ].map(({ label, val }) => (
                      <div key={label} className="flex items-center justify-between px-4 py-3">
                        <span className="text-[13px] text-gray-500">{label}</span>
                        <span className="text-[13px] font-medium text-gray-900">{val}</span>
                      </div>
                    ))}
                  </div>

                  {selectedInstance.labels && Object.keys(selectedInstance.labels).length > 0 && (
                    <div>
                      <div className="text-[13px] font-semibold text-gray-700 mb-2">Labels</div>
                      <div className="flex flex-wrap gap-2">
                        {Object.entries(selectedInstance.labels).map(([k, v]) => (
                          <span key={k} className="inline-flex items-center gap-1 px-2.5 py-1 bg-indigo-50 text-indigo-700 rounded text-[12px]">
                            <span className="font-medium">{k}</span>
                            <span className="text-indigo-400">=</span>
                            {v}
                          </span>
                        ))}
                      </div>
                    </div>
                  )}

                  {selectedInstance.dockerContainerId && (
                    <div className="bg-gray-50 rounded-xl divide-y divide-gray-200">
                      <div className="flex items-center justify-between px-4 py-3">
                        <span className="text-[13px] text-gray-500">Container ID</span>
                        <span className="text-[12px] font-mono text-gray-900">{selectedInstance.dockerContainerId.substring(0, 12)}</span>
                      </div>
                    </div>
                  )}
                </div>
              )}

              {/* Networking Tab */}
              {activeTab === 'networking' && (
                <div className="space-y-4">
                  {selectedInstance.networkInterfaces?.map((nic, i) => (
                    <div key={i} className="bg-gray-50 rounded-xl divide-y divide-gray-200">
                      <div className="px-4 py-3 text-[12px] font-semibold text-gray-500 uppercase tracking-wide">NIC {i}</div>
                      {[
                        { label: 'Network', val: extractName(nic.network || '') || '—' },
                        { label: 'Subnet', val: extractName(nic.subnetwork || '') || '—' },
                        { label: 'Internal IP', val: nic.networkIP || '—' },
                        { label: 'External IP', val: nic.accessConfigs?.[0]?.natIP || '—' },
                      ].map(({ label, val }) => (
                        <div key={label} className="flex items-center justify-between px-4 py-3">
                          <span className="text-[13px] text-gray-500">{label}</span>
                          <span className="text-[13px] font-mono font-medium text-gray-900">{val}</span>
                        </div>
                      ))}
                    </div>
                  ))}
                </div>
              )}

              {/* Tags Tab */}
              {activeTab === 'tags' && (
                <div className="space-y-4">
                  <div className="flex items-center justify-between">
                    <div>
                      <div className="text-[14px] font-semibold text-gray-900">Network Tags</div>
                      <div className="text-[12px] text-gray-500 mt-0.5">Used by firewall rules to target this instance</div>
                    </div>
                    {!editingTags
                      ? <button onClick={() => setEditingTags(true)} className="text-[13px] text-blue-600 hover:text-blue-800 font-medium">Edit</button>
                      : <div className="flex gap-2">
                          <button onClick={handleSaveTags} className="text-[13px] text-blue-600 font-medium hover:text-blue-800">Save</button>
                          <button onClick={() => { setEditingTags(false); setPendingTags(selectedInstance.tags || []); }} className="text-[13px] text-gray-500">Cancel</button>
                        </div>
                    }
                  </div>

                  <div className="flex flex-wrap gap-2">
                    {(editingTags ? pendingTags : (selectedInstance.tags || [])).map(tag => (
                      <span key={tag} className="inline-flex items-center gap-1.5 px-3 py-1 bg-blue-50 text-blue-700 rounded-full text-[12px] font-medium">
                        <Tag className="w-3 h-3" />
                        {tag}
                        {editingTags && (
                          <button onClick={() => setPendingTags(p => p.filter(t => t !== tag))} className="ml-0.5 hover:text-red-500">
                            <X className="w-3 h-3" />
                          </button>
                        )}
                      </span>
                    ))}
                    {(editingTags ? pendingTags : (selectedInstance.tags || [])).length === 0 && (
                      <span className="text-[13px] text-gray-400">No tags</span>
                    )}
                  </div>

                  {editingTags && (
                    <div className="flex gap-2 mt-2">
                      <input
                        value={tagInput}
                        onChange={e => setTagInput(e.target.value)}
                        onKeyDown={e => {
                          if (e.key === 'Enter' && tagInput.trim() && !pendingTags.includes(tagInput.trim())) {
                            setPendingTags(p => [...p, tagInput.trim()]);
                            setTagInput('');
                          }
                        }}
                        placeholder="Add tag and press Enter"
                        className="flex-1 px-3 py-2 text-[13px] border border-gray-300 rounded-lg focus:outline-none focus:border-blue-400"
                      />
                      <button
                        onClick={() => {
                          if (tagInput.trim() && !pendingTags.includes(tagInput.trim())) {
                            setPendingTags(p => [...p, tagInput.trim()]);
                            setTagInput('');
                          }
                        }}
                        className="px-3 py-2 bg-blue-600 text-white rounded-lg text-[13px] hover:bg-blue-700"
                      >
                        <Plus className="w-4 h-4" />
                      </button>
                    </div>
                  )}

                  {/* Metadata section */}
                  {(selectedInstance.metadata_items || []).length > 0 && (
                    <div className="mt-6">
                      <div className="text-[14px] font-semibold text-gray-900 mb-2">Metadata</div>
                      <div className="bg-gray-50 rounded-xl divide-y divide-gray-200">
                        {(selectedInstance.metadata_items || []).map((item, i) => (
                          <div key={i} className="flex items-center justify-between px-4 py-3">
                            <span className="text-[13px] font-mono text-gray-600">{item.key}</span>
                            <span className="text-[13px] font-mono text-gray-900 max-w-[280px] truncate">{item.value}</span>
                          </div>
                        ))}
                      </div>
                    </div>
                  )}
                </div>
              )}

              {/* Serial Console Tab */}
              {activeTab === 'serial' && (
                <div className="space-y-3">
                  <div className="flex items-center justify-between">
                    <div className="text-[14px] font-semibold text-gray-900">Serial Port 1 Output</div>
                    <button onClick={() => fetchSerialOutput(selectedInstance)} disabled={serialLoading}
                      className="inline-flex items-center gap-1.5 px-3 py-1.5 text-[12px] font-medium text-gray-600 border border-gray-300 rounded-lg hover:bg-gray-50 disabled:opacity-50">
                      <RefreshCw className={`w-3.5 h-3.5 ${serialLoading ? 'animate-spin' : ''}`} />
                      Refresh
                    </button>
                  </div>
                  <div className="bg-gray-900 rounded-xl p-4 font-mono text-[12px] text-green-400 h-80 overflow-y-auto whitespace-pre-wrap">
                    {serialLoading ? (
                      <span className="text-gray-400 animate-pulse">Fetching serial output...</span>
                    ) : serialOutput || (
                      <span className="text-gray-500">Click Refresh to load serial port output</span>
                    )}
                  </div>
                </div>
              )}
            </div>
          </div>
        </div>
      )}

      {/* Static IPs Section */}
      <div className="max-w-[1280px] mx-auto px-8 pb-8">
        <div className="bg-white rounded-lg border border-gray-200 shadow-sm">
          <div className="flex items-center justify-between px-6 py-4 border-b border-gray-200">
            <div className="flex items-center gap-3">
              <Globe className="w-5 h-5 text-blue-600" />
              <h2 className="text-[15px] font-bold text-gray-900">External IP Addresses</h2>
            </div>
            <button onClick={() => setShowCreateAddress(true)}
              className="inline-flex items-center gap-2 px-3 h-9 bg-blue-600 text-white rounded-lg hover:bg-blue-700 text-[13px] font-medium">
              <Plus className="w-4 h-4" /> Reserve IP
            </button>
          </div>
          {showCreateAddress && (
            <div className="px-6 py-4 bg-blue-50 border-b border-blue-200">
              <div className="flex items-end gap-3">
                <div className="flex-1">
                  <label className="text-[12px] font-medium text-gray-700 block mb-1">Name</label>
                  <input value={newAddrName} onChange={e => setNewAddrName(e.target.value)}
                    placeholder="e.g. my-static-ip"
                    className="w-full px-3 py-2 text-[13px] border border-gray-300 rounded-lg focus:outline-none focus:border-blue-400" />
                </div>
                <div>
                  <label className="text-[12px] font-medium text-gray-700 block mb-1">Region</label>
                  <select value={newAddrRegion} onChange={e => setNewAddrRegion(e.target.value)}
                    className="px-3 py-2 text-[13px] border border-gray-300 rounded-lg focus:outline-none focus:border-blue-400">
                    {['us-central1', 'us-east1', 'us-west1', 'europe-west1', 'asia-east1'].map(r => (
                      <option key={r} value={r}>{r}</option>
                    ))}
                  </select>
                </div>
                <button onClick={handleCreateAddress} disabled={creatingAddress || !newAddrName.trim()}
                  className="px-4 py-2 bg-blue-600 text-white rounded-lg text-[13px] font-medium hover:bg-blue-700 disabled:opacity-50 h-[38px]">
                  {creatingAddress ? 'Reserving...' : 'Reserve'}
                </button>
                <button onClick={() => setShowCreateAddress(false)}
                  className="px-3 py-2 text-gray-500 hover:text-gray-700 border border-gray-300 rounded-lg text-[13px] h-[38px]">
                  Cancel
                </button>
              </div>
            </div>
          )}
          {addressesLoading ? (
            <div className="p-8 text-center text-[13px] text-gray-500">Loading addresses...</div>
          ) : addresses.length === 0 ? (
            <div className="p-8 text-center">
              <Globe className="w-8 h-8 text-gray-300 mx-auto mb-2" />
              <p className="text-[13px] text-gray-500">No static IP addresses reserved</p>
            </div>
          ) : (
            <table className="w-full">
              <thead>
                <tr className="border-b border-gray-200 bg-gray-50">
                  {['Name', 'IP Address', 'Region', 'Type', 'Status', ''].map(h => (
                    <th key={h} className="px-4 py-3 text-left text-[12px] font-semibold text-gray-600">{h}</th>
                  ))}
                </tr>
              </thead>
              <tbody className="divide-y divide-gray-100">
                {addresses.map(addr => (
                  <tr key={addr.name} className="hover:bg-gray-50">
                    <td className="px-4 py-3 text-[13px] font-medium text-gray-900">{addr.name}</td>
                    <td className="px-4 py-3 text-[13px] font-mono text-blue-600">{addr.address || '—'}</td>
                    <td className="px-4 py-3 text-[13px] text-gray-600">{addr.region}</td>
                    <td className="px-4 py-3 text-[13px] text-gray-600">{addr.addressType || 'EXTERNAL'}</td>
                    <td className="px-4 py-3">
                      <span className={`inline-flex items-center px-2 py-0.5 rounded text-[11px] font-medium ${
                        addr.status === 'IN_USE' ? 'bg-green-100 text-green-700' : 'bg-gray-100 text-gray-600'
                      }`}>{addr.status || 'RESERVED'}</span>
                    </td>
                    <td className="px-4 py-3 text-right">
                      <button onClick={() => handleDeleteAddress(addr)} title="Release IP"
                        className="p-1.5 text-red-400 hover:text-red-600 hover:bg-red-50 rounded">
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
    </div>
  );
};

export default ComputeDashboardPage;
