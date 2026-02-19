import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { useProject } from '../contexts/ProjectContext';
import { createCluster, getServerConfig } from '../api/gke';
import { apiClient } from '../api/client';
import toast from 'react-hot-toast';
import { ArrowLeft, Loader2, ChevronDown, ChevronUp } from 'lucide-react';

interface Zone { name: string; region: string }
interface Network { name: string }

const MACHINE_TYPES = [
  'e2-micro', 'e2-small', 'e2-medium',
  'n1-standard-1', 'n1-standard-2', 'n1-standard-4',
];

export default function CreateClusterPage() {
  const { currentProject } = useProject();
  const navigate = useNavigate();

  const [zones, setZones]       = useState<Zone[]>([]);
  const [networks, setNetworks] = useState<Network[]>([]);
  const [submitting, setSubmitting] = useState(false);
  const [showAdvanced, setShowAdvanced] = useState(false);
  const [validVersions, setValidVersions] = useState<string[]>(['1.30', '1.29', '1.28', '1.27']);

  const [form, setForm] = useState({
    name: 'my-cluster',
    location: 'us-central1-a',
    masterVersion: '1.28',
    nodePoolName: 'default-pool',
    nodeCount: 3,
    machineType: 'e2-medium',
    diskSizeGb: 100,
    network: 'default',
    description: '',
    // GCP-specific
    clusterType: 'STANDARD' as 'STANDARD' | 'AUTOPILOT',
    releaseChannel: 'REGULAR' as 'RAPID' | 'REGULAR' | 'STABLE' | 'NONE',
    enablePrivateNodes: false,
    loggingEnabled: true,
    monitoringEnabled: true,
  });

  function set<K extends keyof typeof form>(key: K, value: typeof form[K]) {
    setForm((prev) => ({ ...prev, [key]: value }));
  }

  useEffect(() => {
    if (!currentProject) return;
    Promise.all([
      apiClient
        .get<{ items?: Zone[] }>(`/compute/v1/projects/${currentProject}/zones`)
        .then((r) => setZones(r.data.items ?? [])),
      apiClient
        .get<{ items?: Network[] }>(`/compute/v1/projects/${currentProject}/global/networks`)
        .then((r) => setNetworks(r.data.items ?? []))
        .catch(() => setNetworks([{ name: 'default' }])),
      getServerConfig(form.location)
        .then((cfg) => {
          if (cfg.validMasterVersions?.length) setValidVersions(cfg.validMasterVersions);
        })
        .catch(() => {}),
    ]).catch(() => {});
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [currentProject]);

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    if (!form.name.trim()) { toast.error('Cluster name is required'); return; }
    setSubmitting(true);
    try {
      const autopilot = form.clusterType === 'AUTOPILOT';
      await createCluster(form.location, {
        name: form.name.trim(),
        description: form.description,
        masterVersion: form.masterVersion,
        initialNodeCount: form.nodeCount,
        nodeConfig: { machineType: form.machineType, diskSizeGb: form.diskSizeGb },
        network: form.network,
        subnetwork: form.network,
        clusterType: form.clusterType,
        autopilot: { enabled: autopilot },
        releaseChannel: { channel: form.releaseChannel },
        privateClusterConfig: { enablePrivateNodes: form.enablePrivateNodes },
        loggingService: form.loggingEnabled
          ? 'logging.googleapis.com/kubernetes' : 'none',
        monitoringService: form.monitoringEnabled
          ? 'monitoring.googleapis.com/kubernetes' : 'none',
        nodePools: [{ name: form.nodePoolName }],
      });
      toast.success(`Cluster "${form.name}" is being created…`);
      navigate('/services/gke/clusters');
    } catch (err: unknown) {
      toast.error(err instanceof Error ? err.message : 'Failed to create cluster');
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <div className="bg-white border-b border-gray-200 px-6 py-4">
        <div className="flex items-center gap-4">
          <button
            onClick={() => navigate('/services/gke/clusters')}
            className="rounded-md p-1.5 text-gray-500 hover:bg-gray-100"
          >
            <ArrowLeft className="h-5 w-5" />
          </button>
          <div>
            <h1 className="text-xl font-semibold text-gray-900">Create a Kubernetes cluster</h1>
            <p className="text-sm text-gray-500">Project: {currentProject}</p>
          </div>
        </div>
      </div>

      <div className="max-w-2xl mx-auto px-6 py-8">
        <form onSubmit={handleSubmit} className="space-y-6">

          {/* Cluster basics */}
          <section className="bg-white rounded-lg border border-gray-200 p-6 space-y-4">
            <h2 className="text-base font-semibold text-gray-900">Cluster basics</h2>

            {/* Cluster Type */}
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">Cluster type</label>
              <div className="flex rounded-md border border-gray-300 overflow-hidden text-sm">
                {(['STANDARD', 'AUTOPILOT'] as const).map((t) => (
                  <button
                    key={t}
                    type="button"
                    onClick={() => set('clusterType', t)}
                    className={`flex-1 py-2 font-medium transition-colors ${
                      form.clusterType === t
                        ? 'bg-blue-600 text-white'
                        : 'bg-white text-gray-700 hover:bg-gray-50'
                    }`}
                  >
                    {t === 'STANDARD' ? 'Standard' : 'Autopilot'}
                  </button>
                ))}
              </div>
              <p className="mt-1 text-xs text-gray-400">
                {form.clusterType === 'AUTOPILOT'
                  ? 'Google manages node provisioning and scaling automatically.'
                  : 'You manage node pools, scaling, and upgrades.'}
              </p>
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Cluster name <span className="text-red-500">*</span>
              </label>
              <input
                type="text"
                value={form.name}
                onChange={(e) => set('name', e.target.value)}
                className="w-full rounded-md border border-gray-300 px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
                placeholder="my-cluster"
                required
              />
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">Location</label>
              <select
                value={form.location}
                onChange={(e) => set('location', e.target.value)}
                className="w-full rounded-md border border-gray-300 px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
              >
                {zones.length === 0 ? (
                  <option value={form.location}>{form.location}</option>
                ) : (
                  zones.map((z) => <option key={z.name} value={z.name}>{z.name}</option>)
                )}
              </select>
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Release channel
              </label>
              <select
                value={form.releaseChannel}
                onChange={(e) => set('releaseChannel', e.target.value as typeof form.releaseChannel)}
                className="w-full rounded-md border border-gray-300 px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
              >
                <option value="RAPID">Rapid</option>
                <option value="REGULAR">Regular (recommended)</option>
                <option value="STABLE">Stable</option>
                <option value="NONE">No channel</option>
              </select>
              <p className="mt-1 text-xs text-gray-400">
                Controls how frequently this cluster receives automatic version upgrades.
              </p>
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">Master version</label>
              <select
                value={form.masterVersion}
                onChange={(e) => set('masterVersion', e.target.value)}
                className="w-full rounded-md border border-gray-300 px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
              >
                {validVersions.map((v) => <option key={v} value={v}>{v}</option>)}
              </select>
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">Description</label>
              <textarea
                value={form.description}
                onChange={(e) => set('description', e.target.value)}
                rows={2}
                className="w-full rounded-md border border-gray-300 px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
                placeholder="Optional description"
              />
            </div>
          </section>

          {/* Default node pool */}
          <section className="bg-white rounded-lg border border-gray-200 p-6 space-y-4">
            <h2 className="text-base font-semibold text-gray-900">Default node pool</h2>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">Node pool name</label>
              <input
                type="text"
                value={form.nodePoolName}
                onChange={(e) => set('nodePoolName', e.target.value)}
                className="w-full rounded-md border border-gray-300 px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
              />
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">Number of nodes</label>
              <input
                type="number"
                min={1}
                max={100}
                value={form.nodeCount}
                onChange={(e) => set('nodeCount', parseInt(e.target.value, 10) || 1)}
                className="w-full rounded-md border border-gray-300 px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
              />
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">Machine type</label>
              <select
                value={form.machineType}
                onChange={(e) => set('machineType', e.target.value)}
                className="w-full rounded-md border border-gray-300 px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
              >
                {MACHINE_TYPES.map((t) => <option key={t} value={t}>{t}</option>)}
              </select>
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">Boot disk size (GB)</label>
              <input
                type="number"
                min={10}
                max={2000}
                value={form.diskSizeGb}
                onChange={(e) => set('diskSizeGb', parseInt(e.target.value, 10) || 100)}
                className="w-full rounded-md border border-gray-300 px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
              />
            </div>
          </section>

          {/* Networking */}
          <section className="bg-white rounded-lg border border-gray-200 p-6 space-y-4">
            <h2 className="text-base font-semibold text-gray-900">Networking</h2>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">Network</label>
              <select
                value={form.network}
                onChange={(e) => set('network', e.target.value)}
                className="w-full rounded-md border border-gray-300 px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
              >
                {networks.length === 0 ? (
                  <option value="default">default</option>
                ) : (
                  networks.map((n) => <option key={n.name} value={n.name}>{n.name}</option>)
                )}
              </select>
            </div>
          </section>

          {/* Advanced settings */}
          <section className="bg-white rounded-lg border border-gray-200 overflow-hidden">
            <button
              type="button"
              onClick={() => setShowAdvanced((v) => !v)}
              className="w-full flex items-center justify-between px-6 py-4 text-sm font-semibold text-gray-900 hover:bg-gray-50"
            >
              Advanced settings
              {showAdvanced ? <ChevronUp className="h-4 w-4" /> : <ChevronDown className="h-4 w-4" />}
            </button>

            {showAdvanced && (
              <div className="px-6 pb-6 space-y-4 border-t border-gray-100">
                {/* Private nodes */}
                <label className="flex items-center gap-3 pt-4 cursor-pointer">
                  <input
                    type="checkbox"
                    checked={form.enablePrivateNodes}
                    onChange={(e) => set('enablePrivateNodes', e.target.checked)}
                    className="h-4 w-4 rounded border-gray-300 text-blue-600"
                  />
                  <div>
                    <span className="text-sm font-medium text-gray-700">Enable private nodes</span>
                    <p className="text-xs text-gray-400">
                      Nodes will not have external IP addresses.
                    </p>
                  </div>
                </label>

                {/* Logging */}
                <label className="flex items-center gap-3 cursor-pointer">
                  <input
                    type="checkbox"
                    checked={form.loggingEnabled}
                    onChange={(e) => set('loggingEnabled', e.target.checked)}
                    className="h-4 w-4 rounded border-gray-300 text-blue-600"
                  />
                  <div>
                    <span className="text-sm font-medium text-gray-700">Cloud Logging</span>
                    <p className="text-xs text-gray-400">
                      Send cluster and workload logs to Cloud Logging.
                    </p>
                  </div>
                </label>

                {/* Monitoring */}
                <label className="flex items-center gap-3 cursor-pointer">
                  <input
                    type="checkbox"
                    checked={form.monitoringEnabled}
                    onChange={(e) => set('monitoringEnabled', e.target.checked)}
                    className="h-4 w-4 rounded border-gray-300 text-blue-600"
                  />
                  <div>
                    <span className="text-sm font-medium text-gray-700">Cloud Monitoring</span>
                    <p className="text-xs text-gray-400">
                      Send cluster metrics to Cloud Monitoring.
                    </p>
                  </div>
                </label>
              </div>
            )}
          </section>

          {/* Submit */}
          <div className="flex items-center justify-end gap-3">
            <button
              type="button"
              onClick={() => navigate('/services/gke/clusters')}
              className="rounded-md border border-gray-300 bg-white px-4 py-2 text-sm text-gray-700 hover:bg-gray-50"
            >
              Cancel
            </button>
            <button
              type="submit"
              disabled={submitting}
              className="inline-flex items-center gap-2 rounded-md bg-blue-600 px-4 py-2 text-sm font-medium text-white hover:bg-blue-700 disabled:opacity-60 disabled:cursor-not-allowed"
            >
              {submitting && <Loader2 className="h-4 w-4 animate-spin" />}
              {submitting ? 'Creating…' : 'Create'}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}
