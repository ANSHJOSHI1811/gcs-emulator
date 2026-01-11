import { useState, useEffect } from 'react';
import { Plus, RefreshCw, Square, Trash2, Power, Server } from 'lucide-react';
import toast from 'react-hot-toast';
import {
  listInstances,
  createInstance,
  stopInstance,
  startInstance,
  terminateInstance,
  getStateColor,
  getStateIcon,
  type ComputeInstance,
} from '../api/compute';
import CreateInstanceModal from '../components/compute/CreateInstanceModal';

export default function ComputeInstancesPage() {
  const [instances, setInstances] = useState<ComputeInstance[]>([]);
  const [loading, setLoading] = useState(true);
  const [showCreateModal, setShowCreateModal] = useState(false);
  const [actionLoading, setActionLoading] = useState<string | null>(null);

  const loadInstances = async () => {
    try {
      setLoading(true);
      const data = await listInstances();
      setInstances(data);
    } catch (error: any) {
      toast.error(error.response?.data?.error || 'Failed to load instances');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadInstances();
    // Auto-refresh every 5 seconds
    const interval = setInterval(loadInstances, 5000);
    return () => clearInterval(interval);
  }, []);

  const handleCreateInstance = async (data: {
    name: string;
    image: string;
    cpu: number;
    memory: number;
  }) => {
    try {
      await createInstance(data);
      toast.success('Instance created successfully');
      setShowCreateModal(false);
      loadInstances();
    } catch (error: any) {
      toast.error(error.response?.data?.error || 'Failed to create instance');
      throw error;
    }
  };

  const handleStopInstance = async (instanceId: string) => {
    try {
      setActionLoading(instanceId);
      await stopInstance(instanceId);
      toast.success('Instance stopped');
      loadInstances();
    } catch (error: any) {
      toast.error(error.response?.data?.error || 'Failed to stop instance');
    } finally {
      setActionLoading(null);
    }
  };

  const handleStartInstance = async (instanceId: string) => {
    try {
      setActionLoading(instanceId);
      await startInstance(instanceId);
      toast.success('Instance started');
      loadInstances();
    } catch (error: any) {
      toast.error(error.response?.data?.error || 'Failed to start instance');
    } finally {
      setActionLoading(null);
    }
  };

  const handleTerminateInstance = async (instanceId: string) => {

    try {
      setActionLoading(instanceId);
      await terminateInstance(instanceId);
      toast.success('Instance terminated');
      loadInstances();
    } catch (error: any) {
      toast.error(error.response?.data?.error || 'Failed to terminate instance');
    } finally {
      setActionLoading(null);
    }
  };

  const getMemoryDisplay = (memoryMb: number) => {
    if (memoryMb >= 1024) {
      return `${(memoryMb / 1024).toFixed(1)} GB`;
    }
    return `${memoryMb} MB`;
  };

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
      <div className="sm:flex sm:items-center sm:justify-between mb-8">
        <div>
          <h1 className="text-3xl font-bold text-gray-900">Compute Engine</h1>
          <p className="mt-2 text-sm text-gray-700">
            Manage virtual machine instances backed by Docker containers
          </p>
        </div>
        <div className="mt-4 sm:mt-0 flex gap-2">
          <button
            onClick={loadInstances}
            disabled={loading}
            className="inline-flex items-center px-4 py-2 border border-gray-300 rounded-md shadow-sm text-sm font-medium text-gray-700 bg-white hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500 disabled:opacity-50"
          >
            <RefreshCw className={`h-4 w-4 mr-2 ${loading ? 'animate-spin' : ''}`} />
            Refresh
          </button>
          <button
            onClick={() => setShowCreateModal(true)}
            className="inline-flex items-center px-4 py-2 border border-transparent rounded-md shadow-sm text-sm font-medium text-white bg-blue-600 hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500"
          >
            <Plus className="h-4 w-4 mr-2" />
            Create Instance
          </button>
        </div>
      </div>

      {loading && instances.length === 0 ? (
        <div className="text-center py-16 bg-white rounded-lg shadow-sm border border-gray-200">
          <RefreshCw className="mx-auto h-12 w-12 text-blue-500 animate-spin" />
          <p className="mt-4 text-sm font-medium text-gray-700">Loading instances...</p>
          <p className="mt-1 text-xs text-gray-500">Please wait while we fetch your compute instances</p>
        </div>
      ) : instances.length === 0 ? (
        <div className="text-center py-16 bg-white rounded-lg shadow-sm border border-gray-200">
          <Server className="mx-auto h-16 w-16 text-gray-300" />
          <h3 className="mt-4 text-lg font-semibold text-gray-900">No instances</h3>
          <p className="mt-2 text-sm text-gray-500">
            Get started by creating your first compute instance.
          </p>
          <div className="mt-8">
            <button
              onClick={() => setShowCreateModal(true)}
              className="inline-flex items-center px-6 py-3 border border-transparent rounded-lg shadow-sm text-sm font-medium text-white bg-blue-600 hover:bg-blue-700 transition-colors"
            >
              <Plus className="h-5 w-5 mr-2" />
              Create Instance
            </button>
          </div>
        </div>
      ) : (
        <div className="bg-white shadow-sm rounded-lg border border-gray-200">
          <ul className="divide-y divide-gray-200">
            {instances.map((instance) => (
              <li key={instance.id} className="hover:bg-gray-50 transition-colors">
                <div className="px-6 py-5">
                  <div className="flex items-center justify-between">
                    <div className="flex-1 min-w-0 pr-4">
                      <div className="flex items-center space-x-3 mb-3">
                        <span
                          className={`inline-flex items-center px-3 py-1 rounded-full text-xs font-semibold ${getStateColor(
                            instance.state
                          )}`}
                        >
                          <span className="mr-1.5 text-sm">{getStateIcon(instance.state)}</span>
                          {instance.state.toUpperCase()}
                        </span>
                        <h3 className="text-lg font-semibold text-gray-900 truncate">
                          {instance.name}
                        </h3>
                      </div>
                      
                      <div className="grid grid-cols-2 gap-3 text-sm">
                        <div className="flex items-center text-gray-600">
                          <span className="font-medium mr-2">ID:</span>
                          <span className="font-mono text-xs bg-gray-100 px-2 py-1 rounded border border-gray-200">
                            {instance.id.substring(0, 13)}...
                          </span>
                        </div>
                        <div className="flex items-center text-gray-600">
                          <span className="font-medium mr-2">Image:</span>
                          <span className="text-blue-600 font-medium">{instance.image}</span>
                        </div>
                        <div className="flex items-center text-gray-600">
                          <span className="font-medium mr-2">Resources:</span>
                          <span>{instance.cpu} CPU • {getMemoryDisplay(instance.memory_mb)}</span>
                        </div>
                        {instance.container_id && (
                          <div className="flex items-center text-gray-600">
                            <span className="font-medium mr-2">Container:</span>
                            <span className="font-mono text-xs bg-blue-50 px-2 py-1 rounded border border-blue-200 text-blue-700">
                              {instance.container_id.substring(0, 12)}
                            </span>
                          </div>
                        )}
                      </div>
                      
                      <div className="mt-2 text-xs text-gray-500">
                        Created {new Date(instance.created_at).toLocaleString()}
                      </div>
                    </div>
                    
                    <div className="flex flex-col space-y-2">
                      {instance.state === 'running' && (
                        <button
                          onClick={() => handleStopInstance(instance.id)}
                          disabled={actionLoading === instance.id}
                          className="inline-flex items-center justify-center px-4 py-2 border border-orange-300 shadow-sm text-sm font-medium rounded-md text-orange-700 bg-white hover:bg-orange-50 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-orange-500 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
                          title="Stop instance"
                        >
                          <Square className="h-4 w-4 mr-2" />
                          Stop
                        </button>
                      )}
                      
                      {(instance.state === 'stopped' || instance.state === 'stopping') && (
                        <button
                          onClick={() => handleStartInstance(instance.id)}
                          disabled={actionLoading === instance.id}
                          className="inline-flex items-center justify-center px-4 py-2 border border-green-300 shadow-sm text-sm font-medium rounded-md text-green-700 bg-white hover:bg-green-50 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-green-500 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
                          title="Start instance"
                        >
                          <Power className="h-4 w-4 mr-2" />
                          Start
                        </button>
                      )}
                      
                      {instance.state !== 'terminated' && (
                        <button
                          onClick={() => handleTerminateInstance(instance.id)}
                          disabled={actionLoading === instance.id}
                          className="inline-flex items-center justify-center px-4 py-2 border border-red-300 shadow-sm text-sm font-medium rounded-md text-red-700 bg-white hover:bg-red-50 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-red-500 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
                          title="Terminate instance"
                        >
                          <Trash2 className="h-4 w-4 mr-2" />
                          Delete
                        </button>
                      )}
                    </div>
                  </div>
                </div>
              </li>
            ))}
          </ul>
        </div>
      )}

      {showCreateModal && (
        <CreateInstanceModal
          onClose={() => setShowCreateModal(false)}
          onCreate={handleCreateInstance}
        />
      )}
    </div>
  );
}
