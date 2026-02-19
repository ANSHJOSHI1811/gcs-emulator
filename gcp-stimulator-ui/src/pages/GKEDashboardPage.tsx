import { useState, useEffect, useCallback, useRef } from 'react';
import { useNavigate } from 'react-router-dom';
import { useProject } from '../contexts/ProjectContext';
import {
  listClusters,
  deleteCluster,
  getKubeconfig,
  stopCluster,
  startCluster,
  GKECluster,
} from '../api/gke';
import toast from 'react-hot-toast';
import {
  Plus,
  Trash2,
  RefreshCw,
  Terminal,
  Loader2,
  AlertCircle,
  CheckCircle2,
  Clock,
  XCircle,
  Download,
  Square,
  Play,
} from 'lucide-react';

const TRANSIENT_STATUSES = new Set(['PROVISIONING', 'RECONCILING', 'STOPPING']);

function StatusBadge({ status }: { status: GKECluster['status'] }) {
  switch (status) {
    case 'RUNNING':
      return (
        <span className="inline-flex items-center gap-1 rounded-full bg-green-100 px-2.5 py-0.5 text-xs font-medium text-green-800">
          <CheckCircle2 className="h-3 w-3" />
          Running
        </span>
      );
    case 'PROVISIONING':
      return (
        <span className="inline-flex items-center gap-1 rounded-full bg-yellow-100 px-2.5 py-0.5 text-xs font-medium text-yellow-800">
          <Loader2 className="h-3 w-3 animate-spin" />
          Provisioning
        </span>
      );
    case 'RECONCILING':
      return (
        <span className="inline-flex items-center gap-1 rounded-full bg-blue-100 px-2.5 py-0.5 text-xs font-medium text-blue-800">
          <Loader2 className="h-3 w-3 animate-spin" />
          Reconciling
        </span>
      );
    case 'STOPPING':
      return (
        <span className="inline-flex items-center gap-1 rounded-full bg-orange-100 px-2.5 py-0.5 text-xs font-medium text-orange-800">
          <Loader2 className="h-3 w-3 animate-spin" />
          Stopping
        </span>
      );
    case 'STOPPED':
      return (
        <span className="inline-flex items-center gap-1 rounded-full bg-gray-100 px-2.5 py-0.5 text-xs font-medium text-gray-600">
          <Square className="h-3 w-3" />
          Stopped
        </span>
      );
    case 'ERROR':
      return (
        <span className="inline-flex items-center gap-1 rounded-full bg-red-100 px-2.5 py-0.5 text-xs font-medium text-red-800">
          <XCircle className="h-3 w-3" />
          Error
        </span>
      );
    default:
      return (
        <span className="inline-flex items-center gap-1 rounded-full bg-gray-100 px-2.5 py-0.5 text-xs font-medium text-gray-600">
          <Clock className="h-3 w-3" />
          {status}
        </span>
      );
  }
}

export default function GKEDashboardPage() {
  const { currentProject } = useProject();
  const navigate = useNavigate();

  const [clusters, setClusters] = useState<GKECluster[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [deletingCluster, setDeletingCluster] = useState<string | null>(null);
  const [stoppingCluster, setStoppingCluster] = useState<string | null>(null);
  const [startingCluster, setStartingCluster] = useState<string | null>(null);
  const [kubeconfigCluster, setKubeconfigCluster] = useState<string | null>(null);
  const pollingRef = useRef<ReturnType<typeof setInterval> | null>(null);

  const fetchClusters = useCallback(async () => {
    if (!currentProject) return;
    try {
      const data = await listClusters('-', currentProject);
      setClusters(data);
      setError(null);
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : 'Failed to load clusters');
    } finally {
      setLoading(false);
    }
  }, [currentProject]);

  // Start/stop polling based on whether any clusters have transient status
  useEffect(() => {
    fetchClusters();
  }, [fetchClusters]);

  useEffect(() => {
    const hasTransient = clusters.some((c) => TRANSIENT_STATUSES.has(c.status));
    if (hasTransient && !pollingRef.current) {
      pollingRef.current = setInterval(fetchClusters, 5000);
    } else if (!hasTransient && pollingRef.current) {
      clearInterval(pollingRef.current);
      pollingRef.current = null;
    }
    return () => {
      if (pollingRef.current) {
        clearInterval(pollingRef.current);
        pollingRef.current = null;
      }
    };
  }, [clusters, fetchClusters]);

  async function handleStop(cluster: GKECluster) {
    setStoppingCluster(cluster.name);
    try {
      await stopCluster(cluster.location, cluster.name);
      toast.success(`Stopping cluster "${cluster.name}"…`);
      await fetchClusters();
    } catch (err: unknown) {
      toast.error(err instanceof Error ? err.message : 'Stop failed');
    } finally {
      setStoppingCluster(null);
    }
  }

  async function handleStart(cluster: GKECluster) {
    setStartingCluster(cluster.name);
    try {
      await startCluster(cluster.location, cluster.name);
      toast.success(`Starting cluster "${cluster.name}"…`);
      await fetchClusters();
    } catch (err: unknown) {
      toast.error(err instanceof Error ? err.message : 'Start failed');
    } finally {
      setStartingCluster(null);
    }
  }

  async function handleDelete(cluster: GKECluster) {
    if (!confirm(`Delete cluster "${cluster.name}"? This cannot be undone.`)) return;
    setDeletingCluster(cluster.name);
    try {
      await deleteCluster(cluster.location, cluster.name);
      toast.success(`Deleting cluster "${cluster.name}"…`);
      await fetchClusters();
    } catch (err: unknown) {
      toast.error(err instanceof Error ? err.message : 'Delete failed');
    } finally {
      setDeletingCluster(null);
    }
  }

  async function handleDownloadKubeconfig(cluster: GKECluster) {
    setKubeconfigCluster(cluster.name);
    try {
      const yaml = await getKubeconfig(cluster.location, cluster.name);
      const blob = new Blob([yaml], { type: 'text/yaml' });
      const url = URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `${cluster.name}-kubeconfig.yaml`;
      document.body.appendChild(a);
      a.click();
      document.body.removeChild(a);
      URL.revokeObjectURL(url);
      toast.success('Kubeconfig downloaded');
    } catch (err: unknown) {
      toast.error(err instanceof Error ? err.message : 'Download failed');
    } finally {
      setKubeconfigCluster(null);
    }
  }

  const running = clusters.filter((c) => c.status === 'RUNNING').length;
  const errored = clusters.filter((c) => c.status === 'ERROR').length;
  const totalNodes = clusters.reduce((sum, c) => sum + (c.currentNodeCount ?? 0), 0);

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <div className="bg-white border-b border-gray-200 px-6 py-4">
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-xl font-semibold text-gray-900">Kubernetes Engine</h1>
            <p className="text-sm text-gray-500 mt-0.5">Clusters · {currentProject}</p>
          </div>
          <div className="flex items-center gap-3">
            <button
              onClick={fetchClusters}
              className="inline-flex items-center gap-2 rounded-md border border-gray-300 bg-white px-3 py-1.5 text-sm text-gray-700 hover:bg-gray-50"
            >
              <RefreshCw className="h-4 w-4" />
              Refresh
            </button>
            <button
              onClick={() => navigate('/services/gke/clusters/create')}
              className="inline-flex items-center gap-2 rounded-md bg-blue-600 px-4 py-1.5 text-sm font-medium text-white hover:bg-blue-700"
            >
              <Plus className="h-4 w-4" />
              Create
            </button>
          </div>
        </div>
      </div>

      <div className="px-6 py-6 space-y-6">
        {/* Stat cards */}
        <div className="grid grid-cols-4 gap-4">
          {[
            { label: 'Total Clusters', value: clusters.length, color: 'text-gray-900' },
            { label: 'Running', value: running, color: 'text-green-600' },
            { label: 'Total Nodes', value: totalNodes, color: 'text-blue-600' },
            { label: 'Errors', value: errored, color: 'text-red-600' },
          ].map((card) => (
            <div key={card.label} className="bg-white rounded-lg border border-gray-200 p-4">
              <p className="text-xs text-gray-500 uppercase tracking-wide">{card.label}</p>
              <p className={`text-3xl font-bold mt-1 ${card.color}`}>{card.value}</p>
            </div>
          ))}
        </div>

        {/* Error */}
        {error && (
          <div className="rounded-md bg-red-50 border border-red-200 p-4 flex items-start gap-3">
            <AlertCircle className="h-5 w-5 text-red-500 shrink-0 mt-0.5" />
            <p className="text-sm text-red-700">{error}</p>
          </div>
        )}

        {/* Cluster table */}
        <div className="bg-white rounded-lg border border-gray-200 overflow-hidden">
          {loading ? (
            <div className="flex items-center justify-center py-16">
              <Loader2 className="h-8 w-8 animate-spin text-blue-500" />
            </div>
          ) : clusters.length === 0 ? (
            <div className="flex flex-col items-center justify-center py-16 text-center">
              <Terminal className="h-12 w-12 text-gray-300 mb-4" />
              <p className="text-gray-500 font-medium">No clusters found</p>
              <p className="text-gray-400 text-sm mt-1">
                Create your first GKE cluster to get started.
              </p>
              <button
                onClick={() => navigate('/services/gke/clusters/create')}
                className="mt-4 inline-flex items-center gap-2 rounded-md bg-blue-600 px-4 py-2 text-sm font-medium text-white hover:bg-blue-700"
              >
                <Plus className="h-4 w-4" />
                Create cluster
              </button>
            </div>
          ) : (
            <table className="w-full text-sm">
              <thead>
                <tr className="border-b border-gray-200 bg-gray-50 text-left">
                  <th className="px-4 py-3 font-medium text-gray-600">Name</th>
                  <th className="px-4 py-3 font-medium text-gray-600">Location</th>
                  <th className="px-4 py-3 font-medium text-gray-600">Status</th>
                  <th className="px-4 py-3 font-medium text-gray-600">Nodes</th>
                  <th className="px-4 py-3 font-medium text-gray-600">Master Version</th>
                  <th className="px-4 py-3 font-medium text-gray-600">Created</th>
                  <th className="px-4 py-3 font-medium text-gray-600">Actions</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-gray-100">
                {clusters.map((c) => (
                  <tr key={c.name} className="hover:bg-gray-50">
                    <td className="px-4 py-3">
                      <button
                        onClick={() =>
                          navigate(
                            `/services/gke/clusters/${c.name}?location=${c.location}`
                          )
                        }
                        className="font-medium text-blue-600 hover:underline"
                      >
                        {c.name}
                      </button>
                    </td>
                    <td className="px-4 py-3 text-gray-600">{c.location}</td>
                    <td className="px-4 py-3">
                      <StatusBadge status={c.status} />
                    </td>
                    <td className="px-4 py-3 text-gray-600">{c.currentNodeCount}</td>
                    <td className="px-4 py-3 text-gray-600">{c.currentMasterVersion}</td>
                    <td className="px-4 py-3 text-gray-500 text-xs">
                      {new Date(c.createTime).toLocaleDateString()}
                    </td>
                    <td className="px-4 py-3">
                      <div className="flex items-center gap-2">
                        {c.status === 'RUNNING' && (
                          <button
                            title="Stop cluster"
                            disabled={stoppingCluster === c.name}
                            onClick={() => handleStop(c)}
                            className="rounded p-1 text-gray-500 hover:bg-gray-100 hover:text-orange-600 disabled:opacity-40 disabled:cursor-not-allowed"
                          >
                            {stoppingCluster === c.name ? (
                              <Loader2 className="h-4 w-4 animate-spin" />
                            ) : (
                              <Square className="h-4 w-4" />
                            )}
                          </button>
                        )}
                        {c.status === 'STOPPED' && (
                          <button
                            title="Start cluster"
                            disabled={startingCluster === c.name}
                            onClick={() => handleStart(c)}
                            className="rounded p-1 text-gray-500 hover:bg-gray-100 hover:text-green-600 disabled:opacity-40 disabled:cursor-not-allowed"
                          >
                            {startingCluster === c.name ? (
                              <Loader2 className="h-4 w-4 animate-spin" />
                            ) : (
                              <Play className="h-4 w-4" />
                            )}
                          </button>
                        )}
                        <button
                          title="Download kubeconfig"
                          disabled={c.status !== 'RUNNING' || kubeconfigCluster === c.name}
                          onClick={() => handleDownloadKubeconfig(c)}
                          className="rounded p-1 text-gray-500 hover:bg-gray-100 hover:text-blue-600 disabled:opacity-40 disabled:cursor-not-allowed"
                        >
                          {kubeconfigCluster === c.name ? (
                            <Loader2 className="h-4 w-4 animate-spin" />
                          ) : (
                            <Download className="h-4 w-4" />
                          )}
                        </button>
                        <button
                          title="Delete cluster"
                          disabled={
                            TRANSIENT_STATUSES.has(c.status) ||
                            deletingCluster === c.name
                          }
                          onClick={() => handleDelete(c)}
                          className="rounded p-1 text-gray-500 hover:bg-gray-100 hover:text-red-600 disabled:opacity-40 disabled:cursor-not-allowed"
                        >
                          {deletingCluster === c.name ? (
                            <Loader2 className="h-4 w-4 animate-spin" />
                          ) : (
                            <Trash2 className="h-4 w-4" />
                          )}
                        </button>
                      </div>
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
}
