import { useState } from 'react';
import { X } from 'lucide-react';

interface CreateInstanceModalProps {
  onClose: () => void;
  onCreate: (data: {
    name: string;
    image: string;
    cpu: number;
    memory: number;
  }) => Promise<void>;
}

export default function CreateInstanceModal({ onClose, onCreate }: CreateInstanceModalProps) {
  const [formData, setFormData] = useState({
    name: '',
    image: 'alpine:latest',
    cpu: 1,
    memory: 512,
  });
  const [loading, setLoading] = useState(false);
  const [errors, setErrors] = useState<Record<string, string>>({});

  const popularImages = [
    { value: 'alpine:latest', label: 'Alpine Linux (Latest)' },
    { value: 'alpine:3.19', label: 'Alpine Linux 3.19' },
    { value: 'ubuntu:latest', label: 'Ubuntu (Latest)' },
    { value: 'ubuntu:22.04', label: 'Ubuntu 22.04' },
    { value: 'debian:latest', label: 'Debian (Latest)' },
    { value: 'nginx:latest', label: 'Nginx (Latest)' },
    { value: 'redis:latest', label: 'Redis (Latest)' },
    { value: 'postgres:latest', label: 'PostgreSQL (Latest)' },
  ];

  const validate = () => {
    const newErrors: Record<string, string> = {};

    if (!formData.name.trim()) {
      newErrors.name = 'Instance name is required';
    } else if (!/^[a-z0-9-]+$/.test(formData.name)) {
      newErrors.name = 'Name must contain only lowercase letters, numbers, and hyphens';
    }

    if (!formData.image.trim()) {
      newErrors.image = 'Docker image is required';
    }

    if (formData.cpu < 1 || formData.cpu > 8) {
      newErrors.cpu = 'CPU must be between 1 and 8';
    }

    if (formData.memory < 128 || formData.memory > 8192) {
      newErrors.memory = 'Memory must be between 128 and 8192 MB';
    }

    setErrors(newErrors);
    return Object.keys(newErrors).length === 0;
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();

    if (!validate()) return;

    try {
      setLoading(true);
      await onCreate(formData);
    } catch (error) {
      // Error handled by parent
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="fixed inset-0 bg-gray-500 bg-opacity-75 flex items-center justify-center p-4 z-50">
      <div className="bg-white rounded-lg shadow-xl max-w-md w-full max-h-[90vh] overflow-y-auto">
        <div className="flex items-center justify-between p-6 border-b border-gray-200">
          <h3 className="text-lg font-medium text-gray-900">Create Instance</h3>
          <button
            onClick={onClose}
            className="text-gray-400 hover:text-gray-500"
            disabled={loading}
          >
            <X className="h-6 w-6" />
          </button>
        </div>

        <form onSubmit={handleSubmit} className="p-6 space-y-4">
          <div>
            <label htmlFor="name" className="block text-sm font-medium text-gray-700">
              Instance Name *
            </label>
            <input
              type="text"
              id="name"
              value={formData.name}
              onChange={(e) => setFormData({ ...formData, name: e.target.value })}
              className={`mt-1 block w-full rounded-md shadow-sm sm:text-sm ${
                errors.name
                  ? 'border-red-300 focus:border-red-500 focus:ring-red-500'
                  : 'border-gray-300 focus:border-blue-500 focus:ring-blue-500'
              }`}
              placeholder="my-instance"
              disabled={loading}
            />
            {errors.name && <p className="mt-1 text-sm text-red-600">{errors.name}</p>}
            <p className="mt-1 text-xs text-gray-500">
              Lowercase letters, numbers, and hyphens only
            </p>
          </div>

          <div>
            <label htmlFor="image" className="block text-sm font-medium text-gray-700">
              Docker Image *
            </label>
            <select
              id="image"
              value={formData.image}
              onChange={(e) => setFormData({ ...formData, image: e.target.value })}
              className={`mt-1 block w-full rounded-md shadow-sm sm:text-sm ${
                errors.image
                  ? 'border-red-300 focus:border-red-500 focus:ring-red-500'
                  : 'border-gray-300 focus:border-blue-500 focus:ring-blue-500'
              }`}
              disabled={loading}
            >
              {popularImages.map((img) => (
                <option key={img.value} value={img.value}>
                  {img.label}
                </option>
              ))}
              <option value="">-- Custom Image --</option>
            </select>
            {formData.image === '' && (
              <input
                type="text"
                value={formData.image}
                onChange={(e) => setFormData({ ...formData, image: e.target.value })}
                className="mt-2 block w-full rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500 sm:text-sm"
                placeholder="custom-image:tag"
                disabled={loading}
              />
            )}
            {errors.image && <p className="mt-1 text-sm text-red-600">{errors.image}</p>}
          </div>

          <div>
            <label htmlFor="cpu" className="block text-sm font-medium text-gray-700">
              CPU Cores *
            </label>
            <input
              type="number"
              id="cpu"
              value={formData.cpu}
              onChange={(e) => setFormData({ ...formData, cpu: parseInt(e.target.value) || 1 })}
              min="1"
              max="8"
              className={`mt-1 block w-full rounded-md shadow-sm sm:text-sm ${
                errors.cpu
                  ? 'border-red-300 focus:border-red-500 focus:ring-red-500'
                  : 'border-gray-300 focus:border-blue-500 focus:ring-blue-500'
              }`}
              disabled={loading}
            />
            {errors.cpu && <p className="mt-1 text-sm text-red-600">{errors.cpu}</p>}
            <p className="mt-1 text-xs text-gray-500">1-8 CPU cores</p>
          </div>

          <div>
            <label htmlFor="memory" className="block text-sm font-medium text-gray-700">
              Memory (MB) *
            </label>
            <input
              type="number"
              id="memory"
              value={formData.memory}
              onChange={(e) =>
                setFormData({ ...formData, memory: parseInt(e.target.value) || 512 })
              }
              min="128"
              max="8192"
              step="128"
              className={`mt-1 block w-full rounded-md shadow-sm sm:text-sm ${
                errors.memory
                  ? 'border-red-300 focus:border-red-500 focus:ring-red-500'
                  : 'border-gray-300 focus:border-blue-500 focus:ring-blue-500'
              }`}
              disabled={loading}
            />
            {errors.memory && <p className="mt-1 text-sm text-red-600">{errors.memory}</p>}
            <p className="mt-1 text-xs text-gray-500">
              128-8192 MB (Current: {(formData.memory / 1024).toFixed(2)} GB)
            </p>
          </div>

          <div className="bg-blue-50 border-l-4 border-blue-400 p-4">
            <div className="flex">
              <div className="flex-shrink-0">
                <svg
                  className="h-5 w-5 text-blue-400"
                  viewBox="0 0 20 20"
                  fill="currentColor"
                >
                  <path
                    fillRule="evenodd"
                    d="M18 10a8 8 0 11-16 0 8 8 0 0116 0zm-7-4a1 1 0 11-2 0 1 1 0 012 0zM9 9a1 1 0 000 2v3a1 1 0 001 1h1a1 1 0 100-2v-3a1 1 0 00-1-1H9z"
                    clipRule="evenodd"
                  />
                </svg>
              </div>
              <div className="ml-3">
                <p className="text-sm text-blue-700">
                  Instances are backed by Docker containers. The image will be pulled if not
                  already available.
                </p>
              </div>
            </div>
          </div>
        </form>

        <div className="flex justify-end gap-3 px-6 py-4 bg-gray-50 border-t border-gray-200">
          <button
            type="button"
            onClick={onClose}
            disabled={loading}
            className="px-4 py-2 text-sm font-medium text-gray-700 bg-white border border-gray-300 rounded-md hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500 disabled:opacity-50"
          >
            Cancel
          </button>
          <button
            type="submit"
            onClick={handleSubmit}
            disabled={loading}
            className="px-4 py-2 text-sm font-medium text-white bg-blue-600 border border-transparent rounded-md hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500 disabled:opacity-50"
          >
            {loading ? 'Creating...' : 'Create Instance'}
          </button>
        </div>
      </div>
    </div>
  );
}
