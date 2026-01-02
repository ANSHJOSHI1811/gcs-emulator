import React, { useState, useEffect, useCallback } from 'react';
import { getInstances, createInstance, getDockerImages } from '../api/compute';
import { Instance } from '../types/compute';
import StatsBar from '../components/compute/StatsBar';
import InstanceTable from '../components/compute/InstanceTable';

const ComputePage: React.FC = () => {
  const [instances, setInstances] = useState<Instance[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [showCreateModal, setShowCreateModal] = useState(false);
  const [createLoading, setCreateLoading] = useState(false);
  const [createError, setCreateError] = useState<string | null>(null);
  const [dockerImages, setDockerImages] = useState<Array<{name: string; id: string; size: string}>>([]);
  const [loadingImages, setLoadingImages] = useState(false);
  const [formData, setFormData] = useState({
    name: '',
    image: 'alpine:latest',
    cpu: 1,
    memory_mb: 512,
  });

  const fetchInstances = useCallback(async () => {
    try {
      setLoading(true);
      const data = await getInstances();
      setInstances(data);
    } catch (err: any) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchInstances();
    const interval = setInterval(fetchInstances, 5000); // Poll every 5 seconds
    return () => clearInterval(interval);
  }, [fetchInstances]);

  const fetchDockerImages = useCallback(async () => {
    try {
      setLoadingImages(true);
      const images = await getDockerImages();
      setDockerImages(images);
      if (images.length > 0 && !formData.image) {
        setFormData(prev => ({ ...prev, image: images[0].name }));
      }
    } catch (err: any) {
      console.error('Failed to fetch Docker images:', err);
    } finally {
      setLoadingImages(false);
    }
  }, [formData.image]);

  const handleCreateInstance = async (e: React.FormEvent) => {
    e.preventDefault();
    setCreateLoading(true);
    setCreateError(null);

    try {
      await createInstance(formData);
      setShowCreateModal(false);
      setFormData({ name: '', image: 'alpine:latest', cpu: 1, memory_mb: 512 });
      fetchInstances();
    } catch (err: any) {
      setCreateError(err.message);
    } finally {
      setCreateLoading(false);
    }
  };

  if (loading && instances.length === 0) {
    return (
      <div className="min-h-screen bg-gray-50 p-8">
        <p className="text-center text-gray-500 mt-8">Loading instances...</p>
      </div>
    );
  }

  if (error) {
    return (
      <div className="min-h-screen bg-gray-50 p-8">
        <div className="bg-red-50 border border-red-200 rounded-lg p-4 text-center">
          <p className="text-red-600">Error: {error}</p>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-50 p-8">
      <div className="flex justify-between items-center mb-6">
        <h1 className="text-3xl font-bold text-gray-900">Compute Engine Instances</h1>
        <button
          onClick={() => {
            setShowCreateModal(true);
            if (dockerImages.length === 0) {
              fetchDockerImages();
            }
          }}
          className="px-4 py-2 text-sm font-medium text-white bg-blue-600 rounded-md hover:bg-blue-700 transition-colors"
        >
          Create Instance
        </button>
      </div>
      <StatsBar instances={instances} />
      <InstanceTable instances={instances} onAction={fetchInstances} />

      {/* Create Instance Modal */}
      {showCreateModal && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <div className="bg-white rounded-lg shadow-xl p-6 w-full max-w-md">
            <h2 className="text-2xl font-bold text-gray-900 mb-4">Create Instance</h2>
            
            <form onSubmit={handleCreateInstance} className="space-y-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Instance Name *
                </label>
                <input
                  type="text"
                  value={formData.name}
                  onChange={(e) => setFormData({ ...formData, name: e.target.value })}
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                  placeholder="my-instance"
                  required
                  pattern="[a-z0-9-]+"
                  title="Only lowercase letters, numbers, and hyphens"
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Docker Image *
                </label>
                {loadingImages ? (
                  <div className="w-full px-3 py-2 border border-gray-300 rounded-md bg-gray-50 text-gray-500">
                    Loading images...
                  </div>
                ) : dockerImages.length > 0 ? (
                  <select
                    value={formData.image}
                    onChange={(e) => setFormData({ ...formData, image: e.target.value })}
                    className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                    required
                  >
                    {dockerImages.map((img) => (
                      <option key={img.id} value={img.name}>
                        {img.name} ({img.size})
                      </option>
                    ))}
                  </select>
                ) : (
                  <input
                    type="text"
                    value={formData.image}
                    onChange={(e) => setFormData({ ...formData, image: e.target.value })}
                    className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                    placeholder="alpine:latest"
                    required
                  />
                )}
                <p className="text-xs text-gray-500 mt-1">
                  {dockerImages.length > 0 ? `${dockerImages.length} images available` : 'Type image name manually'}
                </p>
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  CPU Cores
                </label>
                <input
                  type="number"
                  value={formData.cpu}
                  onChange={(e) => setFormData({ ...formData, cpu: parseInt(e.target.value) || 1 })}
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                  min="1"
                  max="8"
                />
                <p className="text-xs text-gray-500 mt-1">1-8 cores</p>
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Memory (MB)
                </label>
                <input
                  type="number"
                  value={formData.memory_mb}
                  onChange={(e) => setFormData({ ...formData, memory_mb: parseInt(e.target.value) || 512 })}
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                  min="128"
                  max="8192"
                  step="128"
                />
                <p className="text-xs text-gray-500 mt-1">128-8192 MB ({(formData.memory_mb / 1024).toFixed(2)} GB)</p>
              </div>

              {createError && (
                <div className="bg-red-50 text-red-700 px-3 py-2 rounded-md text-sm">
                  {createError}
                </div>
              )}

              <div className="flex justify-end gap-3 mt-6">
                <button
                  type="button"
                  onClick={() => {
                    setShowCreateModal(false);
                    setCreateError(null);
                  }}
                  className="px-4 py-2 text-sm font-medium text-gray-700 bg-white border border-gray-300 rounded-md hover:bg-gray-50"
                  disabled={createLoading}
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  className="px-4 py-2 text-sm font-medium text-white bg-blue-600 rounded-md hover:bg-blue-700 disabled:bg-gray-400"
                  disabled={createLoading}
                >
                  {createLoading ? 'Creating...' : 'Create Instance'}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
};

export default ComputePage;
