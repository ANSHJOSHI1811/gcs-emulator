import React, { useState } from 'react';
import { Instance } from '../../types/compute';
import ActionButtons from './ActionButtons';
import InstanceDetailsInline from './InstanceDetailsInline';
import { startInstance, stopInstance, terminateInstance } from '../../api/compute';

interface InstanceRowProps {
  instance: Instance;
  onAction: () => void;
}

const InstanceRow: React.FC<InstanceRowProps> = ({ instance, onAction }) => {
  const [isExpanded, setIsExpanded] = useState(false);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleAction = async (action: 'start' | 'stop' | 'delete') => {
    setLoading(true);
    setError(null);
    try {
      switch (action) {
        case 'start':
          await startInstance(instance.id);
          break;
        case 'stop':
          await stopInstance(instance.id);
          break;
        case 'delete':
          await terminateInstance(instance.id);
          break;
      }
      setTimeout(onAction, 1000); // Give backend time to update
    } catch (err: any) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  const getStatusPill = (status: string) => {
    const upperStatus = status.toUpperCase();
    switch (upperStatus) {
      case 'RUNNING':
        return <span className="px-2 py-1 text-xs font-semibold leading-tight text-green-700 bg-green-100 rounded-full">RUNNING</span>;
      case 'STOPPED':
        return <span className="px-2 py-1 text-xs font-semibold leading-tight text-yellow-700 bg-yellow-100 rounded-full">STOPPED</span>;
      case 'TERMINATED':
        return <span className="px-2 py-1 text-xs font-semibold leading-tight text-red-700 bg-red-100 rounded-full">TERMINATED</span>;
      case 'STOPPING':
        return <span className="px-2 py-1 text-xs font-semibold leading-tight text-orange-700 bg-orange-100 rounded-full">STOPPING</span>;
      default:
        return <span className="px-2 py-1 text-xs font-semibold leading-tight text-gray-700 bg-gray-100 rounded-full">{upperStatus}</span>;
    }
  };

  return (
    <>
      <tr className="hover:bg-gray-50 cursor-pointer transition-colors" onClick={() => setIsExpanded(!isExpanded)}>
        <td className="px-6 py-4 whitespace-nowrap text-sm font-medium text-gray-900">{instance.name}</td>
        <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">{instance.image}</td>
        <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">{instance.cpu} CPU / {instance.memory_mb} MB</td>
        <td className="px-6 py-4 whitespace-nowrap text-sm">{getStatusPill(instance.state)}</td>
        <td className="px-6 py-4 whitespace-nowrap text-xs font-mono text-gray-500">{instance.container_id ? instance.container_id.substring(0, 12) : 'N/A'}</td>
        <td className="px-6 py-4 whitespace-nowrap text-sm" onClick={(e) => e.stopPropagation()}>
          <ActionButtons
            instance={instance}
            onStart={() => handleAction('start')}
            onStop={() => handleAction('stop')}
            onDelete={() => handleAction('delete')}
            loading={loading}
          />
        </td>
      </tr>
      {isExpanded && (
        <tr>
          <td colSpan={6} className="bg-gray-50 border-t border-gray-200">
            <InstanceDetailsInline instance={instance} />
          </td>
        </tr>
      )}
      {error && (
        <tr>
          <td colSpan={6} className="px-6 py-3 text-sm text-red-600 text-center bg-red-50">
            {error}
          </td>
        </tr>
      )}
    </>
  );
};

export default InstanceRow;
