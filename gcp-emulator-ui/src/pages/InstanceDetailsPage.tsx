import { useEffect, useState } from 'react';
import { useParams, useNavigate, useSearchParams } from 'react-router-dom';
import { fetchInstance, deleteInstance, startInstance, stopInstance } from '@/api/compute';
import { ComputeInstance } from '@/types/compute';
import Spinner from '@/components/common/Spinner';
import DeleteConfirmModal from '@/components/common/DeleteConfirmModal';
import { ArrowLeft, Server, Play, Square, Trash2, Calendar, MapPin, Cpu, HardDrive } from 'lucide-react';
import { format } from 'date-fns';

const STATUS_COLORS: Record<string, string> = {
  RUNNING: "bg-green-100 text-green-800 border-green-200",
  STOPPED: "bg-gray-100 text-gray-800 border-gray-200",
  TERMINATED: "bg-gray-100 text-gray-800 border-gray-200",
  PROVISIONING: "bg-blue-100 text-blue-800 border-blue-200",
  STAGING: "bg-blue-100 text-blue-800 border-blue-200",
  STOPPING: "bg-yellow-100 text-yellow-800 border-yellow-200",
};

export default function InstanceDetailsPage() {
  const { instanceName } = useParams<{ instanceName: string }>();
  const [searchParams] = useSearchParams();
  const zone = searchParams.get('zone') || 'us-central1-a';
  const navigate = useNavigate();

  const [instance, setInstance] = useState<ComputeInstance | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [isDeleteModalOpen, setDeleteModalOpen] = useState(false);
  const [actionInProgress, setActionInProgress] = useState(false);

  const loadInstance = async () => {
    if (!instanceName) return;
    setIsLoading(true);
    setError(null);
    try {
      const data = await fetchInstance(zone, instanceName);
      setInstance(data);
    } catch (err: any) {
      setError(err.response?.data?.error?.message || err.message || "Failed to load instance");
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    loadInstance();
  }, [instanceName, zone]);

  const handleDelete = async () => {
    if (!instanceName) return;
    try {
      await deleteInstance(zone, instanceName);
      setDeleteModalOpen(false);
      navigate('/services/compute/instances');
    } catch (err: any) {
      setError(err.response?.data?.error?.message || err.message || "Failed to delete instance");
    }
  };

  const handleStart = async () => {
    if (!instanceName) return;
    setActionInProgress(true);
    try {
      await startInstance(zone, instanceName);
      await loadInstance();
    } catch (err: any) {
      setError(err.response?.data?.error?.message || err.message || "Failed to start instance");
    } finally {
      setActionInProgress(false);
    }
  };

  const handleStop = async () => {
    if (!instanceName) return;
    setActionInProgress(true);
    try {
      await stopInstance(zone, instanceName);
      await loadInstance();
    } catch (err: any) {
      setError(err.response?.data?.error?.message || err.message || "Failed to stop instance");
    } finally {
      setActionInProgress(false);
    }
  };

  if (isLoading) {
    return (
      <div className="min-h-screen bg-[#f8f9fa]">
        <div className="max-w-[1280px] mx-auto px-8 py-16">
          <div className="flex items-center justify-center py-24 bg-white rounded-lg border border-gray-200 shadow-[0_1px_3px_rgba(0,0,0,0.04)]">
            <Spinner />
          </div>
        </div>
      </div>
    );
  }

  if (error && !instance) {
    return (
      <div className="min-h-screen bg-[#f8f9fa]">
        <div className="max-w-[1280px] mx-auto px-8 py-16">
          <div className="bg-red-50 border border-red-200 rounded-lg px-5 py-4 flex items-start gap-3 shadow-[0_1px_3px_rgba(0,0,0,0.04)]" role="alert">
            <div className="flex-shrink-0 w-5 h-5 mt-0.5">
              <svg className="w-5 h-5 text-red-600" fill="currentColor" viewBox="0 0 20 20">
                <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zM8.707 7.293a1 1 0 00-1.414 1.414L8.586 10l-1.293 1.293a1 1 0 101.414 1.414L10 11.414l1.293 1.293a1 1 0 001.414-1.414L11.414 10l1.293-1.293a1 1 0 00-1.414-1.414L10 8.586 8.707 7.293z" clipRule="evenodd" />
              </svg>
            </div>
            <div>
              <span className="text-[13px] font-medium text-red-800">{error}</span>
              <button
                onClick={() => navigate('/services/compute/instances')}
                className="mt-2 text-sm text-red-600 hover:text-red-800 underline"
              >
                Back to Instances
              </button>
            </div>
          </div>
        </div>
      </div>
    );
  }

  if (!instance) {
    return null;
  }

  return (
    <div className="min-h-screen bg-[#f8f9fa]">
      {/* Header */}
      <div className="bg-white border-b border-gray-200 shadow-[0_1px_3px_rgba(0,0,0,0.04)]">
        <div className="max-w-[1280px] mx-auto px-8 py-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-4">
              <button
                onClick={() => navigate('/services/compute/instances')}
                className="p-2 hover:bg-gray-100 rounded-lg transition-colors"
                title="Back to Instances"
              >
                <ArrowLeft className="w-5 h-5 text-gray-600" />
              </button>
              <div className="flex items-center gap-3">
                <Server className="w-6 h-6 text-gray-500" />
                <div>
                  <h1 className="text-[20px] font-bold text-gray-900">{instance.name}</h1>
                  <div className="flex items-center gap-2 mt-0.5">
                    <span className={`inline-flex items-center px-2.5 py-1 rounded-md text-[11px] font-semibold border ${STATUS_COLORS[instance.status] || STATUS_COLORS.TERMINATED}`}>
                      {instance.status}
                    </span>
                    {instance.statusMessage && (
                      <span className="text-xs text-gray-500">{instance.statusMessage}</span>
                    )}
                  </div>
                </div>
              </div>
            </div>

            <div className="flex items-center gap-2">
              {instance.status === "RUNNING" ? (
                <button
                  onClick={handleStop}
                  disabled={actionInProgress}
                  className="inline-flex items-center gap-1.5 px-4 py-2 text-[13px] font-medium text-yellow-700 bg-yellow-50 border border-yellow-200 rounded-lg hover:bg-yellow-100 transition-colors disabled:opacity-50"
                >
                  <Square className="w-4 h-4" />
                  {actionInProgress ? 'Stopping...' : 'Stop'}
                </button>
              ) : instance.status === "TERMINATED" ? (
                <button
                  onClick={handleStart}
                  disabled={actionInProgress}
                  className="inline-flex items-center gap-1.5 px-4 py-2 text-[13px] font-medium text-green-700 bg-green-50 border border-green-200 rounded-lg hover:bg-green-100 transition-colors disabled:opacity-50"
                >
                  <Play className="w-4 h-4" />
                  {actionInProgress ? 'Starting...' : 'Start'}
                </button>
              ) : null}
              <button
                onClick={() => setDeleteModalOpen(true)}
                className="inline-flex items-center gap-1.5 px-4 py-2 text-[13px] font-medium text-red-700 bg-red-50 border border-red-200 rounded-lg hover:bg-red-100 transition-colors"
              >
                <Trash2 className="w-4 h-4" />
                Delete
              </button>
            </div>
          </div>
        </div>
      </div>

      {/* Content */}
      <div className="max-w-[1280px] mx-auto px-8 py-6">
        {error && (
          <div className="mb-6 bg-red-50 border border-red-200 rounded-lg px-5 py-4 flex items-start gap-3" role="alert">
            <div className="flex-shrink-0 w-5 h-5 mt-0.5">
              <svg className="w-5 h-5 text-red-600" fill="currentColor" viewBox="0 0 20 20">
                <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zM8.707 7.293a1 1 0 00-1.414 1.414L8.586 10l-1.293 1.293a1 1 0 101.414 1.414L10 11.414l1.293 1.293a1 1 0 001.414-1.414L11.414 10l1.293-1.293a1 1 0 00-1.414-1.414L10 8.586 8.707 7.293z" clipRule="evenodd" />
              </svg>
            </div>
            <span className="text-[13px] font-medium text-red-800">{error}</span>
          </div>
        )}

        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          {/* Instance Information */}
          <div className="bg-white rounded-lg border border-gray-200 shadow-[0_1px_3px_rgba(0,0,0,0.04)] p-6">
            <h2 className="text-[16px] font-semibold text-gray-900 mb-4">Instance Information</h2>
            <dl className="space-y-3">
              <div className="flex items-start gap-3">
                <Server className="w-4 h-4 text-gray-400 mt-1" />
                <div className="flex-1">
                  <dt className="text-[12px] font-medium text-gray-500 uppercase">Name</dt>
                  <dd className="text-[14px] text-gray-900 font-medium mt-0.5">{instance.name}</dd>
                </div>
              </div>
              <div className="flex items-start gap-3">
                <MapPin className="w-4 h-4 text-gray-400 mt-1" />
                <div className="flex-1">
                  <dt className="text-[12px] font-medium text-gray-500 uppercase">Zone</dt>
                  <dd className="text-[14px] text-gray-900 mt-0.5">{instance.zone}</dd>
                </div>
              </div>
              <div className="flex items-start gap-3">
                <Cpu className="w-4 h-4 text-gray-400 mt-1" />
                <div className="flex-1">
                  <dt className="text-[12px] font-medium text-gray-500 uppercase">Machine Type</dt>
                  <dd className="text-[14px] text-gray-900 font-mono mt-0.5">{instance.machineType}</dd>
                </div>
              </div>
              <div className="flex items-start gap-3">
                <Calendar className="w-4 h-4 text-gray-400 mt-1" />
                <div className="flex-1">
                  <dt className="text-[12px] font-medium text-gray-500 uppercase">Created</dt>
                  <dd className="text-[14px] text-gray-900 mt-0.5">
                    {format(new Date(instance.creationTimestamp), 'MMM d, yyyy, h:mm a')}
                  </dd>
                </div>
              </div>
              {instance.lastStartTimestamp && (
                <div className="flex items-start gap-3">
                  <Calendar className="w-4 h-4 text-gray-400 mt-1" />
                  <div className="flex-1">
                    <dt className="text-[12px] font-medium text-gray-500 uppercase">Last Started</dt>
                    <dd className="text-[14px] text-gray-900 mt-0.5">
                      {format(new Date(instance.lastStartTimestamp), 'MMM d, yyyy, h:mm a')}
                    </dd>
                  </div>
                </div>
              )}
              {instance.lastStopTimestamp && (
                <div className="flex items-start gap-3">
                  <Calendar className="w-4 h-4 text-gray-400 mt-1" />
                  <div className="flex-1">
                    <dt className="text-[12px] font-medium text-gray-500 uppercase">Last Stopped</dt>
                    <dd className="text-[14px] text-gray-900 mt-0.5">
                      {format(new Date(instance.lastStopTimestamp), 'MMM d, yyyy, h:mm a')}
                    </dd>
                  </div>
                </div>
              )}
              {instance.containerId && (
                <div className="flex items-start gap-3">
                  <HardDrive className="w-4 h-4 text-gray-400 mt-1" />
                  <div className="flex-1">
                    <dt className="text-[12px] font-medium text-gray-500 uppercase">Container ID</dt>
                    <dd className="text-[14px] text-gray-900 font-mono mt-0.5">{instance.containerId}</dd>
                  </div>
                </div>
              )}
            </dl>
          </div>

          {/* Metadata */}
          {instance.metadata && Object.keys(instance.metadata).length > 0 && (
            <div className="bg-white rounded-lg border border-gray-200 shadow-[0_1px_3px_rgba(0,0,0,0.04)] p-6">
              <h2 className="text-[16px] font-semibold text-gray-900 mb-4">Metadata</h2>
              <dl className="space-y-3">
                {Object.entries(instance.metadata).map(([key, value]) => (
                  <div key={key}>
                    <dt className="text-[12px] font-medium text-gray-500 uppercase">{key}</dt>
                    <dd className="text-[14px] text-gray-900 mt-0.5 font-mono break-all">{value}</dd>
                  </div>
                ))}
              </dl>
            </div>
          )}

          {/* Labels */}
          {instance.labels && Object.keys(instance.labels).length > 0 && (
            <div className="bg-white rounded-lg border border-gray-200 shadow-[0_1px_3px_rgba(0,0,0,0.04)] p-6">
              <h2 className="text-[16px] font-semibold text-gray-900 mb-4">Labels</h2>
              <div className="flex flex-wrap gap-2">
                {Object.entries(instance.labels).map(([key, value]) => (
                  <span
                    key={key}
                    className="inline-flex items-center px-3 py-1 rounded-full text-[12px] font-medium bg-blue-100 text-blue-800 border border-blue-200"
                  >
                    {key}: {value}
                  </span>
                ))}
              </div>
            </div>
          )}

          {/* Network Tags */}
          {instance.tags && instance.tags.length > 0 && (
            <div className="bg-white rounded-lg border border-gray-200 shadow-[0_1px_3px_rgba(0,0,0,0.04)] p-6">
              <h2 className="text-[16px] font-semibold text-gray-900 mb-4">Network Tags</h2>
              <div className="flex flex-wrap gap-2">
                {instance.tags.map((tag, index) => (
                  <span
                    key={index}
                    className="inline-flex items-center px-3 py-1 rounded-full text-[12px] font-medium bg-gray-100 text-gray-800 border border-gray-200"
                  >
                    {tag}
                  </span>
                ))}
              </div>
            </div>
          )}
        </div>
      </div>

      {/* Delete Confirmation Modal */}
      <DeleteConfirmModal
        isOpen={isDeleteModalOpen}
        onClose={() => setDeleteModalOpen(false)}
        onConfirm={handleDelete}
        title="Delete VM Instance"
        description={`Are you sure you want to delete "${instance.name}"? This action cannot be undone.`}
      />
    </div>
  );
}
