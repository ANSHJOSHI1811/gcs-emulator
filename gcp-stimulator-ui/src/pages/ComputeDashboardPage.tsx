import { useEffect, useState } from 'react';
import { Cpu, Server, Plus, StopCircle, Play, Trash2, Network } from 'lucide-react';
import { Link } from 'react-router-dom';
import { apiClient } from '../api/client';
import { Modal, ModalFooter, ModalButton } from '../components/Modal';
import { FormField, Input, Select } from '../components/FormFields';
import { useProject } from '../contexts/ProjectContext';
import { listNetworks, listSubnets } from '../api/networking';

interface Zone {
  id: string;
  name: string;
  region: string;
  status: string;
}

interface Instance {
  id: string;
  name: string;
  zone: string;
  machineType: string;
  status: string;
  networkInterfaces?: Array<{
    networkIP: string;
    accessConfigs?: Array<{
      natIP: string;
    }>;
  }>;
  dockerContainerId?: string;
  dockerContainerName?: string;
}

interface Network {
  name: string;
  id: string;
  autoCreateSubnetworks: boolean;
}

interface Subnet {
  id: string;
  name: string;
  network: string;
  region: string;
  ipCidrRange: string;
  gatewayAddress?: string;
}

const ComputeDashboardPage = () => {
  const [zones, setZones] = useState<Zone[]>([]);
  const [instances, setInstances] = useState<Instance[]>([]);
  const [networks, setNetworks] = useState<Network[]>([]);
  const [subnets, setSubnets] = useState<Subnet[]>([]);
  const [filteredSubnets, setFilteredSubnets] = useState<Subnet[]>([]);
  const [loading, setLoading] = useState(true);
  const [showCreateModal, setShowCreateModal] = useState(false);
  const [createLoading, setCreateLoading] = useState(false);
  const [selectedInstance, setSelectedInstance] = useState<Instance | null>(null);
  const [isInstanceDetailsOpen, setInstanceDetailsOpen] = useState(false);
  const [actionLoading, setActionLoading] = useState(false);
  const [statusFilter, setStatusFilter] = useState<string | null>(null);
  const { currentProject } = useProject();
  const [formData, setFormData] = useState({
    name: '',
    zone: 'us-central1-a',
    machineType: 'n1-standard-1',
    network: 'default',
    subnetwork: ''
  });

  // Helper function to extract resource name from GCP URL
  const extractResourceName = (url: string): string => {
    if (!url) return '-';
    // Extract the last part after the last slash
    const parts = url.split('/');
    return parts[parts.length - 1] || url;
  };

  // Helper function to get internal IP from network interfaces
  const getInternalIp = (instance: Instance): string => {
    return instance.networkInterfaces?.[0]?.networkIP || '-';
  };

  // Helper function to get external IP from network interfaces
  const getExternalIp = (instance: Instance): string => {
    return instance.networkInterfaces?.[0]?.accessConfigs?.[0]?.natIP || '-';
  };

  useEffect(() => {
    loadData();
    
    // Auto-refresh every 3 seconds to update instance status
    const interval = setInterval(() => {
      loadData();
    }, 3000);
    
    return () => clearInterval(interval);
  }, [currentProject]);

  const loadData = async () => {
    try {
      // Load zones first
      const zonesRes = await apiClient.get(`/compute/v1/projects/${currentProject}/zones`);
      const zonesList = zonesRes.data.items || [];
      setZones(zonesList);

      // Load networks
      const networksList = await listNetworks(currentProject);
      setNetworks(networksList as any);

      // Load subnets
      const subnetsList = await listSubnets(currentProject);
      setSubnets(subnetsList as any);

      // Load instances from all zones
      const allInstances: Instance[] = [];
      if (zonesList.length > 0) {
        const instancePromises = zonesList.map((zone: Zone) =>
          apiClient.get(`/compute/v1/projects/${currentProject}/zones/${zone.name}/instances`)
            .then(res => res.data.items || [])
            .catch(() => [])
        );
        const instancesByZone = await Promise.all(instancePromises);
        instancesByZone.forEach(zoneInstances => {
          allInstances.push(...zoneInstances);
        });
      }
      setInstances(allInstances);
    } catch (error) {
      console.error('Failed to load compute data:', error);
    } finally {
      setLoading(false);
    }
  };

  // Filter subnets when network or zone changes
  useEffect(() => {
    if (formData.network && formData.zone) {
      const region = formData.zone.substring(0, formData.zone.lastIndexOf('-')); // Extract region from zone
      const filtered = subnets.filter(subnet => {
        const subnetNetwork = subnet.network.split('/').pop();
        return subnetNetwork === formData.network && subnet.region === region;
      });
      setFilteredSubnets(filtered);
      
      // Auto-select first subnet if available
      if (filtered.length > 0 && !formData.subnetwork) {
        setFormData(prev => ({ ...prev, subnetwork: filtered[0].name }));
      } else if (filtered.length === 0) {
        setFormData(prev => ({ ...prev, subnetwork: '' }));
      }
    } else {
      setFilteredSubnets([]);
    }
  }, [formData.network, formData.zone, subnets]);

  const getStatusColor = (status: string) => {
    switch (status?.toUpperCase()) {
      case 'RUNNING':
        return 'bg-green-100 text-green-800';
      case 'STOPPED':
      case 'TERMINATED':
        return 'bg-gray-100 text-gray-800';
      case 'STAGING':
      case 'PROVISIONING':
      case 'STARTING':
        return 'bg-yellow-100 text-yellow-800';
      case 'STOPPING':
      case 'TERMINATING':
        return 'bg-orange-100 text-orange-800';
      case 'DELETING':
        return 'bg-red-100 text-red-800';
      default:
        return 'bg-blue-100 text-blue-800';
    }
  };

  const handleCreateInstance = async (e: React.FormEvent) => {
    e.preventDefault();
    setCreateLoading(true);
    try {
      const region = formData.zone.substring(0, formData.zone.lastIndexOf('-'));
      const networkInterfaces: any = {
        network: `projects/${currentProject}/global/networks/${formData.network}`
      };
      
      // Add subnetwork if selected
      if (formData.subnetwork) {
        networkInterfaces.subnetwork = `projects/${currentProject}/regions/${region}/subnetworks/${formData.subnetwork}`;
      }

      await apiClient.post(
        `/compute/v1/projects/${currentProject}/zones/${formData.zone}/instances`,
        {
          name: formData.name,
          machineType: formData.machineType,
          networkInterfaces: [networkInterfaces],
          disks: [
            {
              boot: true,
              initializeParams: {
                diskSizeGb: '10',
                sourceImage: 'projects/ubuntu-os-cloud/global/images/family/ubuntu-2004-lts'
              }
            }
          ]
        }
      );
      setShowCreateModal(false);
      setFormData({ name: '', zone: 'us-central1-a', machineType: 'n1-standard-1', network: 'default', subnetwork: '' });
      await loadData();
    } catch (error: any) {
      console.error('Failed to create instance:', error);
      alert(error.response?.data?.error?.message || 'Failed to create instance');
    } finally {
      setCreateLoading(false);
    }
  };

  const handleDeleteInstance = async (instanceName: string, zoneName: string) => {
    if (!confirm(`Are you sure you want to delete instance "${instanceName}"?`)) {
      return;
    }
    try {
      setActionLoading(true);
      // Optimistically update status
      setInstances(prev => prev.map(inst => 
        inst.name === instanceName ? { ...inst, status: 'DELETING' } : inst
      ));
      const zone = extractResourceName(zoneName);
      await apiClient.delete(
        `/compute/v1/projects/${currentProject}/zones/${zone}/instances/${instanceName}`
      );
      await loadData();
    } catch (error: any) {
      console.error('Failed to delete instance:', error);
      alert(error.response?.data?.error?.message || 'Failed to delete instance');
    } finally {
      setActionLoading(false);
    }
  };

  const handleStopInstance = async (instanceName: string, zone: string) => {
    try {
      setActionLoading(true);
      // Optimistically update status
      setInstances(prev => prev.map(inst => 
        inst.name === instanceName ? { ...inst, status: 'STOPPING' } : inst
      ));
      const zoneName = extractResourceName(zone);
      await apiClient.post(
        `/compute/v1/projects/${currentProject}/zones/${zoneName}/instances/${instanceName}/stop`
      );
      await loadData();
    } catch (error: any) {
      console.error('Failed to stop instance:', error);
      alert(error.response?.data?.error?.message || 'Failed to stop instance');
    } finally {
      setActionLoading(false);
    }
  };

  const handleStartInstance = async (instanceName: string, zoneName: string) => {
    try {
      setActionLoading(true);
      // Optimistically update status
      setInstances(prev => prev.map(inst => 
        inst.name === instanceName ? { ...inst, status: 'STARTING' } : inst
      ));
      const zone = extractResourceName(zoneName);
      await apiClient.post(
        `/compute/v1/projects/${currentProject}/zones/${zone}/instances/${instanceName}/start`
      );
      await loadData();
    } catch (error: any) {
      console.error('Failed to start instance:', error);
      alert(error.response?.data?.error?.message || 'Failed to start instance');
    } finally {
      setActionLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header Section */}
      <div className="bg-white border-b border-gray-200 shadow-sm">
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
                    Virtual machines running in Google's data center • <Link to="/services/vpc/networks" className="text-blue-600 hover:underline">View Networks</Link> • <Link to="/services/vpc/subnets" className="text-blue-600 hover:underline">View Subnets</Link>
                  </p>
                </div>
              </div>
            </div>
            <button
              onClick={() => setShowCreateModal(true)}
              className="inline-flex items-center gap-2 px-4 h-10 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-all shadow-sm hover:shadow-md text-[13px] font-medium"
            >
              <Plus className="w-4 h-4" />
              Create Instance
            </button>
          </div>

          {/* Quick Stats */}
          <div className="flex items-center gap-6 pt-4 border-t border-gray-200">
            <button
              onClick={() => setStatusFilter(null)}
              className={`flex items-center gap-2 px-3 py-2 rounded-lg transition-colors cursor-pointer group ${
                statusFilter === null ? 'bg-blue-50' : 'hover:bg-blue-50'
              }`}
            >
              <div className={`w-2 h-2 bg-blue-500 rounded-full ${statusFilter === null ? 'scale-125' : 'group-hover:scale-125'} transition-transform`}></div>
              <span className="text-[13px] text-gray-600">
                <span className={`font-semibold ${statusFilter === null ? 'text-blue-600' : 'text-gray-900 group-hover:text-blue-600'}`}>{instances.length}</span> Instances
              </span>
            </button>
            <button
              onClick={() => setStatusFilter('RUNNING')}
              className={`flex items-center gap-2 px-3 py-2 rounded-lg transition-colors cursor-pointer group ${
                statusFilter === 'RUNNING' ? 'bg-green-50' : 'hover:bg-green-50'
              }`}
            >
              <div className={`w-2 h-2 bg-green-500 rounded-full ${statusFilter === 'RUNNING' ? 'scale-125' : 'group-hover:scale-125'} transition-transform`}></div>
              <span className="text-[13px] text-gray-600">
                <span className={`font-semibold ${statusFilter === 'RUNNING' ? 'text-green-600' : 'text-gray-900 group-hover:text-green-600'}`}>{instances.filter(i => i.status === 'RUNNING').length}</span> Running
              </span>
            </button>
            <button
              onClick={() => setStatusFilter('STOPPED')}
              className={`flex items-center gap-2 px-3 py-2 rounded-lg transition-colors cursor-pointer group ${
                statusFilter === 'STOPPED' ? 'bg-gray-100' : 'hover:bg-gray-100'
              }`}
            >
              <div className={`w-2 h-2 bg-gray-500 rounded-full ${statusFilter === 'STOPPED' ? 'scale-125' : 'group-hover:scale-125'} transition-transform`}></div>
              <span className="text-[13px] text-gray-600">
                <span className={`font-semibold ${statusFilter === 'STOPPED' ? 'text-gray-700' : 'text-gray-900 group-hover:text-gray-700'}`}>{instances.filter(i => i.status === 'TERMINATED' || i.status === 'STOPPED').length}</span> Stopped
              </span>
            </button>
          </div>
        </div>
      </div>

      {/* Main Content */}
      <div className="max-w-[1280px] mx-auto px-8 py-8">
        {/* VM Instances */}
        <div className="mb-8">
          <h2 className="text-[16px] font-bold text-gray-900 mb-4">VM Instances</h2>
          <div className="bg-white rounded-lg border border-gray-200 shadow-[0_1px_3px_rgba(0,0,0,0.07)]">
        {loading ? (
          <div className="p-12 text-center">
            <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto"></div>
            <p className="text-gray-600 mt-4">Loading instances...</p>
          </div>
        ) : (() => {
          const filteredInstances = statusFilter === null
            ? instances
            : statusFilter === 'RUNNING'
            ? instances.filter(i => i.status?.toUpperCase() === 'RUNNING')
            : instances.filter(i => {
                const status = i.status?.toUpperCase();
                return status === 'TERMINATED' || status === 'STOPPED' || status === 'STOPPING' || status === 'TERMINATING';
              });
          
          return filteredInstances.length === 0 ? (
          <div className="p-12 text-center">
            <Server className="w-16 h-16 text-gray-300 mx-auto mb-4" />
            <h3 className="text-lg font-medium text-gray-900 mb-2">No instances yet</h3>
            <p className="text-gray-600 mb-6">
              Create a VM instance to get started with Compute Engine
            </p>
            <button
              onClick={() => setShowCreateModal(true)}
              className="inline-flex items-center gap-2 px-4 h-9 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-all text-[13px] font-medium"
            >
              <Plus className="w-4 h-4" />
              Create Your First Instance
            </button>
          </div>
        ) : (
          <div className="overflow-x-auto">
            <table className="min-w-full divide-y divide-gray-200">
              <thead className="bg-gray-50">
                <tr>
                  <th className="px-6 py-4 text-left text-xs font-semibold text-gray-700 uppercase tracking-wider">
                    Name
                  </th>
                  <th className="px-6 py-4 text-left text-xs font-semibold text-gray-700 uppercase tracking-wider">
                    Zone
                  </th>
                  <th className="px-6 py-4 text-left text-xs font-semibold text-gray-700 uppercase tracking-wider">
                    Status
                  </th>
                  <th className="px-6 py-4 text-right text-xs font-semibold text-gray-700 uppercase tracking-wider">
                    Actions
                  </th>
                </tr>
              </thead>
              <tbody className="bg-white divide-y divide-gray-100">
                {filteredInstances.map((instance) => (
                  <tr key={instance.id} className="hover:bg-gray-50 transition-colors">
                    <td className="px-6 py-4 text-sm font-medium text-gray-900">
                      <button
                        onClick={() => {
                          setSelectedInstance(instance);
                          setInstanceDetailsOpen(true);
                        }}
                        className="text-blue-600 hover:text-blue-800 hover:underline flex items-center gap-2"
                      >
                        <Server className="w-4 h-4 text-gray-400" />
                        <span>{instance.name}</span>
                      </button>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-600">
                      {extractResourceName(instance.zone)}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap">
                      <span
                        className={`px-2 py-1 text-xs font-medium rounded-full ${getStatusColor(
                          instance.status
                        )}`}
                      >
                        {instance.status}
                      </span>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-right text-sm font-medium">
                      <div className="flex items-center justify-end gap-2">
                        {instance.status === 'RUNNING' ? (
                          <button
                            onClick={() => handleStopInstance(instance.name, instance.zone)}
                            className="p-2 text-orange-600 hover:bg-orange-50 rounded-lg transition-colors"
                            title="Stop"
                          >
                            <StopCircle size={18} />
                          </button>
                        ) : instance.status === 'TERMINATED' || instance.status === 'STOPPED' ? (
                          <button
                            onClick={() => handleStartInstance(instance.name, instance.zone)}
                            className="p-2 text-green-600 hover:bg-green-50 rounded-lg transition-colors"
                            title="Start"
                          >
                            <Play size={18} />
                          </button>
                        ) : null}
                        <button
                          onClick={() => handleDeleteInstance(instance.name, instance.zone)}
                          className="p-2 text-red-600 hover:bg-red-50 rounded-lg transition-colors"
                          title="Delete"
                        >
                          <Trash2 size={18} />
                        </button>
                      </div>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        );
        })()}
          </div>
        </div>

        {/* Recent Activity */}
        <div className="mt-8">
          <h2 className="text-[16px] font-bold text-gray-900 mb-4">Recent Activity</h2>
          <div className="bg-white rounded-lg border border-gray-200 shadow-[0_1px_3px_rgba(0,0,0,0.07)]">
            <div className="divide-y divide-gray-200">
              {instances.slice(0, 5).map((instance, index) => (
                <div key={instance.id} className="flex items-center justify-between p-4 hover:bg-gray-50 transition-colors">
                  <div className="flex items-center gap-3">
                    <div className="p-2 bg-gray-50 rounded-lg">
                      <Server className="w-4 h-4 text-gray-600" />
                    </div>
                    <div>
                      <p className="text-[13px] font-medium text-gray-900">
                        Instance: <span className="text-blue-600">{instance.name}</span>
                      </p>
                      <p className="text-[12px] text-gray-500">
                        {extractResourceName(instance.zone)} • {extractResourceName(instance.machineType)}
                      </p>
                    </div>
                  </div>
                  <span className={`px-2 py-1 text-xs font-medium rounded-full ${getStatusColor(instance.status)}`}>
                    {instance.status}
                  </span>
                </div>
              ))}
              {instances.length === 0 && (
                <div className="p-8 text-center">
                  <Server className="w-12 h-12 text-gray-300 mx-auto mb-3" />
                  <p className="text-[13px] text-gray-500">No recent activity</p>
                </div>
              )}
            </div>
          </div>
        </div>
      </div>

      {/* Create Instance Modal */}
      <Modal
        isOpen={showCreateModal}
        onClose={() => setShowCreateModal(false)}
        title="Create VM Instance"
        description="Deploy a new virtual machine instance"
        size="md"
      >
        <form onSubmit={handleCreateInstance} className="space-y-5">
          <FormField
            label="Instance Name"
            required
            help="Lowercase letters, numbers, and hyphens only"
          >
            <Input
              type="text"
              required
              value={formData.name}
              onChange={(e) => setFormData({ ...formData, name: e.target.value })}
              placeholder="my-instance"
              pattern="[a-z0-9-]+"
            />
          </FormField>

          <FormField label="Zone" required>
            <Select
              required
              value={formData.zone}
              onChange={(e) => setFormData({ ...formData, zone: e.target.value })}
            >
              {zones.map(zone => (
                <option key={zone.name} value={zone.name}>
                  {zone.name} ({zone.region})
                </option>
              ))}
            </Select>
          </FormField>

          <FormField label="Machine Type" required>
            <Select
              required
              value={formData.machineType}
              onChange={(e) => setFormData({ ...formData, machineType: e.target.value })}
            >
              <option value="e2-micro">e2-micro (2 vCPUs, 1 GB RAM)</option>
              <option value="e2-small">e2-small (2 vCPUs, 2 GB RAM)</option>
              <option value="e2-medium">e2-medium (2 vCPUs, 4 GB RAM)</option>
              <option value="n1-standard-1">n1-standard-1 (1 vCPU, 3.75 GB RAM)</option>
              <option value="n1-standard-2">n1-standard-2 (2 vCPUs, 7.5 GB RAM)</option>
              <option value="n1-standard-4">n1-standard-4 (4 vCPUs, 15 GB RAM)</option>
            </Select>
          </FormField>

          <FormField label="Network" required>
            <Select
              required
              value={formData.network}
              onChange={(e) => setFormData({ ...formData, network: e.target.value, subnetwork: '' })}
            >
              {networks.map(network => (
                <option key={network.name} value={network.name}>
                  {network.name}
                </option>
              ))}
            </Select>
          </FormField>

          {filteredSubnets.length > 0 && (
            <FormField 
              label="Subnet" 
              required
              help={`${filteredSubnets.length} subnet(s) available in this region`}
            >
              <Select
                required
                value={formData.subnetwork}
                onChange={(e) => setFormData({ ...formData, subnetwork: e.target.value })}
              >
                {filteredSubnets.map(subnet => (
                  <option key={subnet.name} value={subnet.name}>
                    {subnet.name} ({subnet.ipCidrRange})
                  </option>
                ))}
              </Select>
            </FormField>
          )}

          {filteredSubnets.length === 0 && formData.network && (
            <div className="bg-yellow-50 border-2 border-yellow-100 p-4 rounded-xl">
              <p className="text-xs text-yellow-900 font-medium">
                <strong className="font-bold">No subnets found:</strong> <Link to={`/services/vpc/subnets?network=${formData.network}`} className="text-blue-600 hover:underline font-bold">Create a subnet</Link> in the selected network and region first.
              </p>
            </div>
          )}

          <div className="bg-blue-50 border-2 border-blue-100 p-4 rounded-xl">
            <p className="text-xs text-blue-900 font-medium">
              <strong className="font-bold">Note:</strong> Instance will be created with Ubuntu 20.04 LTS image and a Docker container will be automatically spawned.
            </p>
          </div>

          <ModalFooter>
            <ModalButton
              variant="secondary"
              onClick={() => setShowCreateModal(false)}
            >
              Cancel
            </ModalButton>
            <ModalButton
              variant="primary"
              type="submit"
              loading={createLoading}
            >
              Create
            </ModalButton>
          </ModalFooter>
        </form>
      </Modal>

      {/* Instance Details Modal */}
      {selectedInstance && (
        <Modal
          isOpen={isInstanceDetailsOpen}
          onClose={() => {
            setInstanceDetailsOpen(false);
            setSelectedInstance(null);
          }}
          title={selectedInstance.name}
        >
          <div className="space-y-4">
            {/* Status Badge */}
            <div className="flex items-center gap-2">
              <span className={`px-3 py-1 text-xs font-medium rounded-full ${getStatusColor(selectedInstance.status)}`}>
                {selectedInstance.status}
              </span>
            </div>

            {/* Details Grid */}
            <div className="bg-gray-50 rounded-lg p-4 space-y-3">
              <div className="flex justify-between text-sm">
                <span className="text-gray-600">Zone</span>
                <span className="text-gray-900 font-medium">{extractResourceName(selectedInstance.zone)}</span>
              </div>
              <div className="flex justify-between text-sm border-t border-gray-200 pt-3">
                <span className="text-gray-600">Machine Type</span>
                <span className="text-gray-900 font-medium">{extractResourceName(selectedInstance.machineType)}</span>
              </div>
              <div className="flex justify-between text-sm border-t border-gray-200 pt-3">
                <span className="text-gray-600">Internal IP</span>
                <span className="text-gray-900 font-mono text-xs">{getInternalIp(selectedInstance)}</span>
              </div>
              <div className="flex justify-between text-sm border-t border-gray-200 pt-3">
                <span className="text-gray-600">External IP</span>
                <span className="text-gray-900 font-mono text-xs">{getExternalIp(selectedInstance)}</span>
              </div>
              {selectedInstance.dockerContainerId && (
                <>
                  <div className="flex justify-between text-sm border-t border-gray-200 pt-3">
                    <span className="text-gray-600">Container ID</span>
                    <span className="text-gray-900 font-mono text-xs">{selectedInstance.dockerContainerId.substring(0, 12)}</span>
                  </div>
                  {selectedInstance.dockerContainerName && (
                    <div className="flex justify-between text-sm border-t border-gray-200 pt-3">
                      <span className="text-gray-600">Container Name</span>
                      <span className="text-gray-900 font-mono text-xs">{selectedInstance.dockerContainerName}</span>
                    </div>
                  )}
                </>
              )}
            </div>

            {/* Actions */}
            <div className="flex gap-2 pt-2">
              {selectedInstance.status === 'RUNNING' ? (
                <button
                  onClick={() => {
                    handleStopInstance(selectedInstance.name, selectedInstance.zone);
                    setInstanceDetailsOpen(false);
                    setSelectedInstance(null);
                  }}
                  disabled={actionLoading}
                  className="flex-1 flex items-center justify-center gap-2 px-4 py-2 bg-orange-600 text-white rounded-lg hover:bg-orange-700 transition-colors text-sm font-medium disabled:opacity-50 disabled:cursor-not-allowed"
                >
                  {actionLoading ? (
                    <div className="w-4 h-4 border-2 border-white border-t-transparent rounded-full animate-spin"></div>
                  ) : (
                    <StopCircle size={16} />
                  )}
                  Stop Instance
                </button>
              ) : selectedInstance.status === 'TERMINATED' || selectedInstance.status === 'STOPPED' ? (
                <button
                  onClick={() => {
                    handleStartInstance(selectedInstance.name, selectedInstance.zone);
                    setInstanceDetailsOpen(false);
                    setSelectedInstance(null);
                  }}
                  disabled={actionLoading}
                  className="flex-1 flex items-center justify-center gap-2 px-4 py-2 bg-green-600 text-white rounded-lg hover:bg-green-700 transition-colors text-sm font-medium disabled:opacity-50 disabled:cursor-not-allowed"
                >
                  {actionLoading ? (
                    <div className="w-4 h-4 border-2 border-white border-t-transparent rounded-full animate-spin"></div>
                  ) : (
                    <Play size={16} />
                  )}
                  Start Instance
                </button>
              ) : null}
              <button
                onClick={() => {
                  handleDeleteInstance(selectedInstance.name, selectedInstance.zone);
                  setInstanceDetailsOpen(false);
                  setSelectedInstance(null);
                }}
                disabled={actionLoading}
                className="flex items-center justify-center gap-2 px-4 py-2 bg-red-600 text-white rounded-lg hover:bg-red-700 transition-colors text-sm font-medium disabled:opacity-50 disabled:cursor-not-allowed"
              >
                {actionLoading ? (
                  <div className="w-4 h-4 border-2 border-white border-t-transparent rounded-full animate-spin"></div>
                ) : (
                  <Trash2 size={16} />
                )}
                Delete
              </button>
            </div>
          </div>
        </Modal>
      )}
    </div>
  );
};

export default ComputeDashboardPage;
