import { FormEvent, useCallback, useEffect, useState } from 'react';
import toast from 'react-hot-toast';
import { useProject } from '../contexts/ProjectContext';
import {
  ArtifactRepository,
  createRepository,
  deleteRepository,
  ensureRegistry,
  listRepositories,
  RegistryStatus,
} from '../api/artifacts';
import { Loader2, Plus, RefreshCw, Trash2, Wrench } from 'lucide-react';
import { Modal, ModalButton, ModalFooter } from '../components/Modal';

const DEFAULT_REGION = 'us-central1';
const REGIONS = ['us-central1', 'us-east1', 'us-west1'];

export default function ArtifactRegistryPage() {
  const { currentProject } = useProject();

  const [location, setLocation] = useState(DEFAULT_REGION);
  const [repositories, setRepositories] = useState<ArtifactRepository[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [creating, setCreating] = useState(false);
  const [deleting, setDeleting] = useState<string | null>(null);
  const [ensuring, setEnsuring] = useState<string | null>(null);

  const [showCreate, setShowCreate] = useState(false);
  const [repoId, setRepoId] = useState('');
  const [format, setFormat] = useState('DOCKER');
  const [description, setDescription] = useState('');

  const [registryStatus, setRegistryStatus] = useState<RegistryStatus | null>(null);

  const loadRepositories = useCallback(async () => {
    try {
      setLoading(true);
      const data = await listRepositories(location, currentProject);
      setRepositories(data);
      setError(null);
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : 'Failed to load repositories');
    } finally {
      setLoading(false);
    }
  }, [location, currentProject]);

  useEffect(() => {
    loadRepositories();
  }, [loadRepositories]);

  const resetCreateForm = () => {
    setRepoId('');
    setFormat('DOCKER');
    setDescription('');
  };

  const handleCreate = async (e: FormEvent) => {
    e.preventDefault();
    const trimmedId = repoId.trim();
    if (!trimmedId) {
      toast.error('Repository ID is required');
      return;
    }

    setCreating(true);
    try {
      await createRepository(location, trimmedId, { format, description });
      toast.success(`Repository "${trimmedId}" created`);
      setShowCreate(false);
      resetCreateForm();
      await loadRepositories();
    } catch (err: unknown) {
      toast.error(err instanceof Error ? err.message : 'Create repository failed');
    } finally {
      setCreating(false);
    }
  };

  const handleDelete = async (repo: ArtifactRepository) => {
    if (!confirm(`Delete repository "${repo.repositoryId}"?`)) return;
    setDeleting(repo.repositoryId);
    try {
      await deleteRepository(location, repo.repositoryId);
      toast.success(`Repository "${repo.repositoryId}" deleted`);
      await loadRepositories();
    } catch (err: unknown) {
      toast.error(err instanceof Error ? err.message : 'Delete repository failed');
    } finally {
      setDeleting(null);
    }
  };

  const handleEnsureRegistry = async (repo: ArtifactRepository) => {
    setEnsuring(repo.repositoryId);
    try {
      const status = await ensureRegistry(location, repo.repositoryId);
      setRegistryStatus(status);
      toast.success(`Registry ensured for "${repo.repositoryId}"`);
    } catch (err: unknown) {
      toast.error(err instanceof Error ? err.message : 'Ensure registry failed');
    } finally {
      setEnsuring(null);
    }
  };

  return (
    <div className="min-h-screen bg-gray-50">
      <div className="bg-white border-b border-gray-200 px-6 py-4">
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-xl font-semibold text-gray-900">Artifact Registry</h1>
            <p className="text-sm text-gray-500 mt-0.5">{currentProject}</p>
          </div>
          <div className="flex items-center gap-3">
            <select
              value={location}
              onChange={(e) => setLocation(e.target.value)}
              className="rounded-md border border-gray-300 bg-white px-3 py-1.5 text-sm text-gray-700"
            >
              {REGIONS.map((region) => (
                <option key={region} value={region}>{region}</option>
              ))}
            </select>
            <button
              onClick={loadRepositories}
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
              Create
            </button>
          </div>
        </div>
      </div>

      <div className="px-6 py-6 space-y-6">
        {error && (
          <div className="rounded-md bg-red-50 border border-red-200 p-4 text-sm text-red-700">{error}</div>
        )}

        {registryStatus && (
          <div className="rounded-lg border border-blue-200 bg-blue-50 p-4">
            <h2 className="text-sm font-semibold text-blue-900 mb-2">Registry Status</h2>
            <p className="text-sm text-blue-800">Endpoint: {registryStatus.registry.endpoint}</p>
            <p className="text-sm text-blue-800">Status: {registryStatus.registry.status}</p>
            <p className="text-xs text-blue-700 mt-2 font-mono break-all">{registryStatus.pushExample}</p>
          </div>
        )}

        <div className="bg-white rounded-lg border border-gray-200 overflow-hidden">
          {loading ? (
            <div className="flex items-center justify-center py-16">
              <Loader2 className="h-8 w-8 animate-spin text-blue-500" />
            </div>
          ) : repositories.length === 0 ? (
            <div className="text-center py-16">
              <p className="text-gray-600 font-medium">No repositories found</p>
              <p className="text-gray-400 text-sm mt-1">Create your first Artifact Registry repository.</p>
            </div>
          ) : (
            <table className="w-full text-sm">
              <thead>
                <tr className="border-b border-gray-200 bg-gray-50 text-left">
                  <th className="px-4 py-3 font-medium text-gray-600">Name</th>
                  <th className="px-4 py-3 font-medium text-gray-600">Format</th>
                  <th className="px-4 py-3 font-medium text-gray-600">Location</th>
                  <th className="px-4 py-3 font-medium text-gray-600">Registry Host</th>
                  <th className="px-4 py-3 font-medium text-gray-600">Docker Prefix</th>
                  <th className="px-4 py-3 font-medium text-gray-600">Created</th>
                  <th className="px-4 py-3 font-medium text-gray-600">Actions</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-gray-100">
                {repositories.map((repo) => (
                  <tr key={repo.name} className="hover:bg-gray-50">
                    <td className="px-4 py-3 font-medium text-gray-900">{repo.repositoryId}</td>
                    <td className="px-4 py-3 text-gray-600">{repo.format}</td>
                    <td className="px-4 py-3 text-gray-600">{repo.location}</td>
                    <td className="px-4 py-3 text-gray-600">{repo.registryHost}</td>
                    <td className="px-4 py-3 text-gray-600 break-all">{repo.dockerRepositoryPrefix}</td>
                    <td className="px-4 py-3 text-gray-600">
                      {repo.createTime ? new Date(repo.createTime).toLocaleString() : '—'}
                    </td>
                    <td className="px-4 py-3">
                      <div className="flex items-center gap-1">
                        <button
                          title="Ensure local registry"
                          onClick={() => handleEnsureRegistry(repo)}
                          disabled={ensuring === repo.repositoryId}
                          className="rounded p-1 text-gray-500 hover:bg-gray-100 hover:text-blue-600 disabled:opacity-50"
                        >
                          {ensuring === repo.repositoryId ? (
                            <Loader2 className="h-4 w-4 animate-spin" />
                          ) : (
                            <Wrench className="h-4 w-4" />
                          )}
                        </button>
                        <button
                          title="Delete repository"
                          onClick={() => handleDelete(repo)}
                          disabled={deleting === repo.repositoryId}
                          className="rounded p-1 text-gray-500 hover:bg-gray-100 hover:text-red-600 disabled:opacity-50"
                        >
                          {deleting === repo.repositoryId ? (
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
        isOpen={showCreate}
        onClose={() => {
          if (!creating) {
            setShowCreate(false);
            resetCreateForm();
          }
        }}
        title="Create Artifact Repository"
        description="Create a repository for container images"
      >
        <form onSubmit={handleCreate} className="space-y-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Repository ID</label>
            <input
              value={repoId}
              onChange={(e) => setRepoId(e.target.value)}
              className="w-full rounded-md border border-gray-300 px-3 py-2 text-sm"
              placeholder="demo-repo"
              required
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Format</label>
            <select
              value={format}
              onChange={(e) => setFormat(e.target.value)}
              className="w-full rounded-md border border-gray-300 px-3 py-2 text-sm"
            >
              <option value="DOCKER">DOCKER</option>
            </select>
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Description (optional)</label>
            <textarea
              value={description}
              onChange={(e) => setDescription(e.target.value)}
              className="w-full rounded-md border border-gray-300 px-3 py-2 text-sm"
              rows={3}
            />
          </div>

          <ModalFooter>
            <ModalButton type="button" onClick={() => setShowCreate(false)} disabled={creating}>
              Cancel
            </ModalButton>
            <ModalButton type="submit" variant="primary" loading={creating}>
              Create Repository
            </ModalButton>
          </ModalFooter>
        </form>
      </Modal>
    </div>
  );
}
