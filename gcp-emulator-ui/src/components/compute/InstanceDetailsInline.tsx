import React from 'react';
import { Instance } from '../../types/compute';

interface InstanceDetailsInlineProps {
  instance: Instance;
}

const KeyValueList: React.FC<{ data: Record<string, string> | undefined, title: string }> = ({ data, title }) => {
  if (!data || Object.keys(data).length === 0) {
    return null;
  }
  return (
    <div>
      <h4 className="text-sm font-semibold text-gray-700 mb-2">{title}</h4>
      <div className="space-y-1">
        {Object.entries(data).map(([key, value]) => (
          <div key={key} className="text-sm">
            <span className="font-mono bg-gray-100 px-2 py-0.5 rounded text-gray-800">{key}</span>
            <span className="text-gray-600">: {value}</span>
          </div>
        ))}
      </div>
    </div>
  );
};

const InstanceDetailsInline: React.FC<InstanceDetailsInlineProps> = ({ instance }) => {
  return (
    <div className="p-6 space-y-4">
      <div className="grid grid-cols-2 gap-4">
        <div>
          <h4 className="text-sm font-semibold text-gray-700 mb-2">Instance Details</h4>
          <div className="space-y-2 text-sm">
            <div><span className="font-medium text-gray-600">ID:</span> <span className="font-mono text-gray-800">{instance.id}</span></div>
            <div><span className="font-medium text-gray-600">Project:</span> <span className="text-gray-800">{instance.project_id}</span></div>
            <div><span className="font-medium text-gray-600">Image:</span> <span className="text-gray-800">{instance.image}</span></div>
            <div><span className="font-medium text-gray-600">CPU:</span> <span className="text-gray-800">{instance.cpu} cores</span></div>
            <div><span className="font-medium text-gray-600">Memory:</span> <span className="text-gray-800">{instance.memory_mb} MB ({(instance.memory_mb / 1024).toFixed(2)} GB)</span></div>
          </div>
        </div>
        <div>
          <h4 className="text-sm font-semibold text-gray-700 mb-2">Container Details</h4>
          <div className="space-y-2 text-sm">
            <div><span className="font-medium text-gray-600">Container ID:</span> <span className="font-mono text-xs text-gray-800">{instance.container_id || 'N/A'}</span></div>
            <div><span className="font-medium text-gray-600">Created:</span> <span className="text-gray-800">{new Date(instance.created_at).toLocaleString()}</span></div>
            <div><span className="font-medium text-gray-600">Updated:</span> <span className="text-gray-800">{new Date(instance.updated_at).toLocaleString()}</span></div>
          </div>
        </div>
      </div>
      {instance.description && (
        <div>
          <h4 className="text-sm font-semibold text-gray-700 mb-1">Description</h4>
          <p className="text-sm text-gray-600">{instance.description}</p>
        </div>
      )}
      <KeyValueList data={instance.labels} title="Labels" />
      <KeyValueList data={instance.metadata} title="Metadata" />
    </div>
  );
};

export default InstanceDetailsInline;
