import { useEffect, useState } from 'react';
import { Cpu, Server, MapPin, Settings, Plus, StopCircle, Play, Trash2 } from 'lucide-react';
import { apiClient } from '../api/client';
import { Modal, ModalFooter, ModalButton } from '../components/Modal';
import { FormField, Input, Select } from '../components/FormFields';
import { useProject } from '../contexts/ProjectContext';

interface Zone {
  id: string;
  name: string;
  region: string;
  status: string;
}

interface MachineType {
  id: string;
  name: string;
  description: string;
  guestCpus: number;
  memoryMb: number;
  zone: string;
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

const ComputeDashboardPage = () => {
  const [zones, setZones] = useState<Zone[]>([]);
  const [instances, setInstances] = useState<Instance[]>([]);
  const [machineTypes, setMachineTypes] = useState<MachineType[]>([]);
  const [loading, setLoading] = useState(true);
  const [showCreateModal, setShowCreateModal] = useState(false);
  const [createLoading, setCreateLoading] = useState(false);
  const { currentProject } = useProject();
  const [formData, setFormData] = useState({
    name: '',
    zone: 'us-central1-a',
    machineType: 'n1-standard-1'
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

      // Load machine types for first zone
      if (zonesList.length > 0) {
        const firstZone = zonesList[0].name;
        const mtRes = await apiClient.get(
          `/compute/v1/projects/${currentProject}/zones/${firstZone}/machineTypes`
        );
        setMachineTypes(mtRes.data.items || []);
      }
    } catch (error) {
      console.error('Failed to load compute data:', error);
    } finally {
      setLoading(false);
    }
  };

  const getStatusColor = (status: string) => {
    switch (status?.toUpperCase()) {
      case 'RUNNING':
        return 'bg-green-100 text-green-800';
      case 'STOPPED':
      case 'TERMINATED':
        return 'bg-gray-100 text-gray-800';
      case 'STAGING':
      case 'PROVISIONING':
        return 'bg-yellow-100 text-yellow-800';
      default:
        return 'bg-blue-100 text-blue-800';
    }
  };

  const handleCreateInstance = async (e: React.FormEvent) => {
    e.preventDefault();
    setCreateLoading(true);
    try {
      await apiClient.post(
        `/compute/v1/projects/${currentProject}/zones/${formData.zone}/instances`,
        {
          name: formData.name,
          machineType: formData.machineType,
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
      setFormData({ name: '', zone: 'us-central1-a', machineType: 'n1-standard-1' });
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
      const zone = extractResourceName(zoneName);
      await apiClient.delete(
        `/compute/v1/projects/${currentProject}/zones/${zone}/instances/${instanceName}`
      );
      await loadData();
    } catch (error: any) {
      console.error('Failed to delete instance:', error);
      alert(error.response?.data?.error?.message || 'Failed to delete instance');
    }
  };

  const handleStopInstance = async (instanceName: string, zoneName: string) => {
    try {
      const zone = extractResourceName(zoneName);
      await apiClient.post(
        `/compute/v1/projects/${currentProject}/zones/${zone}/instances/${instanceName}/stop`
      );
      await loadData();
    } catch (error: any) {
      console.error('Failed to stop instance:', error);
      alert(error.response?.data?.error?.message || 'Failed to stop instance');
    }
  };

  const handleStartInstance = async (instanceName: string, zoneName: string) => {
    try {
      const zone = extractResourceName(zoneName);
      await apiClient.post(
        `/compute/v1/projects/${currentProject}/zones/${zone}/instances/${instanceName}/start`
      );
      await loadData();
    } catch (error: any) {
      console.error('Failed to start instance:', error);
      alert(error.response?.data?.error?.message || 'Failed to start instance');
      alert(error.response?.data?.message || 'Failed to create instance');
    } finally {
      setCreateLoading(false);
    }
  };

  return (
    <div className="p-6 max-w-7xl mx-auto">
      {/* Header */}
      <div className="mb-8 flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-semibold text-gray-900 flex items-center gap-3">
            <Cpu className="w-8 h-8 text-blue-600" />
            Compute Engine
          </h1>
          <p className="text-gray-600 mt-2">
            Manage virtual machines and compute resources
          </p>
        </div>
        <button
          onClick={() => setShowCreateModal(true)}
          className="flex items-center gap-2 px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors"
        >
          <Plus className="w-5 h-5" />
          Create Instance
        </button>
      </div>

      {/* Quick Stats */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-6 mb-8">
        <div className="bg-white rounded-lg border border-gray-200 p-6">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm text-gray-600">VM Instances</p>
              <p className="text-2xl font-semibold text-gray-900 mt-1">
                {instances.length}
              </p>
            </div>
            <Server className="w-8 h-8 text-blue-500" />
          </div>
        </div>

        <div className="bg-white rounded-lg border border-gray-200 p-6">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm text-gray-600">Running</p>
              <p className="text-2xl font-semibold text-gray-900 mt-1">
                {instances.filter(i => i.status === 'RUNNING').length}
              </p>
            </div>
            <div className="w-3 h-3 bg-green-500 rounded-full"></div>
          </div>
        </div>

        <div className="bg-white rounded-lg border border-gray-200 p-6">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm text-gray-600">Zones</p>
              <p className="text-2xl font-semibold text-gray-900 mt-1">
                {zones.length}
              </p>
            </div>
            <MapPin className="w-8 h-8 text-purple-500" />
          </div>
        </div>

        <div className="bg-white rounded-lg border border-gray-200 p-6">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm text-gray-600">Machine Types</p>
              <p className="text-2xl font-semibold text-gray-900 mt-1">
                {machineTypes.length}
              </p>
            </div>
            <Settings className="w-8 h-8 text-orange-500" />
          </div>
        </div>
      </div>

      {/* VM Instances */}
      <div className="bg-white rounded-lg border border-gray-200 mb-8">
        <div className="px-6 py-4 border-b border-gray-200">
          <h2 className="text-lg font-semibold text-gray-900">VM Instances</h2>
          <p className="text-sm text-gray-600 mt-1">
            Manage your virtual machine instances
          </p>
        </div>

        {loading ? (
          <div className="p-12 text-center">
            <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto"></div>
            <p className="text-gray-600 mt-4">Loading instances...</p>
          </div>
        ) : instances.length === 0 ? (
          <div className="p-12 text-center">
            <Server className="w-16 h-16 text-gray-300 mx-auto mb-4" />
            <h3 className="text-lg font-medium text-gray-900 mb-2">No instances yet</h3>
            <p className="text-gray-600 mb-6">
              Create a VM instance to get started with Compute Engine
            </p>
          </div>
        ) : (
          <div className="overflow-x-auto">
            <table className="min-w-full divide-y divide-gray-200">
              <thead className="bg-gray-50">
                <tr>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Name
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Zone
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Machine Type
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Internal IP
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    External IP
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Container ID
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Status
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Actions
                  </th>
                </tr>
              </thead>
              <tbody className="bg-white divide-y divide-gray-200">
                {instances.map((instance) => (
                  <tr key={instance.id} className="hover:bg-gray-50">
                    <td className="px-6 py-4 whitespace-nowrap">
                      <div className="flex items-center">
                        <Server className="w-5 h-5 text-gray-400 mr-3" />
                        <span className="text-sm font-medium text-gray-900">
                          {instance.name}
                        </span>
                      </div>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-600">
                      {extractResourceName(instance.zone)}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-600">
                      {extractResourceName(instance.machineType)}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-600">
                      {getInternalIp(instance)}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-600">
                      {getExternalIp(instance)}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-600 font-mono">
                      {instance.dockerContainerId ? (
                        <span className="text-xs bg-gray-100 px-2 py-1 rounded" title={instance.dockerContainerId}>
                          {instance.dockerContainerId.substring(0, 12)}
                        </span>
                      ) : (
                        '-'
                      )}
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
                    <td className="px-6 py-4 whitespace-nowrap text-sm">
                      <div className="flex items-center space-x-2">
                        {instance.status === 'RUNNING' ? (
                          <button
                            onClick={() => handleStopInstance(instance.name, instance.zone)}
                            className="text-orange-600 hover:text-orange-800 p-1 rounded hover:bg-orange-50 transition-colors"
                            title="Stop instance"
                          >
                            <StopCircle className="w-5 h-5" />
                          </button>
                        ) : instance.status === 'TERMINATED' || instance.status === 'STOPPED' ? (
                          <button
                            onClick={() => handleStartInstance(instance.name, instance.zone)}
                            className="text-green-600 hover:text-green-800 p-1 rounded hover:bg-green-50"
                            title="Start instance"
                          >
                            <Play className="w-5 h-5" />
                          </button>
                        ) : null}
                        <button
                          onClick={() => handleDeleteInstance(instance.name, instance.zone)}
                          className="p-1 text-red-600 hover:text-red-800 hover:bg-red-50 rounded"
                          title="Delete instance"
                        >
                          <Trash2 className="w-4 h-4" />
                        </button>
                      </div>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>

      {/* Zones List */}
      <div className="bg-white rounded-lg border border-gray-200">
        <div className="px-6 py-4 border-b border-gray-200">
          <h2 className="text-lg font-semibold text-gray-900">Available Zones</h2>
          <p className="text-sm text-gray-600 mt-1">
            Zones where you can deploy VM instances
          </p>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-3 gap-4 p-6">
          {zones.map((zone) => (
            <div
              key={zone.id}
              className="border border-gray-200 rounded-lg p-4 hover:border-blue-300 hover:shadow-sm transition-all"
            >
              <div className="flex items-start justify-between">
                <div>
                  <h3 className="font-medium text-gray-900">{zone.name}</h3>
                  <p className="text-sm text-gray-600 mt-1">Region: {zone.region}</p>
                </div>
                <MapPin className="w-5 h-5 text-gray-400" />
              </div>
              <div className="mt-3">
                <span className="px-2 py-1 text-xs font-medium rounded-full bg-green-100 text-green-800">
                  {zone.status}
                </span>
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* API Endpoints Info */}
      <div className="mt-8 bg-blue-50 border border-blue-200 rounded-lg p-6">
        <h3 className="text-lg font-semibold text-blue-900 mb-3">Available Compute APIs</h3>
        <div className="space-y-2 text-sm">
          <div className="flex items-start">
            <code className="bg-blue-100 px-2 py-1 rounded text-blue-900 mr-3">GET</code>
            <span className="text-blue-800">/compute/v1/projects/{'{project}'}/zones</span>
          </div>
          <div className="flex items-start">
            <code className="bg-blue-100 px-2 py-1 rounded text-blue-900 mr-3">GET</code>
            <span className="text-blue-800">/compute/v1/projects/{'{project}'}/zones/{'{zone}'}/instances</span>
          </div>
          <div className="flex items-start">
            <code className="bg-blue-100 px-2 py-1 rounded text-blue-900 mr-3">POST</code>
            <span className="text-blue-800">/compute/v1/projects/{'{project}'}/zones/{'{zone}'}/instances</span>
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
    </div>
  );
};

export default ComputeDashboardPage;
