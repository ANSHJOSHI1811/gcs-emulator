import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { useProject } from '../contexts/ProjectContext';
import { createMetricDescriptor, MetricKind, ValueType } from '../api/monitoring';
import toast from 'react-hot-toast';
import { ArrowLeft, Loader2, Copy, CheckCircle2 } from 'lucide-react';

interface MetricTemplate {
  name: string;
  type: string;
  displayName: string;
  description: string;
  metricKind: MetricKind;
  valueType: ValueType;
  unit: string;
}

const METRIC_TEMPLATES: MetricTemplate[] = [
  {
    name: 'CPU Usage',
    type: 'custom.googleapis.com/cpu_usage',
    displayName: 'CPU Usage (%)',
    description: 'CPU utilization percentage',
    metricKind: MetricKind.GAUGE,
    valueType: ValueType.DOUBLE,
    unit: '%',
  },
  {
    name: 'Memory Usage',
    type: 'custom.googleapis.com/memory_usage',
    displayName: 'Memory Usage (MB)',
    description: 'Memory usage in megabytes',
    metricKind: MetricKind.GAUGE,
    valueType: ValueType.INT64,
    unit: 'MB',
  },
  {
    name: 'Request Latency',
    type: 'custom.googleapis.com/request_latency',
    displayName: 'Request Latency (ms)',
    description: 'API request latency in milliseconds',
    metricKind: MetricKind.GAUGE,
    valueType: ValueType.DOUBLE,
    unit: 'ms',
  },
  {
    name: 'Error Rate',
    type: 'custom.googleapis.com/error_rate',
    displayName: 'Error Rate (%)',
    description: 'Percentage of requests that resulted in errors',
    metricKind: MetricKind.GAUGE,
    valueType: ValueType.DOUBLE,
    unit: '%',
  },
  {
    name: 'Active Connections',
    type: 'custom.googleapis.com/active_connections',
    displayName: 'Active Connections',
    description: 'Number of active database connections',
    metricKind: MetricKind.GAUGE,
    valueType: ValueType.INT64,
    unit: '1',
  },
  {
    name: 'Total Requests',
    type: 'custom.googleapis.com/total_requests',
    displayName: 'Total Requests',
    description: 'Cumulative count of requests',
    metricKind: MetricKind.CUMULATIVE,
    valueType: ValueType.INT64,
    unit: '1',
  },
  {
    name: 'Disk Usage',
    type: 'custom.googleapis.com/disk_usage',
    displayName: 'Disk Usage (GB)',
    description: 'Disk storage usage in gigabytes',
    metricKind: MetricKind.GAUGE,
    valueType: ValueType.DOUBLE,
    unit: 'GB',
  },
  {
    name: 'Network Traffic',
    type: 'custom.googleapis.com/network_traffic',
    displayName: 'Network Traffic (Mbps)',
    description: 'Network throughput in megabits per second',
    metricKind: MetricKind.GAUGE,
    valueType: ValueType.DOUBLE,
    unit: 'Mbps',
  },
];

export default function CreateMetricPage() {
  const { currentProject } = useProject();
  const navigate = useNavigate();

  const [mode, setMode] = useState<'template' | 'custom'>('template');
  const [selectedTemplate, setSelectedTemplate] = useState<MetricTemplate | null>(null);
  const [submitting, setSubmitting] = useState(false);
  const [copied, setCopied] = useState<string | null>(null);

  const [customForm, setCustomForm] = useState({
    type: '',
    displayName: '',
    description: '',
    metricKind: MetricKind.GAUGE as MetricKind,
    valueType: ValueType.DOUBLE as ValueType,
    unit: '1',
  });

  function copyToClipboard(text: string, id: string) {
    navigator.clipboard.writeText(text);
    setCopied(id);
    setTimeout(() => setCopied(null), 2000);
  }

  async function handleCreateFromTemplate(template: MetricTemplate) {
    if (!currentProject) return;

    setSubmitting(true);
    try {
      await createMetricDescriptor(
        template.type,
        template.metricKind,
        template.valueType,
        template.displayName,
        template.description,
        template.unit,
        currentProject
      );
      toast.success(`Created metric: ${template.displayName}`);
      navigate('/services/monitoring');
    } catch (err: unknown) {
      const message = err instanceof Error ? err.message : 'Failed to create metric';
      if (message.includes('409')) {
        toast.error(`Metric "${template.type}" already exists`);
      } else {
        toast.error(message);
      }
    } finally {
      setSubmitting(false);
    }
  }

  async function handleCreateCustom() {
    if (!currentProject) return;

    if (!customForm.type || !customForm.displayName) {
      toast.error('Type and display name are required');
      return;
    }

    setSubmitting(true);
    try {
      await createMetricDescriptor(
        customForm.type,
        customForm.metricKind,
        customForm.valueType,
        customForm.displayName,
        customForm.description,
        customForm.unit,
        currentProject
      );
      toast.success(`Created metric: ${customForm.displayName}`);
      navigate('/services/monitoring');
    } catch (err: unknown) {
      const message = err instanceof Error ? err.message : 'Failed to create metric';
      if (message.includes('409')) {
        toast.error(`Metric "${customForm.type}" already exists`);
      } else {
        toast.error(message);
      }
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <div className="border-b border-gray-200 bg-white px-6 py-4">
        <div className="flex items-center gap-4">
          <button
            onClick={() => navigate('/services/monitoring')}
            className="rounded-md p-1.5 text-gray-500 hover:bg-gray-100"
          >
            <ArrowLeft className="h-5 w-5" />
          </button>
          <div>
            <h1 className="text-xl font-semibold text-gray-900">Create Metric</h1>
            <p className="text-sm text-gray-500">Project: {currentProject}</p>
          </div>
        </div>
      </div>

      <div className="max-w-4xl mx-auto px-6 py-8">
        {/* Mode Selector */}
        <div className="mb-8 flex gap-4">
          <button
            onClick={() => { setMode('template'); setSelectedTemplate(null); }}
            className={`px-6 py-3 rounded-lg font-medium transition-colors ${
              mode === 'template'
                ? 'bg-blue-600 text-white'
                : 'bg-white border border-gray-300 text-gray-700 hover:bg-gray-50'
            }`}
          >
            📋 Use Template
          </button>
          <button
            onClick={() => setMode('custom')}
            className={`px-6 py-3 rounded-lg font-medium transition-colors ${
              mode === 'custom'
                ? 'bg-blue-600 text-white'
                : 'bg-white border border-gray-300 text-gray-700 hover:bg-gray-50'
            }`}
          >
            ✏️ Custom Metric
          </button>
        </div>

        {/* Template Mode */}
        {mode === 'template' && !selectedTemplate && (
          <div>
            <h2 className="text-lg font-semibold text-gray-900 mb-4">Select a template</h2>
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
              {METRIC_TEMPLATES.map((template) => (
                <div
                  key={template.type}
                  className="bg-white rounded-lg border border-gray-200 p-4 hover:border-blue-400 hover:shadow-md transition-all cursor-pointer"
                  onClick={() => setSelectedTemplate(template)}
                >
                  <h3 className="font-semibold text-gray-900 text-base">{template.name}</h3>
                  <p className="text-sm text-gray-600 mt-1">{template.description}</p>
                  <div className="mt-3 space-y-1">
                    <p className="text-xs text-gray-500">
                      <span className="font-medium">Type:</span> {template.type}
                    </p>
                    <p className="text-xs text-gray-500">
                      <span className="font-medium">Kind:</span> {template.metricKind}
                    </p>
                  </div>
                  <button
                    onClick={(e) => {
                      e.stopPropagation();
                      handleCreateFromTemplate(template);
                    }}
                    disabled={submitting}
                    className="mt-4 w-full py-2 px-3 bg-blue-600 text-white text-sm font-medium rounded-md hover:bg-blue-700 disabled:opacity-60 disabled:cursor-not-allowed transition-colors"
                  >
                    {submitting ? <Loader2 className="h-4 w-4 inline animate-spin mr-2" /> : null}
                    Create
                  </button>
                </div>
              ))}
            </div>
          </div>
        )}

        {/* Template Details */}
        {mode === 'template' && selectedTemplate && (
          <div className="bg-white rounded-lg border border-gray-200 p-8">
            <button
              onClick={() => setSelectedTemplate(null)}
              className="text-blue-600 hover:text-blue-700 text-sm font-medium mb-6"
            >
              ← Back to templates
            </button>

            <h2 className="text-2xl font-semibold text-gray-900 mb-2">
              {selectedTemplate.name}
            </h2>
            <p className="text-gray-600 mb-8">{selectedTemplate.description}</p>

            <div className="space-y-4 mb-8">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Type</label>
                <div className="flex items-center gap-2">
                  <code className="flex-1 bg-gray-100 px-4 py-2 rounded-md font-mono text-sm text-gray-900 break-all">
                    {selectedTemplate.type}
                  </code>
                  <button
                    onClick={() => copyToClipboard(selectedTemplate.type, 'type')}
                    className="p-2 text-gray-500 hover:bg-gray-100 rounded-md"
                  >
                    {copied === 'type' ? (
                      <CheckCircle2 className="h-5 w-5 text-green-600" />
                    ) : (
                      <Copy className="h-5 w-5" />
                    )}
                  </button>
                </div>
              </div>

              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">Kind</label>
                  <p className="bg-gray-100 px-4 py-2 rounded-md text-sm text-gray-900">
                    {selectedTemplate.metricKind}
                  </p>
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">Value Type</label>
                  <p className="bg-gray-100 px-4 py-2 rounded-md text-sm text-gray-900">
                    {selectedTemplate.valueType}
                  </p>
                </div>
              </div>

              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">Unit</label>
                  <p className="bg-gray-100 px-4 py-2 rounded-md text-sm text-gray-900">
                    {selectedTemplate.unit}
                  </p>
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">Display Name</label>
                  <p className="bg-gray-100 px-4 py-2 rounded-md text-sm text-gray-900">
                    {selectedTemplate.displayName}
                  </p>
                </div>
              </div>
            </div>

            <div className="flex items-center justify-end gap-3">
              <button
                onClick={() => setSelectedTemplate(null)}
                className="px-4 py-2 border border-gray-300 text-gray-700 font-medium rounded-md hover:bg-gray-50"
              >
                Cancel
              </button>
              <button
                onClick={() => handleCreateFromTemplate(selectedTemplate)}
                disabled={submitting}
                className="inline-flex items-center gap-2 px-4 py-2 bg-blue-600 text-white font-medium rounded-md hover:bg-blue-700 disabled:opacity-60 disabled:cursor-not-allowed"
              >
                {submitting && <Loader2 className="h-4 w-4 animate-spin" />}
                Create Metric
              </button>
            </div>
          </div>
        )}

        {/* Custom Mode */}
        {mode === 'custom' && (
          <div className="bg-white rounded-lg border border-gray-200 p-8">
            <h2 className="text-lg font-semibold text-gray-900 mb-6">Create custom metric</h2>

            <div className="space-y-6">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Metric Type <span className="text-red-500">*</span>
                </label>
                <input
                  type="text"
                  value={customForm.type}
                  onChange={(e) => setCustomForm({ ...customForm, type: e.target.value })}
                  placeholder="custom.googleapis.com/my_metric"
                  className="w-full rounded-md border border-gray-300 px-4 py-2 text-sm font-mono focus:outline-none focus:ring-2 focus:ring-blue-500"
                />
                <p className="mt-1 text-xs text-gray-500">
                  Must start with <code className="bg-gray-100 px-1 py-0.5 rounded">custom.googleapis.com/</code>
                </p>
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Display Name <span className="text-red-500">*</span>
                </label>
                <input
                  type="text"
                  value={customForm.displayName}
                  onChange={(e) => setCustomForm({ ...customForm, displayName: e.target.value })}
                  placeholder="My Metric (Unit)"
                  className="w-full rounded-md border border-gray-300 px-4 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">Description</label>
                <textarea
                  value={customForm.description}
                  onChange={(e) => setCustomForm({ ...customForm, description: e.target.value })}
                  placeholder="What does this metric measure?"
                  rows={3}
                  className="w-full rounded-md border border-gray-300 px-4 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
                />
              </div>

              <div className="grid grid-cols-3 gap-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">Metric Kind</label>
                  <select
                    value={customForm.metricKind}
                    onChange={(e) => setCustomForm({ ...customForm, metricKind: e.target.value as MetricKind })}
                    className="w-full rounded-md border border-gray-300 px-4 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
                  >
                    <option value={MetricKind.GAUGE}>GAUGE (current value)</option>
                    <option value={MetricKind.DELTA}>DELTA (change)</option>
                    <option value={MetricKind.CUMULATIVE}>CUMULATIVE (total)</option>
                  </select>
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">Value Type</label>
                  <select
                    value={customForm.valueType}
                    onChange={(e) => setCustomForm({ ...customForm, valueType: e.target.value as ValueType })}
                    className="w-full rounded-md border border-gray-300 px-4 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
                  >
                    <option value={ValueType.DOUBLE}>DOUBLE (decimal)</option>
                    <option value={ValueType.INT64}>INT64 (integer)</option>
                    <option value={ValueType.BOOL}>BOOL (true/false)</option>
                    <option value={ValueType.STRING}>STRING</option>
                  </select>
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">Unit</label>
                  <input
                    type="text"
                    value={customForm.unit}
                    onChange={(e) => setCustomForm({ ...customForm, unit: e.target.value })}
                    placeholder="% or GB or ms"
                    className="w-full rounded-md border border-gray-300 px-4 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
                  />
                </div>
              </div>
            </div>

            <div className="mt-8 flex items-center justify-end gap-3">
              <button
                onClick={() => setMode('template')}
                className="px-4 py-2 border border-gray-300 text-gray-700 font-medium rounded-md hover:bg-gray-50"
              >
                Back
              </button>
              <button
                onClick={handleCreateCustom}
                disabled={submitting || !customForm.type || !customForm.displayName}
                className="inline-flex items-center gap-2 px-4 py-2 bg-blue-600 text-white font-medium rounded-md hover:bg-blue-700 disabled:opacity-60 disabled:cursor-not-allowed"
              >
                {submitting && <Loader2 className="h-4 w-4 animate-spin" />}
                Create Metric
              </button>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
