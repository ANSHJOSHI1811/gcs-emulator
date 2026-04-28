import { FormEvent, useCallback, useEffect, useMemo, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import toast from 'react-hot-toast';
import { useProject } from '../contexts/ProjectContext';
import { deleteRunService, deployRunService, listRunServices, RunService } from '../api/run';
import { Loader2, Plus, RefreshCw, Trash2, ExternalLink, Eye } from 'lucide-react';
import { Modal, ModalButton, ModalFooter } from '../components/Modal';

interface EnvRow {
  name: string;
  value: string;
}

const DEFAULT_REGION = 'us-central1';
const REGIONS = ['us-central1', 'us-east1', 'us-west1'];

export default function CloudRunDashboardPage() {
  const { currentProject } = useProject();
  const navigate = useNavigate();

  const [location, setLocation] = useState(DEFAULT_REGION);
  const [services, setServices] = useState<RunService[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [showDeploy, setShowDeploy] = useState(false);
  const [deploying, setDeploying] = useState(false);
  const [deleting, setDeleting] = useState<string | null>(null);

  const [serviceId, setServiceId] = useState('');
  const [image, setImage] = useState('nginx:alpine');
  const [containerPort, setContainerPort] = useState(8080);
  const [envRows, setEnvRows] = useState<EnvRow[]>([{ name: '', value: '' }]);

  const loadServices = useCallback(async () => {
    try {
      setLoading(true);
      const data = await listRunServices(location, currentProject);
      setServices(data);
      setError(null);
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : 'Failed to load Cloud Run services');
    } finally {
      setLoading(false);
    }
  }, [location, currentProject]);

  useEffect(() => {
    loadServices();
  }, [loadServices]);

  const totalRevisions = useMemo(
    () => services.reduce((sum, s) => sum + s.revisions.length, 0),
    [services]
  );

  const activeTrafficSummary = (s: RunService) => {
    if (!s.traffic.length) return 'No traffic config';
    return s.traffic
      .map((t) => `${t.revision || (t.latestRevision ? 'latest' : 'unknown')}: ${t.percent}%`)
      .join(' | ');
  };

  const resetDeployForm = () => {
    setServiceId('');
    setImage('nginx:alpine');
    setContainerPort(8080);
    setEnvRows([{ name: '', value: '' }]);
  };

  const handleAddEnvRow = () => {
    setEnvRows((prev) => [...prev, { name: '', value: '' }]);
  };

  const handleEnvChange = (idx: number, field: keyof EnvRow, value: string) => {
    setEnvRows((prev) => prev.map((row, i) => (i === idx ? { ...row, [field]: value } : row)));
  };

  const handleRemoveEnvRow = (idx: number) => {
    setEnvRows((prev) => (prev.length <= 1 ? prev : prev.filter((_, i) => i !== idx)));
  };

  const handleDeploy = async (e: FormEvent) => {
    e.preventDefault();
    const trimmedServiceId = serviceId.trim();
    if (!trimmedServiceId) {
      toast.error('Service name is required');
      return;
    }
    if (!image.trim()) {
      toast.error('Container image is required');
      return;
    }
    if (!Number.isInteger(containerPort) || containerPort < 1 || containerPort > 65535) {
      toast.error('Container port must be between 1 and 65535');
      return;
    }

    const env = envRows
      .map((row) => ({ name: row.name.trim(), value: row.value }))
      .filter((row) => row.name.length > 0);

    setDeploying(true);
    try {
      await deployRunService(location, trimmedServiceId, {
        image: image.trim(),
        containerPort,
        env,
      });
      toast.success(`Service "${trimmedServiceId}" deployed`);
      setShowDeploy(false);
      resetDeployForm();
      await loadServices();
    } catch (err: unknown) {
      toast.error(err instanceof Error ? err.message : 'Deploy failed');
    } finally {
      setDeploying(false);
    }
  };

  const handleDelete = async (service: RunService) => {
    if (!confirm(`Delete Cloud Run service "${service.serviceId}"?`)) return;
    setDeleting(service.serviceId);
    try {
      await deleteRunService(location, service.serviceId);
      toast.success(`Deleted ${service.serviceId}`);
      await loadServices();
    } catch (err: unknown) {
      toast.error(err instanceof Error ? err.message : 'Delete failed');
    } finally {
      setDeleting(null);
    }
  };

  return (
    <div className="min-h-screen bg-gray-50">
      <div className="bg-white border-b border-gray-200 px-6 py-4">
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-xl font-semibold text-gray-900">Cloud Run</h1>
            <p className="text-sm text-gray-500 mt-0.5">{currentProject}</p>
          </div>
          <div className="flex items-center gap-3">
            <select
              value={location}
              onChange={(e) => setLocation(e.target.value)}
              className="rounded-md border border-gray-300 bg-white px-3 py-1.5 text-sm text-gray-700"
            >
              {REGIONS.map((region) => (
                <option key={region} value={region}>
                  {region}
                </option>
              ))}
            </select>
            <button
              onClick={loadServices}
              className="inline-flex items-center gap-2 rounded-md border border-gray-300 bg-white px-3 py-1.5 text-sm text-gray-700 hover:bg-gray-50"
            >
              <RefreshCw className="h-4 w-4" />
              Refresh
            </button>
            <button
              onClick={() => setShowDeploy(true)}
              className="inline-flex items-center gap-2 rounded-md bg-blue-600 px-4 py-1.5 text-sm font-medium text-white hover:bg-blue-700"
            >
              <Plus className="h-4 w-4" />
              Deploy
            </button>
          </div>
        </div>
      </div>

      <div className="px-6 py-6 space-y-6">
        <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
          <div className="bg-white rounded-lg border border-gray-200 p-4">
            <p className="text-xs text-gray-500 uppercase tracking-wide">Services</p>
            <p className="text-3xl font-bold mt-1 text-gray-900">{services.length}</p>
          </div>
          <div className="bg-white rounded-lg border border-gray-200 p-4">
            <p className="text-xs text-gray-500 uppercase tracking-wide">Revisions</p>
            <p className="text-3xl font-bold mt-1 text-gray-900">{totalRevisions}</p>
          </div>
          <div className="bg-white rounded-lg border border-gray-200 p-4">
            <p className="text-xs text-gray-500 uppercase tracking-wide">Region</p>
            <p className="text-3xl font-bold mt-1 text-blue-700">{location}</p>
          </div>
        </div>

        {error && (
          <div className="rounded-md bg-red-50 border border-red-200 p-4 text-sm text-red-700">{error}</div>
        )}

        <div className="bg-white rounded-lg border border-gray-200 overflow-hidden">
          {loading ? (
            <div className="flex items-center justify-center py-16">
              <Loader2 className="h-8 w-8 animate-spin text-blue-500" />
            </div>
          ) : services.length === 0 ? (
            <div className="text-center py-16">
              <p className="text-gray-600 font-medium">No Cloud Run services found</p>
              <p className="text-gray-400 text-sm mt-1">Deploy your first service to begin.</p>
            </div>
          ) : (
            <table className="w-full text-sm">
              <thead>
                <tr className="border-b border-gray-200 bg-gray-50 text-left">
                  <th className="px-4 py-3 font-medium text-gray-600">Service</th>
                  <th className="px-4 py-3 font-medium text-gray-600">Latest Revision</th>
                  <th className="px-4 py-3 font-medium text-gray-600">Traffic</th>
                  <th className="px-4 py-3 font-medium text-gray-600">Simulated URL</th>
                  <th className="px-4 py-3 font-medium text-gray-600">Local URL</th>
                  <th className="px-4 py-3 font-medium text-gray-600">Actions</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-gray-100">
                {services.map((service) => (
                  <tr key={service.name} className="hover:bg-gray-50">
                    <td className="px-4 py-3 font-medium text-gray-900">{service.serviceId}</td>
                    <td className="px-4 py-3 text-gray-600">{service.latestReadyRevision || '—'}</td>
                    <td className="px-4 py-3 text-gray-600 max-w-[320px] truncate" title={activeTrafficSummary(service)}>
                      {activeTrafficSummary(service)}
                    </td>
                    <td className="px-4 py-3 text-blue-700 break-all">{service.simulatedUrl || '—'}</td>
                    <td className="px-4 py-3 text-blue-700 break-all">{service.activeLocalUrl || '—'}</td>
                    <td className="px-4 py-3">
                      <div className="flex items-center gap-1">
                        <button
                          title="View service"
                          onClick={() => navigate(`/services/cloud-run/services/${service.serviceId}?location=${location}`)}
                          className="rounded p-1 text-gray-500 hover:bg-gray-100 hover:text-blue-600"
                        >
                          <Eye className="h-4 w-4" />
                        </button>
                        {!!service.activeLocalUrl && (
                          <a
                            href={service.activeLocalUrl}
                            target="_blank"
                            rel="noreferrer"
                            title="Open local URL"
                            className="rounded p-1 text-gray-500 hover:bg-gray-100 hover:text-blue-600"
                          >
                            <ExternalLink className="h-4 w-4" />
                          </a>
                        )}
                        <button
                          title="Delete service"
                          onClick={() => handleDelete(service)}
                          disabled={deleting === service.serviceId}
                          className="rounded p-1 text-gray-500 hover:bg-gray-100 hover:text-red-600 disabled:opacity-50"
                        >
                          {deleting === service.serviceId ? (
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

      <Modal
        isOpen={showDeploy}
        onClose={() => {
          if (!deploying) {
            setShowDeploy(false);
            resetDeployForm();
          }
        }}
        title="Deploy Cloud Run Service"
        description="Create a new service revision from a container image"
        size="lg"
      >
        <form onSubmit={handleDeploy} className="space-y-4">
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">Service name</label>
              <input
                value={serviceId}
                onChange={(e) => setServiceId(e.target.value)}
                className="w-full rounded-md border border-gray-300 px-3 py-2 text-sm"
                placeholder="hello-service"
                required
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">Container port</label>
              <input
                type="number"
                min={1}
                max={65535}
                value={containerPort}
                onChange={(e) => setContainerPort(parseInt(e.target.value, 10) || 8080)}
                className="w-full rounded-md border border-gray-300 px-3 py-2 text-sm"
              />
            </div>
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Image</label>
            <input
              value={image}
              onChange={(e) => setImage(e.target.value)}
              className="w-full rounded-md border border-gray-300 px-3 py-2 text-sm"
              placeholder="nginx:alpine"
              required
            />
          </div>

          <div>
            <div className="flex items-center justify-between mb-2">
              <label className="block text-sm font-medium text-gray-700">Environment variables</label>
              <button
                type="button"
                onClick={handleAddEnvRow}
                className="text-xs text-blue-600 hover:underline"
              >
                + Add variable
              </button>
            </div>
            <div className="space-y-2">
              {envRows.map((row, idx) => (
                <div key={idx} className="grid grid-cols-1 md:grid-cols-[1fr_1fr_auto] gap-2">
                  <input
                    value={row.name}
                    onChange={(e) => handleEnvChange(idx, 'name', e.target.value)}
                    className="rounded-md border border-gray-300 px-3 py-2 text-sm"
                    placeholder="NAME"
                  />
                  <input
                    value={row.value}
                    onChange={(e) => handleEnvChange(idx, 'value', e.target.value)}
                    className="rounded-md border border-gray-300 px-3 py-2 text-sm"
                    placeholder="VALUE"
                  />
                  <button
                    type="button"
                    onClick={() => handleRemoveEnvRow(idx)}
                    className="rounded-md border border-gray-300 px-3 py-2 text-sm text-gray-600 hover:bg-gray-50"
                  >
                    Remove
                  </button>
                </div>
              ))}
            </div>
          </div>

          <ModalFooter>
            <ModalButton type="button" onClick={() => setShowDeploy(false)} disabled={deploying}>
              Cancel
            </ModalButton>
            <ModalButton type="submit" variant="primary" loading={deploying}>
              Deploy
            </ModalButton>
          </ModalFooter>
        </form>
      </Modal>
    </div>
  );
}
