import { useState, useEffect, useCallback, useRef } from 'react';
import { useNavigate, useParams, useSearchParams } from 'react-router-dom';
import { useProject } from '../contexts/ProjectContext';
import {
  getCluster,
  getKubeconfig,
  listNodePools,
  createNodePool,
  deleteNodePool,
  setNodePoolSize,
  listNodes,
  execKubectl,
  listAddons,
  createAddon,
  deleteAddon,
  stopCluster,
  startCluster,
  GKECluster,
  GKENodePool,
  GKENode,
  GKEAddon,
} from '../api/gke';
import toast from 'react-hot-toast';
import {
  ArrowLeft,
  Download,
  Plus,
  Trash2,
  Loader2,
  RefreshCw,
  CheckCircle2,
  XCircle,
  Clock,
  Server,
  Terminal,
  Play,
  Square,
  Package,
  SlidersHorizontal,
} from 'lucide-react';

const TRANSIENT_STATUSES = new Set(['PROVISIONING', 'RECONCILING', 'STOPPING']);

function InfoCard({ label, value }: { label: string; value: string }) {
  return (
    <div className="bg-white rounded-lg border border-gray-200 p-4">
      <p className="text-xs text-gray-500 uppercase tracking-wide mb-1">{label}</p>
      <p className="text-sm font-medium text-gray-900 break-all">{value || '—'}</p>
    </div>
  );
}

function StatusDot({ status }: { status: string }) {
  if (status === 'RUNNING')
    return <CheckCircle2 className="h-4 w-4 text-green-500 inline mr-1" />;
  if (status === 'ERROR')
    return <XCircle className="h-4 w-4 text-red-500 inline mr-1" />;
  if (TRANSIENT_STATUSES.has(status))
    return <Loader2 className="h-4 w-4 text-yellow-500 animate-spin inline mr-1" />;
  return <Clock className="h-4 w-4 text-gray-400 inline mr-1" />;
}

export default function GKEClusterDetailPage() {
  const { clusterName } = useParams<{ clusterName: string }>();
  const [searchParams] = useSearchParams();
  const location = searchParams.get('location') ?? 'us-central1-a';
  const { currentProject } = useProject();
  const navigate = useNavigate();

  const [cluster, setCluster] = useState<GKECluster | null>(null);
  const [nodePools, setNodePools] = useState<GKENodePool[]>([]);
  const [loading, setLoading] = useState(true);
  const [downloadingKubeconfig, setDownloadingKubeconfig] = useState(false);
  const [deletingPool, setDeletingPool] = useState<string | null>(null);
  const [resizingPool, setResizingPool] = useState<string | null>(null);   // pool being resized
  const [resizeTarget, setResizeTarget] = useState<Record<string, number>>({});
  const [savingResize, setSavingResize] = useState<string | null>(null);
  const [showAddPool, setShowAddPool] = useState(false);
  const [newPoolName, setNewPoolName] = useState('');
  const [newPoolNodes, setNewPoolNodes] = useState(3);
  const [addingPool, setAddingPool] = useState(false);
  const [nodes, setNodes] = useState<GKENode[]>([]);
  const [loadingNodes, setLoadingNodes] = useState(false);
  const [nodesError, setNodesError] = useState<string | null>(null);
  // kubectl terminal
  const [kubectlCmd, setKubectlCmd]     = useState('get nodes');
  const [kubectlOut, setKubectlOut]     = useState('');
  const [kubectlRunning, setKubectlRunning] = useState(false);
  // addons
  const [addons, setAddons]             = useState<GKEAddon[]>([]);
  const [loadingAddons, setLoadingAddons] = useState(false);
  const [newAddonName, setNewAddonName] = useState('');
  const [addingAddon, setAddingAddon]   = useState(false);
  const [deletingAddon, setDeletingAddon] = useState<string | null>(null);
  // stop/start
  const [stoppingCluster, setStoppingCluster] = useState(false);
  const [startingCluster, setStartingCluster] = useState(false);
  const pollingRef = useRef<ReturnType<typeof setInterval> | null>(null);

  const fetchAll = useCallback(async () => {
    if (!clusterName) return;
    try {
      const [c, pools] = await Promise.all([
        getCluster(location, clusterName),
        listNodePools(location, clusterName),
      ]);
      setCluster(c);
      setNodePools(pools);
    } catch (err: unknown) {
      toast.error(err instanceof Error ? err.message : 'Failed to load cluster');
    } finally {
      setLoading(false);
    }
  }, [clusterName, location]);

  useEffect(() => {
    fetchAll();
  }, [fetchAll]);

  const fetchAddons = useCallback(async () => {
    if (!clusterName) return;
    setLoadingAddons(true);
    try {
      const data = await listAddons(location, clusterName);
      setAddons(data);
    } catch {
      // addons optional
    } finally {
      setLoadingAddons(false);
    }
  }, [clusterName, location]);

  const fetchNodes = useCallback(async () => {
    if (!clusterName) return;
    setLoadingNodes(true);
    setNodesError(null);
    try {
      const result = await listNodes(location, clusterName);
      setNodes(result.nodes);
      if (result.error) setNodesError(result.error);
    } catch (err: unknown) {
      setNodesError(err instanceof Error ? err.message : 'Failed to load nodes');
    } finally {
      setLoadingNodes(false);
    }
  }, [clusterName, location]);

  // Fetch nodes + addons whenever cluster reaches RUNNING
  useEffect(() => {
    if (cluster?.status === 'RUNNING') {
      fetchNodes();
      fetchAddons();
    }
  }, [cluster?.status, fetchNodes, fetchAddons]);

  // Poll while transient
  useEffect(() => {
    const transient =
      (cluster && TRANSIENT_STATUSES.has(cluster.status)) ||
      nodePools.some((p) => TRANSIENT_STATUSES.has(p.status));

    if (transient && !pollingRef.current) {
      pollingRef.current = setInterval(fetchAll, 5000);
    } else if (!transient && pollingRef.current) {
      clearInterval(pollingRef.current);
      pollingRef.current = null;
    }
    return () => {
      if (pollingRef.current) {
        clearInterval(pollingRef.current);
        pollingRef.current = null;
      }
    };
  }, [cluster, nodePools, fetchAll]);

  async function handleStop() {
    if (!cluster) return;
    setStoppingCluster(true);
    try {
      await stopCluster(location, cluster.name);
      toast.success(`Stopping cluster "${cluster.name}"…`);
      await fetchAll();
    } catch (err: unknown) {
      toast.error(err instanceof Error ? err.message : 'Stop failed');
    } finally {
      setStoppingCluster(false);
    }
  }

  async function handleStart() {
    if (!cluster) return;
    setStartingCluster(true);
    try {
      await startCluster(location, cluster.name);
      toast.success(`Starting cluster "${cluster.name}"…`);
      await fetchAll();
    } catch (err: unknown) {
      toast.error(err instanceof Error ? err.message : 'Start failed');
    } finally {
      setStartingCluster(false);
    }
  }

  async function handleKubectl(e: React.FormEvent) {
    e.preventDefault();
    if (!cluster || !kubectlCmd.trim()) return;
    setKubectlRunning(true);
    setKubectlOut('');
    try {
      const res = await execKubectl(location, cluster.name, kubectlCmd.trim());
      setKubectlOut(res.stdout || res.stderr || '(no output)');
    } catch (err: unknown) {
      setKubectlOut(err instanceof Error ? err.message : 'kubectl failed');
    } finally {
      setKubectlRunning(false);
    }
  }

  async function handleInstallAddon(e: React.FormEvent) {
    e.preventDefault();
    if (!cluster || !newAddonName.trim()) return;
    setAddingAddon(true);
    try {
      await createAddon(location, cluster.name, newAddonName.trim());
      toast.success(`Addon "${newAddonName}" installed`);
      setNewAddonName('');
      await fetchAddons();
    } catch (err: unknown) {
      toast.error(err instanceof Error ? err.message : 'Install failed');
    } finally {
      setAddingAddon(false);
    }
  }

  async function handleDeleteAddon(addonName: string) {
    if (!cluster) return;
    setDeletingAddon(addonName);
    try {
      await deleteAddon(location, cluster.name, addonName);
      toast.success(`Addon "${addonName}" removed`);
      await fetchAddons();
    } catch (err: unknown) {
      toast.error(err instanceof Error ? err.message : 'Delete failed');
    } finally {
      setDeletingAddon(null);
    }
  }

  async function handleDownloadKubeconfig() {
    if (!cluster) return;
    setDownloadingKubeconfig(true);
    try {
      const yaml = await getKubeconfig(location, cluster.name);
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
      setDownloadingKubeconfig(false);
    }
  }

  async function handleDeletePool(pool: GKENodePool) {
    if (!confirm(`Delete node pool "${pool.name}"?`)) return;
    setDeletingPool(pool.name);
    try {
      await deleteNodePool(location, clusterName!, pool.name);
      toast.success(`Deleting node pool "${pool.name}"…`);
      await fetchAll();
    } catch (err: unknown) {
      toast.error(err instanceof Error ? err.message : 'Delete failed');
    } finally {
      setDeletingPool(null);
    }
  }

  async function handleResizePool(pool: GKENodePool) {
    const desired = resizeTarget[pool.name];
    if (desired === undefined || desired < 0) {
      toast.error('Enter a valid node count (≥ 0)');
      return;
    }
    setSavingResize(pool.name);
    try {
      await setNodePoolSize(location, clusterName!, pool.name, desired);
      toast.success(`Resizing "${pool.name}" to ${desired} node(s)…`);
      setResizingPool(null);
      await fetchAll();
    } catch (err: unknown) {
      toast.error(err instanceof Error ? err.message : 'Resize failed');
    } finally {
      setSavingResize(null);
    }
  }

  async function handleAddPool(e: React.FormEvent) {
    e.preventDefault();
    if (!newPoolName.trim()) {
      toast.error('Node pool name is required');
      return;
    }
    setAddingPool(true);
    try {
      await createNodePool(location, clusterName!, {
        name: newPoolName.trim(),
        initialNodeCount: newPoolNodes,
      });
      toast.success(`Adding node pool "${newPoolName}"…`);
      setShowAddPool(false);
      setNewPoolName('');
      setNewPoolNodes(3);
      await fetchAll();
    } catch (err: unknown) {
      toast.error(err instanceof Error ? err.message : 'Failed to add node pool');
    } finally {
      setAddingPool(false);
    }
  }

  if (loading) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <Loader2 className="h-8 w-8 animate-spin text-blue-500" />
      </div>
    );
  }

  if (!cluster) {
    return (
      <div className="flex flex-col items-center justify-center min-h-screen gap-4">
        <p className="text-gray-500">Cluster not found.</p>
        <button
          onClick={() => navigate('/services/gke/clusters')}
          className="text-blue-600 hover:underline text-sm"
        >
          ← Back to clusters
        </button>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <div className="bg-white border-b border-gray-200 px-6 py-4">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-4">
            <button
              onClick={() => navigate('/services/gke/clusters')}
              className="rounded-md p-1.5 text-gray-500 hover:bg-gray-100"
            >
              <ArrowLeft className="h-5 w-5" />
            </button>
            <div>
              <nav className="text-xs text-gray-500 mb-0.5">
                Kubernetes Engine &rsaquo; Clusters &rsaquo;{' '}
                <span className="text-gray-900">{cluster.name}</span>
              </nav>
              <h1 className="text-xl font-semibold text-gray-900 flex items-center gap-2">
                <StatusDot status={cluster.status} />
                {cluster.name}
              </h1>
            </div>
          </div>
          <div className="flex items-center gap-3">
            <button
              onClick={fetchAll}
              className="inline-flex items-center gap-2 rounded-md border border-gray-300 bg-white px-3 py-1.5 text-sm text-gray-700 hover:bg-gray-50"
            >
              <RefreshCw className="h-4 w-4" />
              Refresh
            </button>
            {cluster.status === 'RUNNING' && (
              <button
                onClick={handleStop}
                disabled={stoppingCluster}
                className="inline-flex items-center gap-2 rounded-md border border-orange-300 bg-white px-3 py-1.5 text-sm text-orange-700 hover:bg-orange-50 disabled:opacity-50"
              >
                {stoppingCluster ? <Loader2 className="h-4 w-4 animate-spin" /> : <Square className="h-4 w-4" />}
                Stop
              </button>
            )}
            {cluster.status === 'STOPPED' && (
              <button
                onClick={handleStart}
                disabled={startingCluster}
                className="inline-flex items-center gap-2 rounded-md border border-green-300 bg-white px-3 py-1.5 text-sm text-green-700 hover:bg-green-50 disabled:opacity-50"
              >
                {startingCluster ? <Loader2 className="h-4 w-4 animate-spin" /> : <Play className="h-4 w-4" />}
                Start
              </button>
            )}
            <button
              onClick={handleDownloadKubeconfig}
              disabled={cluster.status !== 'RUNNING' || downloadingKubeconfig}
              className="inline-flex items-center gap-2 rounded-md bg-blue-600 px-4 py-1.5 text-sm font-medium text-white hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed"
            >
              {downloadingKubeconfig ? (
                <Loader2 className="h-4 w-4 animate-spin" />
              ) : (
                <Download className="h-4 w-4" />
              )}
              Download kubeconfig
            </button>
          </div>
        </div>
      </div>

      <div className="px-6 py-6 space-y-6">
        {/* Info cards */}
        <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-4 gap-4">
          <InfoCard label="Status" value={cluster.status} />
          <InfoCard label="Location" value={cluster.location} />
          <InfoCard label="Master Version" value={cluster.currentMasterVersion} />
          <InfoCard label="Nodes" value={String(cluster.currentNodeCount)} />
          <InfoCard label="Endpoint" value={cluster.endpoint || 'Pending…'} />
          <InfoCard label="Network" value={cluster.network} />
          <InfoCard label="Subnetwork" value={cluster.subnetwork} />
          <InfoCard
            label="Created"
            value={new Date(cluster.createTime).toLocaleString()}
          />
        </div>

        {/* Node Pools */}
        <div className="bg-white rounded-lg border border-gray-200 overflow-hidden">
          <div className="flex items-center justify-between px-4 py-3 border-b border-gray-200">
            <h2 className="text-sm font-semibold text-gray-900">Node Pools</h2>
            <button
              onClick={() => setShowAddPool(true)}
              className="inline-flex items-center gap-1.5 rounded-md bg-blue-600 px-3 py-1.5 text-xs font-medium text-white hover:bg-blue-700"
            >
              <Plus className="h-3.5 w-3.5" />
              Add node pool
            </button>
          </div>

          {/* Add node pool inline form */}
          {showAddPool && (
            <form
              onSubmit={handleAddPool}
              className="flex items-end gap-3 px-4 py-3 bg-blue-50 border-b border-blue-100"
            >
              <div>
                <label className="block text-xs text-gray-600 mb-1">Pool name</label>
                <input
                  type="text"
                  value={newPoolName}
                  onChange={(e) => setNewPoolName(e.target.value)}
                  className="rounded border border-gray-300 px-2 py-1 text-sm w-40"
                  placeholder="pool-1"
                  required
                />
              </div>
              <div>
                <label className="block text-xs text-gray-600 mb-1">Nodes</label>
                <input
                  type="number"
                  min={1}
                  value={newPoolNodes}
                  onChange={(e) => setNewPoolNodes(parseInt(e.target.value, 10) || 1)}
                  className="rounded border border-gray-300 px-2 py-1 text-sm w-20"
                />
              </div>
              <button
                type="submit"
                disabled={addingPool}
                className="inline-flex items-center gap-1.5 rounded-md bg-blue-600 px-3 py-1.5 text-xs font-medium text-white hover:bg-blue-700 disabled:opacity-60"
              >
                {addingPool && <Loader2 className="h-3.5 w-3.5 animate-spin" />}
                Add
              </button>
              <button
                type="button"
                onClick={() => setShowAddPool(false)}
                className="rounded-md border border-gray-300 bg-white px-3 py-1.5 text-xs text-gray-600 hover:bg-gray-50"
              >
                Cancel
              </button>
            </form>
          )}

          {nodePools.length === 0 ? (
            <div className="px-4 py-8 text-center text-sm text-gray-400">
              No node pools found.
            </div>
          ) : (
            <table className="w-full text-sm">
              <thead>
                <tr className="border-b border-gray-200 bg-gray-50 text-left">
                  <th className="px-4 py-2.5 font-medium text-gray-600">Name</th>
                  <th className="px-4 py-2.5 font-medium text-gray-600">Status</th>
                  <th className="px-4 py-2.5 font-medium text-gray-600">Nodes</th>
                  <th className="px-4 py-2.5 font-medium text-gray-600">Machine Type</th>
                  <th className="px-4 py-2.5 font-medium text-gray-600">Disk (GB)</th>
                  <th className="px-4 py-2.5 font-medium text-gray-600">Actions</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-gray-100">
                {nodePools.map((p) => (
                  <tr key={p.name} className="hover:bg-gray-50">
                    <td className="px-4 py-2.5 font-medium text-gray-900">{p.name}</td>
                    <td className="px-4 py-2.5 text-gray-600">
                      <span className="inline-flex items-center gap-1">
                        <StatusDot status={p.status} />
                        {p.status}
                      </span>
                    </td>
                    <td className="px-4 py-2.5 text-gray-600">
                      {resizingPool === p.name ? (
                        <span className="inline-flex items-center gap-1">
                          <input
                            type="number"
                            min={0}
                            value={resizeTarget[p.name] ?? p.nodeCount}
                            onChange={(e) =>
                              setResizeTarget((prev) => ({
                                ...prev,
                                [p.name]: parseInt(e.target.value, 10) || 0,
                              }))
                            }
                            className="w-16 rounded border border-blue-400 px-1.5 py-0.5 text-sm text-center focus:outline-none"
                          />
                          <button
                            onClick={() => handleResizePool(p)}
                            disabled={savingResize === p.name}
                            className="rounded bg-blue-600 px-2 py-0.5 text-xs text-white hover:bg-blue-700 disabled:opacity-50"
                          >
                            {savingResize === p.name ? (
                              <Loader2 className="h-3 w-3 animate-spin" />
                            ) : 'Save'}
                          </button>
                          <button
                            onClick={() => setResizingPool(null)}
                            className="rounded border border-gray-300 px-2 py-0.5 text-xs text-gray-600 hover:bg-gray-50"
                          >
                            ✕
                          </button>
                        </span>
                      ) : (
                        p.nodeCount
                      )}
                    </td>
                    <td className="px-4 py-2.5 text-gray-600">{p.config.machineType}</td>
                    <td className="px-4 py-2.5 text-gray-600">{p.config.diskSizeGb}</td>
                    <td className="px-4 py-2.5">
                      <div className="flex items-center gap-1">
                        <button
                          onClick={() => {
                            setResizeTarget((prev) => ({ ...prev, [p.name]: p.nodeCount }));
                            setResizingPool(resizingPool === p.name ? null : p.name);
                          }}
                          disabled={TRANSIENT_STATUSES.has(p.status)}
                          className="rounded p-1 text-gray-400 hover:text-blue-600 hover:bg-blue-50 disabled:opacity-40"
                          title="Resize node pool"
                        >
                          <SlidersHorizontal className="h-4 w-4" />
                        </button>
                        <button
                          onClick={() => handleDeletePool(p)}
                          disabled={
                            TRANSIENT_STATUSES.has(p.status) || deletingPool === p.name
                          }
                          className="rounded p-1 text-gray-400 hover:text-red-600 hover:bg-red-50 disabled:opacity-40"
                          title="Delete node pool"
                        >
                          {deletingPool === p.name ? (
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
        {/* Nodes */}
        <div className="bg-white rounded-lg border border-gray-200 overflow-hidden">
          <div className="flex items-center justify-between px-4 py-3 border-b border-gray-200">
            <h2 className="text-sm font-semibold text-gray-900 flex items-center gap-2">
              <Server className="h-4 w-4 text-gray-500" />
              Nodes
            </h2>
            <button
              onClick={fetchNodes}
              disabled={loadingNodes || cluster.status !== 'RUNNING'}
              className="inline-flex items-center gap-1.5 rounded-md border border-gray-300 bg-white px-2.5 py-1 text-xs text-gray-600 hover:bg-gray-50 disabled:opacity-50"
            >
              {loadingNodes ? (
                <Loader2 className="h-3.5 w-3.5 animate-spin" />
              ) : (
                <RefreshCw className="h-3.5 w-3.5" />
              )}
              Refresh
            </button>
          </div>

          {nodesError && (
            <div className="px-4 py-3 bg-red-50 text-sm text-red-700 border-b border-red-100">
              {nodesError}
            </div>
          )}

          {loadingNodes ? (
            <div className="flex items-center justify-center py-10">
              <Loader2 className="h-6 w-6 animate-spin text-blue-500" />
            </div>
          ) : nodes.length === 0 ? (
            <div className="px-4 py-8 text-center text-sm text-gray-400">
              {cluster.status === 'RUNNING' ? 'No nodes found.' : 'Cluster is not running.'}
            </div>
          ) : (
            <table className="w-full text-sm">
              <thead>
                <tr className="border-b border-gray-200 bg-gray-50 text-left">
                  <th className="px-4 py-2.5 font-medium text-gray-600">Name</th>
                  <th className="px-4 py-2.5 font-medium text-gray-600">Status</th>
                  <th className="px-4 py-2.5 font-medium text-gray-600">Roles</th>
                  <th className="px-4 py-2.5 font-medium text-gray-600">Version</th>
                  <th className="px-4 py-2.5 font-medium text-gray-600">Internal IP</th>
                  <th className="px-4 py-2.5 font-medium text-gray-600">OS Image</th>
                  <th className="px-4 py-2.5 font-medium text-gray-600">Runtime</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-gray-100">
                {nodes.map((node) => (
                  <tr key={node.name} className="hover:bg-gray-50">
                    <td className="px-4 py-2.5 font-mono text-xs text-gray-900">{node.name}</td>
                    <td className="px-4 py-2.5">
                      <span
                        className={`inline-flex items-center gap-1 rounded-full px-2 py-0.5 text-xs font-medium ${
                          node.status === 'Ready'
                            ? 'bg-green-100 text-green-700'
                            : 'bg-red-100 text-red-700'
                        }`}
                      >
                        {node.status === 'Ready' ? (
                          <CheckCircle2 className="h-3 w-3" />
                        ) : (
                          <XCircle className="h-3 w-3" />
                        )}
                        {node.status}
                      </span>
                    </td>
                    <td className="px-4 py-2.5 text-gray-600">{node.roles}</td>
                    <td className="px-4 py-2.5 font-mono text-xs text-gray-600">{node.version}</td>
                    <td className="px-4 py-2.5 font-mono text-xs text-gray-600">{node.internalIP}</td>
                    <td className="px-4 py-2.5 text-xs text-gray-600">{node.osImage}</td>
                    <td className="px-4 py-2.5 font-mono text-xs text-gray-600">{node.containerRuntime}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          )}
        </div>

        {/* kubectl Terminal */}
        <div className="bg-white rounded-lg border border-gray-200 overflow-hidden">
          <div className="flex items-center gap-2 px-4 py-3 border-b border-gray-200">
            <Terminal className="h-4 w-4 text-gray-500" />
            <h2 className="text-sm font-semibold text-gray-900">kubectl</h2>
          </div>
          <div className="p-4 space-y-3">
            <form onSubmit={handleKubectl} className="flex gap-2">
              <span className="flex items-center text-sm text-gray-500 font-mono">kubectl</span>
              <input
                type="text"
                value={kubectlCmd}
                onChange={(e) => setKubectlCmd(e.target.value)}
                disabled={cluster.status !== 'RUNNING' || kubectlRunning}
                placeholder="get pods --all-namespaces"
                className="flex-1 rounded border border-gray-300 px-3 py-1.5 text-sm font-mono focus:outline-none focus:ring-2 focus:ring-blue-500 disabled:bg-gray-50 disabled:text-gray-400"
              />
              <button
                type="submit"
                disabled={cluster.status !== 'RUNNING' || kubectlRunning}
                className="inline-flex items-center gap-1.5 rounded-md bg-blue-600 px-3 py-1.5 text-sm font-medium text-white hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed"
              >
                {kubectlRunning ? <Loader2 className="h-3.5 w-3.5 animate-spin" /> : <Play className="h-3.5 w-3.5" />}
                Run
              </button>
            </form>
            {kubectlOut && (
              <pre className="rounded bg-gray-900 text-gray-100 text-xs font-mono p-4 overflow-x-auto whitespace-pre-wrap max-h-80 overflow-y-auto">
                {kubectlOut}
              </pre>
            )}
            {cluster.status !== 'RUNNING' && (
              <p className="text-xs text-gray-400">Cluster must be RUNNING to execute kubectl commands.</p>
            )}
          </div>
        </div>

        {/* Addons */}
        <div className="bg-white rounded-lg border border-gray-200 overflow-hidden">
          <div className="flex items-center justify-between px-4 py-3 border-b border-gray-200">
            <h2 className="text-sm font-semibold text-gray-900 flex items-center gap-2">
              <Package className="h-4 w-4 text-gray-500" />
              Add-ons
            </h2>
            <button
              onClick={fetchAddons}
              disabled={loadingAddons}
              className="inline-flex items-center gap-1.5 rounded-md border border-gray-300 bg-white px-2.5 py-1 text-xs text-gray-600 hover:bg-gray-50 disabled:opacity-50"
            >
              {loadingAddons ? <Loader2 className="h-3.5 w-3.5 animate-spin" /> : <RefreshCw className="h-3.5 w-3.5" />}
              Refresh
            </button>
          </div>

          {/* Install addon form */}
          <form onSubmit={handleInstallAddon} className="flex items-end gap-3 px-4 py-3 bg-gray-50 border-b border-gray-100">
            <div className="flex-1">
              <label className="block text-xs text-gray-600 mb-1">Addon name</label>
              <select
                value={newAddonName}
                onChange={(e) => setNewAddonName(e.target.value)}
                className="w-full rounded border border-gray-300 px-2 py-1.5 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
              >
                <option value="">— select addon —</option>
                <option value="HttpLoadBalancing">HttpLoadBalancing</option>
                <option value="HorizontalPodAutoscaling">HorizontalPodAutoscaling</option>
                <option value="NetworkPolicy">NetworkPolicy</option>
                <option value="KubernetesDashboard">KubernetesDashboard</option>
                <option value="GcePersistentDiskCsiDriver">GcePersistentDiskCsiDriver</option>
                <option value="GcpFilestoreCsiDriver">GcpFilestoreCsiDriver</option>
              </select>
            </div>
            <button
              type="submit"
              disabled={addingAddon || !newAddonName}
              className="inline-flex items-center gap-1.5 rounded-md bg-blue-600 px-3 py-1.5 text-xs font-medium text-white hover:bg-blue-700 disabled:opacity-60"
            >
              {addingAddon && <Loader2 className="h-3.5 w-3.5 animate-spin" />}
              Install
            </button>
          </form>

          {loadingAddons ? (
            <div className="flex items-center justify-center py-8">
              <Loader2 className="h-6 w-6 animate-spin text-blue-500" />
            </div>
          ) : addons.length === 0 ? (
            <div className="px-4 py-8 text-center text-sm text-gray-400">No add-ons installed.</div>
          ) : (
            <table className="w-full text-sm">
              <thead>
                <tr className="border-b border-gray-200 bg-gray-50 text-left">
                  <th className="px-4 py-2.5 font-medium text-gray-600">Name</th>
                  <th className="px-4 py-2.5 font-medium text-gray-600">Status</th>
                  <th className="px-4 py-2.5 font-medium text-gray-600">Version</th>
                  <th className="px-4 py-2.5 font-medium text-gray-600">Actions</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-gray-100">
                {addons.map((addon) => (
                  <tr key={addon.name} className="hover:bg-gray-50">
                    <td className="px-4 py-2.5 font-medium text-gray-900">{addon.name}</td>
                    <td className="px-4 py-2.5">
                      <span className={`inline-flex items-center gap-1 rounded-full px-2 py-0.5 text-xs font-medium ${
                        addon.status === 'ENABLED'
                          ? 'bg-green-100 text-green-700'
                          : 'bg-gray-100 text-gray-600'
                      }`}>
                        {addon.status}
                      </span>
                    </td>
                    <td className="px-4 py-2.5 text-gray-600 font-mono text-xs">{addon.version || '—'}</td>
                    <td className="px-4 py-2.5">
                      <button
                        onClick={() => handleDeleteAddon(addon.name)}
                        disabled={deletingAddon === addon.name}
                        className="rounded p-1 text-gray-400 hover:text-red-600 hover:bg-red-50 disabled:opacity-40"
                        title="Remove addon"
                      >
                        {deletingAddon === addon.name ? (
                          <Loader2 className="h-4 w-4 animate-spin" />
                        ) : (
                          <Trash2 className="h-4 w-4" />
                        )}
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
}
