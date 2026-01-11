import React, { useState } from 'react';
import { createInstance } from '../../api/compute';

interface CreateInstanceModalProps {
  isOpen: boolean;
  onClose: () => void;
  onSuccess: () => void;
}

export const CreateInstanceModal: React.FC<CreateInstanceModalProps> = ({ isOpen, onClose, onSuccess }) => {
  const [name, setName] = useState('');
  const [zone, setZone] = useState('us-central1-a');
  const [machineType, setMachineType] = useState('n1-standard-1');
  const [description, setDescription] = useState('');
  const [image, setImage] = useState('debian-11');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    setError(null);

    try {
      await createInstance({
        name,
        zone,
        machine_type: machineType,
        description,
        image,
        labels: {},
        metadata: {}
      });
      onSuccess();
      onClose();
      // Reset form
      setName('');
      setDescription('');
      setImage('debian-11');
    } catch (err: any) {
      setError(err.message || 'Failed to create instance');
    } finally {
      setLoading(false);
    }
  };

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
      <div className="bg-white rounded-lg shadow-xl p-6 w-full max-w-md">
        <h2 className="text-2xl font-bold text-gray-900 mb-4">Create Instance</h2>
        
        <form onSubmit={handleSubmit} className="space-y-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Instance Name *
            </label>
            <input
              type="text"
              value={name}
              onChange={(e) => setName(e.target.value)}
              className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
              placeholder="my-instance"
              required
              pattern="[a-z0-9-]+"
              title="Only lowercase letters, numbers, and hyphens"
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Zone *
            </label>
            <select
              value={zone}
              onChange={(e) => setZone(e.target.value)}
              className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
              required
            >
              <option value="us-central1-a">us-central1-a</option>
              <option value="us-central1-b">us-central1-b</option>
              <option value="us-east1-a">us-east1-a</option>
              <option value="europe-west1-b">europe-west1-b</option>
              <option value="asia-east1-a">asia-east1-a</option>
            </select>
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Machine Type *
            </label>
            <select
              value={machineType}
              onChange={(e) => setMachineType(e.target.value)}
              className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
              required
            >
              <option value="f1-micro">f1-micro (0.2 vCPU, 0.6 GB)</option>
              <option value="g1-small">g1-small (0.5 vCPU, 1.7 GB)</option>
              <option value="n1-standard-1">n1-standard-1 (1 vCPU, 3.75 GB)</option>
              <option value="n1-standard-2">n1-standard-2 (2 vCPU, 7.5 GB)</option>
              <option value="n1-standard-4">n1-standard-4 (4 vCPU, 15 GB)</option>
            </select>
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Image
            </label>
            <input
              type="text"
              value={image}
              onChange={(e) => setImage(e.target.value)}
              className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
              placeholder="debian-11"
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Description
            </label>
            <textarea
              value={description}
              onChange={(e) => setDescription(e.target.value)}
              className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
              placeholder="Optional description"
              rows={2}
            />
          </div>

          {error && (
            <div className="bg-red-50 text-red-700 px-3 py-2 rounded-md text-sm">
              {error}
            </div>
          )}

          <div className="flex justify-end gap-3 mt-6">
            <button
              type="button"
              onClick={onClose}
              className="px-4 py-2 text-sm font-medium text-gray-700 bg-white border border-gray-300 rounded-md hover:bg-gray-50"
              disabled={loading}
            >
              Cancel
            </button>
            <button
              type="submit"
              className="px-4 py-2 text-sm font-medium text-white bg-blue-600 rounded-md hover:bg-blue-700 disabled:bg-gray-400"
              disabled={loading}
            >
              {loading ? 'Creating...' : 'Create Instance'}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
};

