import { FormEvent, useCallback, useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import toast from 'react-hot-toast';
import { useProject } from '../contexts/ProjectContext';
import { listSecrets, createSecret, deleteSecret, Secret, Replication } from '../api/secretmanager';
import { Loader2, Plus, RefreshCw, Trash2, Eye, Key, Shield } from 'lucide-react';
import { Modal, ModalButton, ModalFooter } from '../components/Modal';

export default function SecretManagerDashboardPage() {
  const { currentProject } = useProject();
  const navigate = useNavigate();

  const [secrets, setSecrets] = useState<Secret[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [deleting, setDeleting] = useState<string | null>(null);

  // Create Secret modal
  const [showCreate, setShowCreate] = useState(false);
  const [creating, setCreating] = useState(false);
  const [secretId, setSecretId] = useState('');
  const [description, setDescription] = useState('');
  const [replicationType, setReplicationType] = useState<'automatic' | 'userManaged'>('automatic');
  const [replicationLocations, setReplicationLocations] = useState('us-central1');
  const [labels, setLabels] = useState('');

  const loadSecrets = useCallback(async () => {
    try {
      setLoading(true);
      const data = await listSecrets(currentProject);
      setSecrets(data);
      setError(null);
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : 'Failed to load secrets');
    } finally {
      setLoading(false);
    }
  }, [currentProject]);

  useEffect(() => {
    loadSecrets();
  }, [loadSecrets]);

  const parseLabels = (labelsStr: string): Record<string, string> => {
    if (!labelsStr.trim()) return {};
    try {
      const pairs = labelsStr.split(',').map((p) => p.trim());
      const labelsObj: Record<string, string> = {};
      pairs.forEach((pair) => {
        const [key, value] = pair.split('=').map((s) => s.trim());
        if (key && value) labelsObj[key] = value;
      });
      return labelsObj;
    } catch {
      return {};
    }
  };

  const resetForm = () => {
    setSecretId('');
    setDescription('');
    setReplicationType('automatic');
    setReplicationLocations('us-central1');
    setLabels('');
  };

  const handleCreate = async (e: FormEvent) => {
    e.preventDefault();
    const trimmedId = secretId.trim();
    if (!trimmedId) {
      toast.error('Secret ID is required');
      return;
    }

    setCreating(true);
    try {
      let replication: Replication;
      if (replicationType === 'automatic') {
        replication = { automatic: {} };
      } else {
        const locations = replicationLocations
          .split(',')
          .map((loc) => loc.trim())
          .filter(Boolean);
        replication = {
          userManaged: {
            replicas: locations.map((location) => ({ location })),
          },
        };
      }

      const labelsObj = parseLabels(labels);

      await createSecret({
        secretId: trimmedId,
        replication,
        labels: labelsObj,
        description,
      });

      toast.success(`Secret "${trimmedId}" created`);
      setShowCreate(false);
      resetForm();
      await loadSecrets();
    } catch (err: unknown) {
      toast.error(err instanceof Error ? err.message : 'Failed to create secret');
    } finally {
      setCreating(false);
    }
  };

  const handleDelete = async (secret: Secret) => {
    const secretId = secret.name.split('/').pop();
    if (!confirm(`Delete secret "${secretId}"? All versions will be destroyed.`)) return;

    setDeleting(secret.name);
    try {
      await deleteSecret(secret.name);
      toast.success('Secret deleted');
      await loadSecrets();
    } catch (err: unknown) {
      toast.error(err instanceof Error ? err.message : 'Failed to delete secret');
    } finally {
      setDeleting(null);
    }
  };

  const handleViewSecret = (secret: Secret) => {
    const secretId = secret.name.split('/').pop();
    navigate(`/services/secretmanager/secrets/${secretId}`);
  };

  const formatDate = (dateStr: string): string => {
    try {
      return new Date(dateStr).toLocaleString();
    } catch {
      return dateStr;
    }
  };

  const getReplicationText = (replication: Replication): string => {
    if (replication.automatic) {
      return 'Automatic';
    }
    if (replication.userManaged) {
      const count = replication.userManaged.replicas?.length || 0;
      return `User-managed (${count} ${count === 1 ? 'location' : 'locations'})`;
    }
    return 'Unknown';
  };

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <div className="bg-white border-b border-gray-200 px-6 py-4">
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-xl font-semibold text-gray-900 flex items-center gap-2">
              <Shield className="h-5 w-5 text-blue-600" />
              Secret Manager
            </h1>
            <p className="text-sm text-gray-500 mt-0.5">{currentProject}</p>
          </div>
          <div className="flex items-center gap-3">
            <button
              onClick={loadSecrets}
              className="inline-flex items-center gap-2 rounded-md border border-gray-300 bg-white px-3 py-1.5 text-sm text-gray-700 hover:bg-gray-50"
            >
              <RefreshCw className="h-4 w-4" />
              Refresh
            </button>
            <button
              onClick={() => setShowCreate(true)}
              className="inline-flex items-center gap-2 rounded-md bg-blue-600 px-4 py-1.5 text-sm font-medium text-white hover:bg-blue-700"
            >
              <Plus className="h-4 w-4" />
              Create Secret
            </button>
          </div>
        </div>
      </div>

      {/* Stats */}
      <div className="px-6 py-6">
        <div className="grid grid-cols-1 sm:grid-cols-3 gap-4 mb-6">
          <div className="bg-white rounded-lg border border-gray-200 p-4">
            <div className="flex items-center gap-3">
              <div className="p-2 bg-blue-100 rounded-lg">
                <Key className="h-5 w-5 text-blue-600" />
              </div>
              <div>
                <p className="text-xs text-gray-500 uppercase tracking-wide">Total Secrets</p>
                <p className="text-2xl font-bold text-gray-900">{secrets.length}</p>
              </div>
            </div>
          </div>
        </div>

        {/* Error */}
        {error && (
          <div className="mb-6 p-4 bg-red-50 border border-red-200 rounded-lg text-red-700">
            {error}
          </div>
        )}

        {/* Secrets Table */}
        <div className="bg-white rounded-lg border border-gray-200 overflow-hidden">
          {loading ? (
            <div className="flex items-center justify-center py-16">
              <Loader2 className="h-8 w-8 animate-spin text-blue-500" />
            </div>
          ) : secrets.length === 0 ? (
            <div className="text-center py-16">
              <Shield className="h-12 w-12 mx-auto text-gray-400 mb-3" />
              <p className="text-gray-600 font-medium">No secrets found</p>
              <p className="text-gray-400 text-sm mt-1">Create your first secret to get started.</p>
              <button
                onClick={() => setShowCreate(true)}
                className="mt-4 inline-flex items-center gap-2 rounded-md bg-blue-600 px-4 py-2 text-sm font-medium text-white hover:bg-blue-700"
              >
                <Plus className="h-4 w-4" />
                Create Secret
              </button>
            </div>
          ) : (
            <table className="w-full text-sm">
              <thead>
                <tr className="border-b border-gray-200 bg-gray-50 text-left">
                  <th className="px-4 py-3 font-medium text-gray-600">Name</th>
                  <th className="px-4 py-3 font-medium text-gray-600">Description</th>
                  <th className="px-4 py-3 font-medium text-gray-600">Replication</th>
                  <th className="px-4 py-3 font-medium text-gray-600">Labels</th>
                  <th className="px-4 py-3 font-medium text-gray-600">Created</th>
                  <th className="px-4 py-3 font-medium text-gray-600 text-right">Actions</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-gray-100">
                {secrets.map((secret) => {
                  const secretId = secret.name.split('/').pop() || secret.name;
                  return (
                    <tr key={secret.name} className="hover:bg-gray-50">
                      <td className="px-4 py-3">
                        <button
                          onClick={() => handleViewSecret(secret)}
                          className="font-medium text-blue-600 hover:text-blue-800 hover:underline"
                        >
                          {secretId}
                        </button>
                      </td>
                      <td className="px-4 py-3 text-gray-600 max-w-xs truncate">
                        {secret.description || '-'}
                      </td>
                      <td className="px-4 py-3 text-gray-600">
                        {getReplicationText(secret.replication)}
                      </td>
                      <td className="px-4 py-3 text-gray-600 text-xs">
                        {secret.labels && Object.keys(secret.labels).length > 0
                          ? Object.entries(secret.labels)
                              .map(([k, v]) => `${k}=${v}`)
                              .join(', ')
                          : '-'}
                      </td>
                      <td className="px-4 py-3 text-gray-600 text-xs">
                        {formatDate(secret.createTime)}
                      </td>
                      <td className="px-4 py-3 text-right">
                        <div className="flex items-center justify-end gap-1">
                          <button
                            onClick={() => handleViewSecret(secret)}
                            className="rounded p-1 text-gray-500 hover:bg-gray-100 hover:text-blue-600"
                            title="View versions"
                          >
                            <Eye className="h-4 w-4" />
                          </button>
                          <button
                            onClick={() => handleDelete(secret)}
                            disabled={deleting === secret.name}
                            className="rounded p-1 text-gray-500 hover:bg-gray-100 hover:text-red-600 disabled:opacity-50"
                            title="Delete secret"
                          >
                            {deleting === secret.name ? (
                              <Loader2 className="h-4 w-4 animate-spin" />
                            ) : (
                              <Trash2 className="h-4 w-4" />
                            )}
                          </button>
                        </div>
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          )}
        </div>
      </div>

      {/* Create Secret Modal */}
      <Modal
        isOpen={showCreate}
        onClose={() => setShowCreate(false)}
        title="Create Secret"
        description="Store sensitive data securely"
        size="lg"
      >
        <form onSubmit={handleCreate}>
          <div className="space-y-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Secret ID <span className="text-red-500">*</span>
              </label>
              <input
                type="text"
                value={secretId}
                onChange={(e) => setSecretId(e.target.value)}
                placeholder="my-api-key"
                className="w-full rounded-md border border-gray-300 px-3 py-2 text-sm"
                required
              />
              <p className="text-xs text-gray-500 mt-1">
                Unique identifier for the secret (lowercase, hyphens allowed)
              </p>
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Description (optional)
              </label>
              <textarea
                value={description}
                onChange={(e) => setDescription(e.target.value)}
                placeholder="API key for external service"
                rows={2}
                className="w-full rounded-md border border-gray-300 px-3 py-2 text-sm"
              />
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">Replication</label>
              <select
                value={replicationType}
                onChange={(e) => setReplicationType(e.target.value as 'automatic' | 'userManaged')}
                className="w-full rounded-md border border-gray-300 px-3 py-2 text-sm"
              >
                <option value="automatic">Automatic (Google-managed)</option>
                <option value="userManaged">User-managed</option>
              </select>
            </div>

            {replicationType === 'userManaged' && (
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Replication Locations
                </label>
                <input
                  type="text"
                  value={replicationLocations}
                  onChange={(e) => setReplicationLocations(e.target.value)}
                  placeholder="us-central1, us-east1"
                  className="w-full rounded-md border border-gray-300 px-3 py-2 text-sm"
                />
                <p className="text-xs text-gray-500 mt-1">Comma-separated region names</p>
              </div>
            )}

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Labels (optional)
              </label>
              <input
                type="text"
                value={labels}
                onChange={(e) => setLabels(e.target.value)}
                placeholder="env=prod, team=backend"
                className="w-full rounded-md border border-gray-300 px-3 py-2 text-sm"
              />
              <p className="text-xs text-gray-500 mt-1">Comma-separated key=value pairs</p>
            </div>
          </div>

          <ModalFooter>
            <ModalButton variant="secondary" onClick={() => setShowCreate(false)}>
              Cancel
            </ModalButton>
            <ModalButton type="submit" disabled={creating}>
              {creating && <Loader2 className="h-4 w-4 animate-spin" />}
              Create
            </ModalButton>
          </ModalFooter>
        </form>
      </Modal>
    </div>
  );
}
