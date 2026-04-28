import { useState, useEffect, useCallback } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { useProject } from '../contexts/ProjectContext';
import {
  getSecret,
  listVersions,
  addSecretVersion,
  accessSecretVersion,
  enableSecretVersion,
  disableSecretVersion,
  destroySecretVersion,
  generatePassword,
  Secret,
  SecretVersion,
} from '../api/secretmanager';
import toast from 'react-hot-toast';
import {
  ArrowLeft,
  Plus,
  RefreshCw,
  Eye,
  EyeOff,
  Power,
  PowerOff,
  Trash2,
  Loader2,
  Copy,
  Key,
  CheckCircle2,
  XCircle,
  AlertCircle,
} from 'lucide-react';

export default function SecretDetailPage() {
  const { secretId } = useParams<{ secretId: string }>();
  const navigate = useNavigate();
  const { currentProject } = useProject();

  const [secret, setSecret] = useState<Secret | null>(null);
  const [versions, setVersions] = useState<SecretVersion[]>([]);
  const [loading, setLoading] = useState(true);
  const [versionsLoading, setVersionsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // Modals
  const [showAddVersionModal, setShowAddVersionModal] = useState(false);
  const [showViewSecretModal, setShowViewSecretModal] = useState(false);
  const [showGeneratePasswordModal, setShowGeneratePasswordModal] = useState(false);

  // Form states
  const [newVersionData, setNewVersionData] = useState('');
  const [addingVersion, setAddingVersion] = useState(false);
  const [viewingVersion, setViewingVersion] = useState<string | null>(null);
  const [secretData, setSecretData] = useState('');
  const [showSecretValue, setShowSecretValue] = useState(false);
  const [generatedPassword, setGeneratedPassword] = useState('');

  // Action states
  const [actioningVersion, setActioningVersion] = useState<string | null>(null);

  const fetchSecret = useCallback(async () => {
    if (!currentProject || !secretId) return;

    try {
      setLoading(true);
      const secretName = `projects/${currentProject}/secrets/${secretId}`;
      const data = await getSecret(secretName);
      setSecret(data);
      setError(null);
    } catch (err: unknown) {
      const message = err instanceof Error ? err.message : 'Failed to load secret';
      setError(message);
      toast.error(message);
    } finally {
      setLoading(false);
    }
  }, [currentProject, secretId]);

  const fetchVersions = useCallback(async () => {
    if (!currentProject || !secretId) return;

    try {
      setVersionsLoading(true);
      const secretName = `projects/${currentProject}/secrets/${secretId}`;
      const data = await listVersions(secretName);
      setVersions(data);
    } catch (err: unknown) {
      const message = err instanceof Error ? err.message : 'Failed to load versions';
      toast.error(message);
    } finally {
      setVersionsLoading(false);
    }
  }, [currentProject, secretId]);

  useEffect(() => {
    fetchSecret();
    fetchVersions();
  }, [fetchSecret, fetchVersions]);

  async function handleAddVersion() {
    if (!currentProject || !secretId || !newVersionData.trim()) {
      toast.error('Secret data is required');
      return;
    }

    setAddingVersion(true);
    try {
      const secretName = `projects/${currentProject}/secrets/${secretId}`;
      await addSecretVersion(secretName, newVersionData);
      toast.success('Version added successfully');
      setShowAddVersionModal(false);
      setNewVersionData('');
      await fetchVersions();
    } catch (err: unknown) {
      toast.error(err instanceof Error ? err.message : 'Failed to add version');
    } finally {
      setAddingVersion(false);
    }
  }

  async function handleViewSecret(version: string) {
    if (!currentProject || !secretId) return;

    setViewingVersion(version);
    setShowViewSecretModal(true);
    setShowSecretValue(false);

    try {
      const versionName = `projects/${currentProject}/secrets/${secretId}/versions/${version}`;
      const data = await accessSecretVersion(versionName);
      setSecretData(data.payload.data);
    } catch (err: unknown) {
      toast.error(err instanceof Error ? err.message : 'Failed to access secret');
      setShowViewSecretModal(false);
    } finally {
      setViewingVersion(null);
    }
  }

  async function handleEnableVersion(version: string) {
    if (!currentProject || !secretId) return;

    setActioningVersion(version);
    try {
      const versionName = `projects/${currentProject}/secrets/${secretId}/versions/${version}`;
      await enableSecretVersion(versionName);
      toast.success('Version enabled');
      await fetchVersions();
    } catch (err: unknown) {
      toast.error(err instanceof Error ? err.message : 'Failed to enable version');
    } finally {
      setActioningVersion(null);
    }
  }

  async function handleDisableVersion(version: string) {
    if (!currentProject || !secretId) return;

    setActioningVersion(version);
    try {
      const versionName = `projects/${currentProject}/secrets/${secretId}/versions/${version}`;
      await disableSecretVersion(versionName);
      toast.success('Version disabled');
      await fetchVersions();
    } catch (err: unknown) {
      toast.error(err instanceof Error ? err.message : 'Failed to disable version');
    } finally {
      setActioningVersion(null);
    }
  }

  async function handleDestroyVersion(version: string) {
    if (!confirm(`Permanently destroy version ${version}? This cannot be undone.`)) {
      return;
    }

    if (!currentProject || !secretId) return;

    setActioningVersion(version);
    try {
      const versionName = `projects/${currentProject}/secrets/${secretId}/versions/${version}`;
      await destroySecretVersion(versionName);
      toast.success('Version destroyed');
      await fetchVersions();
    } catch (err: unknown) {
      toast.error(err instanceof Error ? err.message : 'Failed to destroy version');
    } finally {
      setActioningVersion(null);
    }
  }

  async function handleGeneratePassword() {
    try {
      const password = await generatePassword({
        length: 16,
        includeUppercase: true,
        includeLowercase: true,
        includeDigits: true,
        includeSymbols: true,
        excludeAmbiguous: true,
      });
      setGeneratedPassword(password);
      setShowGeneratePasswordModal(true);
    } catch (err: unknown) {
      toast.error(err instanceof Error ? err.message : 'Failed to generate password');
    }
  }

  function copyToClipboard(text: string) {
    navigator.clipboard.writeText(text);
    toast.success('Copied to clipboard');
  }

  function getVersionState(version: SecretVersion) {
    switch (version.state) {
      case 'ENABLED':
        return (
          <span className="inline-flex items-center gap-1 rounded-full bg-green-100 px-2.5 py-0.5 text-xs font-medium text-green-800">
            <CheckCircle2 className="h-3 w-3" />
            Enabled
          </span>
        );
      case 'DISABLED':
        return (
          <span className="inline-flex items-center gap-1 rounded-full bg-gray-100 px-2.5 py-0.5 text-xs font-medium text-gray-800">
            <XCircle className="h-3 w-3" />
            Disabled
          </span>
        );
      case 'DESTROYED':
        return (
          <span className="inline-flex items-center gap-1 rounded-full bg-red-100 px-2.5 py-0.5 text-xs font-medium text-red-800">
            <AlertCircle className="h-3 w-3" />
            Destroyed
          </span>
        );
      default:
        return (
          <span className="rounded-full bg-gray-100 px-2.5 py-0.5 text-xs font-medium text-gray-800">
            {version.state}
          </span>
        );
    }
  }

  function getVersionNumber(versionName: string): string {
    const parts = versionName.split('/');
    return parts[parts.length - 1] || versionName;
  }

  if (loading) {
    return (
      <div className="flex h-screen items-center justify-center bg-gray-50">
        <Loader2 className="h-8 w-8 animate-spin text-blue-500" />
      </div>
    );
  }

  if (error || !secret) {
    return (
      <div className="min-h-screen bg-gray-50 p-6">
        <div className="mx-auto max-w-7xl">
          <button
            onClick={() => navigate('/services/secretmanager')}
            className="mb-4 inline-flex items-center gap-2 text-sm text-gray-600 hover:text-gray-900"
          >
            <ArrowLeft className="h-4 w-4" />
            Back to Secrets
          </button>
          <div className="rounded-lg border border-red-200 bg-red-50 p-4 text-red-700">
            {error || 'Secret not found'}
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <div className="border-b border-gray-200 bg-white px-6 py-4">
        <div className="mx-auto max-w-7xl">
          <button
            onClick={() => navigate('/services/secretmanager')}
            className="mb-3 inline-flex items-center gap-2 text-sm text-gray-600 hover:text-gray-900"
          >
            <ArrowLeft className="h-4 w-4" />
            Back to Secrets
          </button>
          <div className="flex items-start justify-between">
            <div>
              <h1 className="text-xl font-semibold text-gray-900">{secretId}</h1>
              <p className="mt-1 text-sm text-gray-500">{secret.description || 'No description'}</p>
              {secret.labels && Object.keys(secret.labels).length > 0 && (
                <div className="mt-2 flex flex-wrap gap-2">
                  {Object.entries(secret.labels).map(([key, value]) => (
                    <span
                      key={key}
                      className="inline-flex items-center rounded-md bg-blue-50 px-2 py-1 text-xs font-medium text-blue-700"
                    >
                      {key}: {value}
                    </span>
                  ))}
                </div>
              )}
            </div>
            <div className="flex items-center gap-3">
              <button
                onClick={handleGeneratePassword}
                className="inline-flex items-center gap-2 rounded-md border border-gray-300 bg-white px-3 py-1.5 text-sm text-gray-700 hover:bg-gray-50"
              >
                <Key className="h-4 w-4" />
                Generate Password
              </button>
              <button
                onClick={() => setShowAddVersionModal(true)}
                className="inline-flex items-center gap-2 rounded-md bg-blue-600 px-4 py-1.5 text-sm font-medium text-white hover:bg-blue-700"
              >
                <Plus className="h-4 w-4" />
                Add Version
              </button>
            </div>
          </div>
        </div>
      </div>

      {/* Content */}
      <div className="mx-auto max-w-7xl px-6 py-6">
        {/* Metadata */}
        <div className="mb-6 grid grid-cols-1 gap-4 sm:grid-cols-3">
          <div className="rounded-lg border border-gray-200 bg-white p-4">
            <p className="text-xs text-gray-500 uppercase tracking-wide">Created</p>
            <p className="mt-1 text-sm font-medium text-gray-900">
              {new Date(secret.createTime).toLocaleString()}
            </p>
          </div>
          <div className="rounded-lg border border-gray-200 bg-white p-4">
            <p className="text-xs text-gray-500 uppercase tracking-wide">Replication</p>
            <p className="mt-1 text-sm font-medium text-gray-900">
              {secret.replication.automatic ? 'Automatic' : 'User Managed'}
            </p>
          </div>
          <div className="rounded-lg border border-gray-200 bg-white p-4">
            <p className="text-xs text-gray-500 uppercase tracking-wide">Versions</p>
            <p className="mt-1 text-sm font-medium text-gray-900">{versions.length}</p>
          </div>
        </div>

        {/* Versions Table */}
        <div className="rounded-lg border border-gray-200 bg-white overflow-hidden">
          <div className="flex items-center justify-between border-b border-gray-200 bg-gray-50 px-4 py-3">
            <h2 className="text-sm font-medium text-gray-900">Secret Versions</h2>
            <button
              onClick={fetchVersions}
              disabled={versionsLoading}
              className="inline-flex items-center gap-2 text-sm text-gray-600 hover:text-gray-900 disabled:opacity-50"
            >
              <RefreshCw className={`h-4 w-4 ${versionsLoading ? 'animate-spin' : ''}`} />
              Refresh
            </button>
          </div>

          {versionsLoading ? (
            <div className="flex items-center justify-center py-12">
              <Loader2 className="h-6 w-6 animate-spin text-blue-500" />
            </div>
          ) : versions.length === 0 ? (
            <div className="py-12 text-center">
              <p className="text-sm font-medium text-gray-600">No versions yet</p>
              <p className="mt-1 text-xs text-gray-400">Add your first secret version to get started</p>
            </div>
          ) : (
            <table className="w-full text-sm">
              <thead>
                <tr className="border-b border-gray-200 bg-gray-50 text-left">
                  <th className="px-4 py-3 font-medium text-gray-600">Version</th>
                  <th className="px-4 py-3 font-medium text-gray-600">State</th>
                  <th className="px-4 py-3 font-medium text-gray-600">Created</th>
                  <th className="px-4 py-3 font-medium text-gray-600">Actions</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-gray-100">
                {versions.map((version) => {
                  const versionNum = getVersionNumber(version.name);
                  const isActioning = actioningVersion === versionNum;

                  return (
                    <tr key={version.name} className="hover:bg-gray-50">
                      <td className="px-4 py-3 font-medium text-gray-900">{versionNum}</td>
                      <td className="px-4 py-3">{getVersionState(version)}</td>
                      <td className="px-4 py-3 text-gray-600">
                        {new Date(version.createTime).toLocaleString()}
                      </td>
                      <td className="px-4 py-3">
                        <div className="flex items-center gap-2">
                          {version.state === 'ENABLED' && (
                            <>
                              <button
                                onClick={() => handleViewSecret(versionNum)}
                                disabled={isActioning}
                                className="rounded p-1 text-gray-500 hover:bg-blue-50 hover:text-blue-600 disabled:opacity-50"
                                title="View secret"
                              >
                                <Eye className="h-4 w-4" />
                              </button>
                              <button
                                onClick={() => handleDisableVersion(versionNum)}
                                disabled={isActioning}
                                className="rounded p-1 text-gray-500 hover:bg-gray-100 hover:text-gray-700 disabled:opacity-50"
                                title="Disable"
                              >
                                {isActioning ? (
                                  <Loader2 className="h-4 w-4 animate-spin" />
                                ) : (
                                  <PowerOff className="h-4 w-4" />
                                )}
                              </button>
                            </>
                          )}
                          {version.state === 'DISABLED' && (
                            <>
                              <button
                                onClick={() => handleEnableVersion(versionNum)}
                                disabled={isActioning}
                                className="rounded p-1 text-gray-500 hover:bg-green-50 hover:text-green-600 disabled:opacity-50"
                                title="Enable"
                              >
                                {isActioning ? (
                                  <Loader2 className="h-4 w-4 animate-spin" />
                                ) : (
                                  <Power className="h-4 w-4" />
                                )}
                              </button>
                              <button
                                onClick={() => handleDestroyVersion(versionNum)}
                                disabled={isActioning}
                                className="rounded p-1 text-gray-500 hover:bg-red-50 hover:text-red-600 disabled:opacity-50"
                                title="Destroy"
                              >
                                {isActioning ? (
                                  <Loader2 className="h-4 w-4 animate-spin" />
                                ) : (
                                  <Trash2 className="h-4 w-4" />
                                )}
                              </button>
                            </>
                          )}
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

      {/* Add Version Modal */}
      {showAddVersionModal && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black bg-opacity-50 p-4">
          <div className="w-full max-w-lg rounded-lg bg-white p-6 shadow-xl">
            <h3 className="text-lg font-semibold text-gray-900">Add Secret Version</h3>
            <p className="mt-1 text-sm text-gray-500">Add a new version to this secret</p>

            <div className="mt-4">
              <label className="block text-sm font-medium text-gray-700">Secret Data</label>
              <textarea
                value={newVersionData}
                onChange={(e) => setNewVersionData(e.target.value)}
                rows={6}
                placeholder="Enter secret data..."
                className="mt-1 w-full rounded-md border border-gray-300 px-3 py-2 text-sm focus:border-blue-500 focus:outline-none focus:ring-1 focus:ring-blue-500"
              />
            </div>

            <div className="mt-6 flex justify-end gap-3">
              <button
                onClick={() => {
                  setShowAddVersionModal(false);
                  setNewVersionData('');
                }}
                disabled={addingVersion}
                className="rounded-md border border-gray-300 bg-white px-4 py-2 text-sm font-medium text-gray-700 hover:bg-gray-50 disabled:opacity-50"
              >
                Cancel
              </button>
              <button
                onClick={handleAddVersion}
                disabled={addingVersion || !newVersionData.trim()}
                className="inline-flex items-center gap-2 rounded-md bg-blue-600 px-4 py-2 text-sm font-medium text-white hover:bg-blue-700 disabled:opacity-50"
              >
                {addingVersion && <Loader2 className="h-4 w-4 animate-spin" />}
                Add Version
              </button>
            </div>
          </div>
        </div>
      )}

      {/* View Secret Modal */}
      {showViewSecretModal && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black bg-opacity-50 p-4">
          <div className="w-full max-w-lg rounded-lg bg-white p-6 shadow-xl">
            <h3 className="text-lg font-semibold text-gray-900">Secret Value</h3>
            <p className="mt-1 text-sm text-gray-500">Version {viewingVersion || 'latest'}</p>

            <div className="mt-4">
              <div className="flex items-center justify-between mb-2">
                <label className="block text-sm font-medium text-gray-700">Data</label>
                <button
                  onClick={() => setShowSecretValue(!showSecretValue)}
                  className="inline-flex items-center gap-1 text-sm text-blue-600 hover:text-blue-700"
                >
                  {showSecretValue ? (
                    <>
                      <EyeOff className="h-4 w-4" />
                      Hide
                    </>
                  ) : (
                    <>
                      <Eye className="h-4 w-4" />
                      Show
                    </>
                  )}
                </button>
              </div>
              <div className="relative">
                <textarea
                  value={showSecretValue ? secretData : '●'.repeat(secretData.length)}
                  readOnly
                  rows={6}
                  className="w-full rounded-md border border-gray-300 bg-gray-50 px-3 py-2 text-sm font-mono"
                />
                <button
                  onClick={() => copyToClipboard(secretData)}
                  className="absolute right-2 top-2 rounded p-1.5 text-gray-500 hover:bg-white hover:text-blue-600"
                  title="Copy to clipboard"
                >
                  <Copy className="h-4 w-4" />
                </button>
              </div>
            </div>

            <div className="mt-6 flex justify-end">
              <button
                onClick={() => {
                  setShowViewSecretModal(false);
                  setSecretData('');
                  setShowSecretValue(false);
                }}
                className="rounded-md bg-gray-900 px-4 py-2 text-sm font-medium text-white hover:bg-gray-800"
              >
                Close
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Generate Password Modal */}
      {showGeneratePasswordModal && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black bg-opacity-50 p-4">
          <div className="w-full max-w-lg rounded-lg bg-white p-6 shadow-xl">
            <h3 className="text-lg font-semibold text-gray-900">Generated Password</h3>
            <p className="mt-1 text-sm text-gray-500">Use this password for your secret</p>

            <div className="mt-4">
              <div className="relative">
                <input
                  type="text"
                  value={generatedPassword}
                  readOnly
                  className="w-full rounded-md border border-gray-300 bg-gray-50 px-3 py-2 pr-10 text-sm font-mono"
                />
                <button
                  onClick={() => copyToClipboard(generatedPassword)}
                  className="absolute right-2 top-1/2 -translate-y-1/2 rounded p-1.5 text-gray-500 hover:bg-white hover:text-blue-600"
                  title="Copy to clipboard"
                >
                  <Copy className="h-4 w-4" />
                </button>
              </div>
              <p className="mt-2 text-xs text-gray-500">
                This password will not be stored. Make sure to copy it now.
              </p>
            </div>

            <div className="mt-6 flex justify-end gap-3">
              <button
                onClick={() => {
                  setShowGeneratePasswordModal(false);
                  setGeneratedPassword('');
                }}
                className="rounded-md border border-gray-300 bg-white px-4 py-2 text-sm font-medium text-gray-700 hover:bg-gray-50"
              >
                Close
              </button>
              <button
                onClick={() => {
                  setNewVersionData(generatedPassword);
                  setShowGeneratePasswordModal(false);
                  setShowAddVersionModal(true);
                  toast.success('Password copied to new version form');
                }}
                className="rounded-md bg-blue-600 px-4 py-2 text-sm font-medium text-white hover:bg-blue-700"
              >
                Use in New Version
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
