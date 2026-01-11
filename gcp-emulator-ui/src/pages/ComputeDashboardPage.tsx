import { useEffect, useState } from 'react';
import { Cpu, Server, MapPin, Settings } from 'lucide-react';
import { apiClient } from '../api/client';

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
  internalIp: string;
  externalIp: string;
}

const ComputeDashboardPage = () => {
  const [zones, setZones] = useState<Zone[]>([]);
  const [instances, setInstances] = useState<Instance[]>([]);
  const [machineTypes, setMachineTypes] = useState<MachineType[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    loadData();
  }, []);

  const loadData = async () => {
    try {
      // Load zones first
      const zonesRes = await apiClient.get('/compute/v1/projects/demo-project/zones');
      const zonesList = zonesRes.data.items || [];
      setZones(zonesList);

      // Load instances from all zones
      const allInstances: Instance[] = [];
      if (zonesList.length > 0) {
        const instancePromises = zonesList.map((zone: Zone) =>
          apiClient.get(`/compute/v1/projects/demo-project/zones/${zone.name}/instances`)
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
          `/compute/v1/projects/demo-project/zones/${firstZone}/machineTypes`
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

  return (
    <div className="p-6 max-w-7xl mx-auto">
      {/* Header */}
      <div className="mb-8">
        <h1 className="text-3xl font-semibold text-gray-900 flex items-center gap-3">
          <Cpu className="w-8 h-8 text-blue-600" />
          Compute Engine
        </h1>
        <p className="text-gray-600 mt-2">
          Virtual machines running in Google's data center
        </p>
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
                    Status
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
                      {instance.zone}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-600">
                      {instance.machineType}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-600">
                      {instance.internalIp || '-'}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-600">
                      {instance.externalIp || '-'}
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
    </div>
  );
};

export default ComputeDashboardPage;
