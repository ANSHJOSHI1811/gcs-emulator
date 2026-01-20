import React from 'react';
import { Instance } from '../../types/compute';

interface ActionButtonsProps {
  instance: Instance;
  onStart: () => void;
  onStop: () => void;
  onDelete: () => void;
  loading: boolean;
}

const ActionButtons: React.FC<ActionButtonsProps> = ({ instance, onStart, onStop, onDelete, loading }) => {
  const state = instance.state.toLowerCase();
  return (
    <div className="flex space-x-2">
      <button
        onClick={onStart}
        disabled={state === 'running' || loading}
        className="px-3 py-1 text-xs font-medium text-white bg-green-600 hover:bg-green-700 rounded disabled:bg-gray-300 disabled:cursor-not-allowed transition-colors"
      >
        Start
      </button>
      <button
        onClick={onStop}
        disabled={state !== 'running' || loading}
        className="px-3 py-1 text-xs font-medium text-white bg-yellow-600 hover:bg-yellow-700 rounded disabled:bg-gray-300 disabled:cursor-not-allowed transition-colors"
      >
        Stop
      </button>
      <button
        onClick={onDelete}
        disabled={loading}
        className="px-3 py-1 text-xs font-medium text-white bg-red-600 hover:bg-red-700 rounded disabled:bg-gray-300 disabled:cursor-not-allowed transition-colors"
      >
        Delete
      </button>
    </div>
  );
};

export default ActionButtons;
