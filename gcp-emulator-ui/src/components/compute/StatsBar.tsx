import React from 'react';
import { Instance } from '../../types/compute';

interface StatsBarProps {
  instances: Instance[];
}

const StatsBar: React.FC<StatsBarProps> = ({ instances }) => {
  const total = instances.length;
  const running = instances.filter(inst => inst.state.toLowerCase() === 'running').length;
  const stopped = instances.filter(inst => inst.state.toLowerCase() === 'stopped').length;
  const terminated = instances.filter(inst => inst.state.toLowerCase() === 'terminated').length;

  return (
    <div className="grid grid-cols-4 gap-6 mb-6">
      <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
        <p className="text-3xl font-bold text-gray-900">{total}</p>
        <p className="text-sm text-gray-500 mt-1">Total Instances</p>
      </div>
      <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
        <p className="text-3xl font-bold text-green-600">{running}</p>
        <p className="text-sm text-gray-500 mt-1">Running</p>
      </div>
      <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
        <p className="text-3xl font-bold text-yellow-600">{stopped}</p>
        <p className="text-sm text-gray-500 mt-1">Stopped</p>
      </div>
      <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
        <p className="text-3xl font-bold text-red-600">{terminated}</p>
        <p className="text-sm text-gray-500 mt-1">Terminated</p>
      </div>
    </div>
  );
};

export default StatsBar;
