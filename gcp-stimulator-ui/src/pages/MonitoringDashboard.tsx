import { useState, useEffect, useCallback } from 'react';
import { useProject } from '../contexts/ProjectContext';
import {
  listMetricDescriptors,
  listAlertPolicies,
  listNotificationChannels,
  createMetricDescriptor,
  createAlertPolicy,
  createNotificationChannel,
  deleteAlertPolicy,
  deleteNotificationChannel,
  MetricDescriptor,
  AlertPolicy,
  NotificationChannel,
  MetricKind,
  ValueType,
  Condition,
} from '../api/monitoring';
import toast from 'react-hot-toast';
import {
  Activity,
  AlertTriangle,
  Bell,
  Plus,
  RefreshCw,
  Trash2,
  Loader2,
  TrendingUp,
  CheckCircle2,
  XCircle,
} from 'lucide-react';

type ActiveTab = 'metrics' | 'alerts' | 'channels';

export default function MonitoringDashboard() {
  const { currentProject } = useProject();

  const [activeTab, setActiveTab] = useState<ActiveTab>('metrics');
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  // Data
  const [metricDescriptors, setMetricDescriptors] = useState<MetricDescriptor[]>([]);
  const [alertPolicies, setAlertPolicies] = useState<AlertPolicy[]>([]);
  const [notificationChannels, setNotificationChannels] = useState<NotificationChannel[]>([]);

  // Modals
  const [showCreateMetricModal, setShowCreateMetricModal] = useState(false);
  const [showCreateAlertModal, setShowCreateAlertModal] = useState(false);
  const [showCreateChannelModal, setShowCreateChannelModal] = useState(false);

  // Form states
  const [metricForm, setMetricForm] = useState({
    type: '',
    displayName: '',
    description: '',
    metricKind: MetricKind.GAUGE,
    valueType: ValueType.DOUBLE,
    unit: '1',
  });

  const [alertForm, setAlertForm] = useState({
    displayName: '',
    filter: '',
    threshold: 80,
    duration: '60s',
    documentation: '',
  });

  const [channelForm, setChannelForm] = useState({
    type: 'email',
    displayName: '',
    description: '',
    email: '',
  });

  const [submitting, setSubmitting] = useState(false);
  const [deleting, setDeleting] = useState<string | null>(null);

  const fetchData = useCallback(async () => {
    if (!currentProject) return;

    try {
      setLoading(true);
      const [metrics, alerts, channels] = await Promise.all([
        listMetricDescriptors(undefined, currentProject),
        listAlertPolicies(currentProject),
        listNotificationChannels(currentProject),
      ]);

      setMetricDescriptors(metrics);
      setAlertPolicies(alerts);
      setNotificationChannels(channels);
      setError(null);
    } catch (err: unknown) {
      const message = err instanceof Error ? err.message : 'Failed to load monitoring data';
      setError(message);
      toast.error(message);
    } finally {
      setLoading(false);
    }
  }, [currentProject]);

  useEffect(() => {
    fetchData();
  }, [fetchData]);

  function getPolicyId(name: string): string {
    const parts = name.split('/');
    return parts[parts.length - 1] || name;
  }

  function getChannelId(name: string): string {
    const parts = name.split('/');
    return parts[parts.length - 1] || name;
  }

  async function handleCreateMetric() {
    if (!currentProject) return;

    if (!metricForm.type || !metricForm.displayName) {
      toast.error('Type and display name are required');
      return;
    }

    setSubmitting(true);
    try {
      await createMetricDescriptor(
        metricForm.type,
        metricForm.metricKind,
        metricForm.valueType,
        metricForm.displayName,
        metricForm.description,
        metricForm.unit,
        currentProject
      );
      toast.success('Metric descriptor created successfully');
      setShowCreateMetricModal(false);
      setMetricForm({
        type: '',
        displayName: '',
        description: '',
        metricKind: MetricKind.GAUGE,
        valueType: ValueType.DOUBLE,
        unit: '1',
      });
      await fetchData();
    } catch (err: unknown) {
      toast.error(err instanceof Error ? err.message : 'Failed to create metric descriptor');
    } finally {
      setSubmitting(false);
    }
  }

  async function handleCreateAlert() {
    if (!currentProject) return;

    if (!alertForm.displayName || !alertForm.filter) {
      toast.error('Display name and filter are required');
      return;
    }

    setSubmitting(true);
    try {
      const condition: Condition = {
        displayName: `${alertForm.displayName} condition`,
        conditionThreshold: {
          filter: alertForm.filter,
          comparison: 'COMPARISON_GT',
          thresholdValue: alertForm.threshold,
          duration: alertForm.duration,
          aggregations: [
            {
              alignmentPeriod: '60s',
              perSeriesAligner: 'ALIGN_RATE',
            },
          ],
        },
      };

      await createAlertPolicy(
        alertForm.displayName,
        [condition],
        [],
        alertForm.documentation,
        currentProject
      );

      toast.success('Alert policy created successfully');
      setShowCreateAlertModal(false);
      setAlertForm({
        displayName: '',
        filter: '',
        threshold: 80,
        duration: '60s',
        documentation: '',
      });
      await fetchData();
    } catch (err: unknown) {
      toast.error(err instanceof Error ? err.message : 'Failed to create alert policy');
    } finally {
      setSubmitting(false);
    }
  }

  async function handleCreateChannel() {
    if (!currentProject) return;

    if (!channelForm.displayName || !channelForm.email) {
      toast.error('Display name and email are required');
      return;
    }

    setSubmitting(true);
    try {
      await createNotificationChannel(
        channelForm.type,
        channelForm.displayName,
        { email_address: channelForm.email },
        channelForm.description,
        currentProject
      );

      toast.success('Notification channel created successfully');
      setShowCreateChannelModal(false);
      setChannelForm({
        type: 'email',
        displayName: '',
        description: '',
        email: '',
      });
      await fetchData();
    } catch (err: unknown) {
      toast.error(err instanceof Error ? err.message : 'Failed to create notification channel');
    } finally {
      setSubmitting(false);
    }
  }

  async function handleDeleteAlert(policy: AlertPolicy) {
    if (!confirm(`Delete alert policy "${policy.displayName}"?`)) {
      return;
    }

    if (!currentProject) return;

    const policyId = getPolicyId(policy.name);
    setDeleting(policyId);
    try {
      await deleteAlertPolicy(policyId, currentProject);
      toast.success('Alert policy deleted');
      await fetchData();
    } catch (err: unknown) {
      toast.error(err instanceof Error ? err.message : 'Failed to delete policy');
    } finally {
      setDeleting(null);
    }
  }

  async function handleDeleteChannel(channel: NotificationChannel) {
    if (!confirm(`Delete notification channel "${channel.displayName}"?`)) {
      return;
    }

    if (!currentProject) return;

    const channelId = getChannelId(channel.name);
    setDeleting(channelId);
    try {
      await deleteNotificationChannel(channelId, currentProject);
      toast.success('Notification channel deleted');
      await fetchData();
    } catch (err: unknown) {
      toast.error(err instanceof Error ? err.message : 'Failed to delete channel');
    } finally {
      setDeleting(null);
    }
  }

  const enabledAlerts = alertPolicies.filter(p => p.enabled).length;
  const activeChannels = notificationChannels.filter(c => c.enabled).length;

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <div className="border-b border-gray-200 bg-white px-6 py-4">
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-xl font-semibold text-gray-900">Cloud Monitoring</h1>
            <p className="mt-0.5 text-sm text-gray-500">{currentProject}</p>
          </div>
          <div className="flex items-center gap-3">
            <button
              onClick={fetchData}
              className="inline-flex items-center gap-2 rounded-md border border-gray-300 bg-white px-3 py-1.5 text-sm text-gray-700 hover:bg-gray-50"
            >
              <RefreshCw className="h-4 w-4" />
              Refresh
            </button>
            {activeTab === 'metrics' && (
              <button
                onClick={() => setShowCreateMetricModal(true)}
                className="inline-flex items-center gap-2 rounded-md bg-blue-600 px-4 py-1.5 text-sm font-medium text-white hover:bg-blue-700"
              >
                <Plus className="h-4 w-4" />
                Create Metric
              </button>
            )}
            {activeTab === 'alerts' && (
              <button
                onClick={() => setShowCreateAlertModal(true)}
                className="inline-flex items-center gap-2 rounded-md bg-blue-600 px-4 py-1.5 text-sm font-medium text-white hover:bg-blue-700"
              >
                <Plus className="h-4 w-4" />
                Create Alert
              </button>
            )}
            {activeTab === 'channels' && (
              <button
                onClick={() => setShowCreateChannelModal(true)}
                className="inline-flex items-center gap-2 rounded-md bg-blue-600 px-4 py-1.5 text-sm font-medium text-white hover:bg-blue-700"
              >
                <Plus className="h-4 w-4" />
                Create Channel
              </button>
            )}
          </div>
        </div>

        {/* Tabs */}
        <div className="mt-4 flex gap-6 border-b border-gray-200">
          <button
            onClick={() => setActiveTab('metrics')}
            className={`pb-3 px-1 border-b-2 font-medium text-sm ${
              activeTab === 'metrics'
                ? 'border-blue-600 text-blue-600'
                : 'border-transparent text-gray-500 hover:text-gray-700'
            }`}
          >
            <Activity className="inline h-4 w-4 mr-1" />
            Metric Descriptors
          </button>
          <button
            onClick={() => setActiveTab('alerts')}
            className={`pb-3 px-1 border-b-2 font-medium text-sm ${
              activeTab === 'alerts'
                ? 'border-blue-600 text-blue-600'
                : 'border-transparent text-gray-500 hover:text-gray-700'
            }`}
          >
            <AlertTriangle className="inline h-4 w-4 mr-1" />
            Alert Policies
          </button>
          <button
            onClick={() => setActiveTab('channels')}
            className={`pb-3 px-1 border-b-2 font-medium text-sm ${
              activeTab === 'channels'
                ? 'border-blue-600 text-blue-600'
                : 'border-transparent text-gray-500 hover:text-gray-700'
            }`}
          >
            <Bell className="inline h-4 w-4 mr-1" />
            Notification Channels
          </button>
        </div>
      </div>

      {/* Content */}
      <div className="px-6 py-6">
        {/* Stats */}
        <div className="mb-6 grid grid-cols-1 gap-4 sm:grid-cols-3">
          <div className="rounded-lg border border-gray-200 bg-white p-4">
            <p className="text-xs uppercase tracking-wide text-gray-500">Metric Descriptors</p>
            <p className="mt-1 text-3xl font-bold text-gray-900">{metricDescriptors.length}</p>
          </div>
          <div className="rounded-lg border border-gray-200 bg-white p-4">
            <p className="text-xs uppercase tracking-wide text-gray-500">Alert Policies</p>
            <p className="mt-1 text-3xl font-bold text-blue-600">
              {enabledAlerts} / {alertPolicies.length}
            </p>
          </div>
          <div className="rounded-lg border border-gray-200 bg-white p-4">
            <p className="text-xs uppercase tracking-wide text-gray-500">Notification Channels</p>
            <p className="mt-1 text-3xl font-bold text-green-600">
              {activeChannels} / {notificationChannels.length}
            </p>
          </div>
        </div>

        {loading ? (
          <div className="flex items-center justify-center py-16">
            <Loader2 className="h-8 w-8 animate-spin text-blue-500" />
          </div>
        ) : error ? (
          <div className="rounded-lg border border-red-200 bg-red-50 p-4 text-red-700">{error}</div>
        ) : (
          <>
            {/* Metric Descriptors Tab */}
            {activeTab === 'metrics' && (
              <div className="overflow-hidden rounded-lg border border-gray-200 bg-white">
                {metricDescriptors.length === 0 ? (
                  <div className="py-16 text-center">
                    <Activity className="mx-auto h-12 w-12 text-gray-400" />
                    <p className="mt-2 font-medium text-gray-600">No metric descriptors</p>
                    <p className="mt-1 text-sm text-gray-400">Create your first metric descriptor</p>
                  </div>
                ) : (
                  <table className="w-full text-sm">
                    <thead>
                      <tr className="border-b border-gray-200 bg-gray-50 text-left">
                        <th className="px-4 py-3 font-medium text-gray-600">Type</th>
                        <th className="px-4 py-3 font-medium text-gray-600">Display Name</th>
                        <th className="px-4 py-3 font-medium text-gray-600">Kind</th>
                        <th className="px-4 py-3 font-medium text-gray-600">Value Type</th>
                        <th className="px-4 py-3 font-medium text-gray-600">Unit</th>
                      </tr>
                    </thead>
                    <tbody className="divide-y divide-gray-100">
                      {metricDescriptors.map((metric) => (
                        <tr key={metric.type} className="hover:bg-gray-50">
                          <td className="px-4 py-3 font-mono text-xs text-gray-900">{metric.type}</td>
                          <td className="px-4 py-3 font-medium text-gray-900">{metric.displayName}</td>
                          <td className="px-4 py-3 text-gray-600">{metric.metricKind}</td>
                          <td className="px-4 py-3 text-gray-600">{metric.valueType}</td>
                          <td className="px-4 py-3 text-gray-600">{metric.unit}</td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                )}
              </div>
            )}

            {/* Alert Policies Tab */}
            {activeTab === 'alerts' && (
              <div className="overflow-hidden rounded-lg border border-gray-200 bg-white">
                {alertPolicies.length === 0 ? (
                  <div className="py-16 text-center">
                    <AlertTriangle className="mx-auto h-12 w-12 text-gray-400" />
                    <p className="mt-2 font-medium text-gray-600">No alert policies</p>
                    <p className="mt-1 text-sm text-gray-400">Create your first alert policy</p>
                  </div>
                ) : (
                  <table className="w-full text-sm">
                    <thead>
                      <tr className="border-b border-gray-200 bg-gray-50 text-left">
                        <th className="px-4 py-3 font-medium text-gray-600">Name</th>
                        <th className="px-4 py-3 font-medium text-gray-600">Conditions</th>
                        <th className="px-4 py-3 font-medium text-gray-600">Channels</th>
                        <th className="px-4 py-3 font-medium text-gray-600">Status</th>
                        <th className="px-4 py-3 font-medium text-gray-600">Actions</th>
                      </tr>
                    </thead>
                    <tbody className="divide-y divide-gray-100">
                      {alertPolicies.map((policy) => {
                        const policyId = getPolicyId(policy.name);
                        return (
                          <tr key={policy.name} className="hover:bg-gray-50">
                            <td className="px-4 py-3 font-medium text-gray-900">{policy.displayName}</td>
                            <td className="px-4 py-3 text-gray-600">{policy.conditions.length}</td>
                            <td className="px-4 py-3 text-gray-600">
                              {policy.notificationChannels?.length || 0}
                            </td>
                            <td className="px-4 py-3">
                              {policy.enabled ? (
                                <span className="inline-flex items-center gap-1 rounded-full bg-green-100 px-2.5 py-0.5 text-xs font-medium text-green-800">
                                  <CheckCircle2 className="h-3 w-3" />
                                  Enabled
                                </span>
                              ) : (
                                <span className="inline-flex items-center gap-1 rounded-full bg-gray-100 px-2.5 py-0.5 text-xs font-medium text-gray-800">
                                  <XCircle className="h-3 w-3" />
                                  Disabled
                                </span>
                              )}
                            </td>
                            <td className="px-4 py-3">
                              <button
                                onClick={() => handleDeleteAlert(policy)}
                                disabled={deleting === policyId}
                                className="rounded p-1 text-gray-500 hover:bg-red-50 hover:text-red-600 disabled:opacity-50"
                                title="Delete"
                              >
                                {deleting === policyId ? (
                                  <Loader2 className="h-4 w-4 animate-spin" />
                                ) : (
                                  <Trash2 className="h-4 w-4" />
                                )}
                              </button>
                            </td>
                          </tr>
                        );
                      })}
                    </tbody>
                  </table>
                )}
              </div>
            )}

            {/* Notification Channels Tab */}
            {activeTab === 'channels' && (
              <div className="overflow-hidden rounded-lg border border-gray-200 bg-white">
                {notificationChannels.length === 0 ? (
                  <div className="py-16 text-center">
                    <Bell className="mx-auto h-12 w-12 text-gray-400" />
                    <p className="mt-2 font-medium text-gray-600">No notification channels</p>
                    <p className="mt-1 text-sm text-gray-400">Create your first notification channel</p>
                  </div>
                ) : (
                  <table className="w-full text-sm">
                    <thead>
                      <tr className="border-b border-gray-200 bg-gray-50 text-left">
                        <th className="px-4 py-3 font-medium text-gray-600">Name</th>
                        <th className="px-4 py-3 font-medium text-gray-600">Type</th>
                        <th className="px-4 py-3 font-medium text-gray-600">Description</th>
                        <th className="px-4 py-3 font-medium text-gray-600">Status</th>
                        <th className="px-4 py-3 font-medium text-gray-600">Actions</th>
                      </tr>
                    </thead>
                    <tbody className="divide-y divide-gray-100">
                      {notificationChannels.map((channel) => {
                        const channelId = getChannelId(channel.name);
                        return (
                          <tr key={channel.name} className="hover:bg-gray-50">
                            <td className="px-4 py-3 font-medium text-gray-900">{channel.displayName}</td>
                            <td className="px-4 py-3 text-gray-600">{channel.type}</td>
                            <td className="px-4 py-3 text-gray-600">{channel.description || '-'}</td>
                            <td className="px-4 py-3">
                              {channel.enabled ? (
                                <span className="inline-flex items-center gap-1 rounded-full bg-green-100 px-2.5 py-0.5 text-xs font-medium text-green-800">
                                  <CheckCircle2 className="h-3 w-3" />
                                  Enabled
                                </span>
                              ) : (
                                <span className="inline-flex items-center gap-1 rounded-full bg-gray-100 px-2.5 py-0.5 text-xs font-medium text-gray-800">
                                  <XCircle className="h-3 w-3" />
                                  Disabled
                                </span>
                              )}
                            </td>
                            <td className="px-4 py-3">
                              <button
                                onClick={() => handleDeleteChannel(channel)}
                                disabled={deleting === channelId}
                                className="rounded p-1 text-gray-500 hover:bg-red-50 hover:text-red-600 disabled:opacity-50"
                                title="Delete"
                              >
                                {deleting === channelId ? (
                                  <Loader2 className="h-4 w-4 animate-spin" />
                                ) : (
                                  <Trash2 className="h-4 w-4" />
                                )}
                              </button>
                            </td>
                          </tr>
                        );
                      })}
                    </tbody>
                  </table>
                )}
              </div>
            )}
          </>
        )}
      </div>

      {/* Create Metric Modal */}
      {showCreateMetricModal && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black bg-opacity-50 p-4">
          <div className="w-full max-w-lg rounded-lg bg-white p-6 shadow-xl">
            <h3 className="text-lg font-semibold text-gray-900">Create Metric Descriptor</h3>
            <p className="mt-1 text-sm text-gray-500">Define a new metric type</p>

            <div className="mt-4 space-y-4">
              <div>
                <label className="block text-sm font-medium text-gray-700">Metric Type *</label>
                <input
                  type="text"
                  value={metricForm.type}
                  onChange={(e) => setMetricForm({ ...metricForm, type: e.target.value })}
                  placeholder="custom.googleapis.com/my-metric"
                  className="mt-1 w-full rounded-md border border-gray-300 px-3 py-2 text-sm"
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700">Display Name *</label>
                <input
                  type="text"
                  value={metricForm.displayName}
                  onChange={(e) => setMetricForm({ ...metricForm, displayName: e.target.value })}
                  placeholder="My Metric"
                  className="mt-1 w-full rounded-md border border-gray-300 px-3 py-2 text-sm"
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700">Description</label>
                <input
                  type="text"
                  value={metricForm.description}
                  onChange={(e) => setMetricForm({ ...metricForm, description: e.target.value })}
                  placeholder="Optional description"
                  className="mt-1 w-full rounded-md border border-gray-300 px-3 py-2 text-sm"
                />
              </div>

              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700">Metric Kind</label>
                  <select
                    value={metricForm.metricKind}
                    onChange={(e) => setMetricForm({ ...metricForm, metricKind: e.target.value as MetricKind })}
                    className="mt-1 w-full rounded-md border border-gray-300 px-3 py-2 text-sm"
                  >
                    {Object.values(MetricKind).map((kind) => (
                      <option key={kind} value={kind}>{kind}</option>
                    ))}
                  </select>
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700">Value Type</label>
                  <select
                    value={metricForm.valueType}
                    onChange={(e) => setMetricForm({ ...metricForm, valueType: e.target.value as ValueType })}
                    className="mt-1 w-full rounded-md border border-gray-300 px-3 py-2 text-sm"
                  >
                    {Object.values(ValueType).map((type) => (
                      <option key={type} value={type}>{type}</option>
                    ))}
                  </select>
                </div>
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700">Unit</label>
                <input
                  type="text"
                  value={metricForm.unit}
                  onChange={(e) => setMetricForm({ ...metricForm, unit: e.target.value })}
                  placeholder="1, s, By, etc."
                  className="mt-1 w-full rounded-md border border-gray-300 px-3 py-2 text-sm"
                />
              </div>
            </div>

            <div className="mt-6 flex justify-end gap-3">
              <button
                onClick={() => {
                  setShowCreateMetricModal(false);
                  setMetricForm({
                    type: '',
                    displayName: '',
                    description: '',
                    metricKind: MetricKind.GAUGE,
                    valueType: ValueType.DOUBLE,
                    unit: '1',
                  });
                }}
                disabled={submitting}
                className="rounded-md border border-gray-300 bg-white px-4 py-2 text-sm font-medium text-gray-700 hover:bg-gray-50"
              >
                Cancel
              </button>
              <button
                onClick={handleCreateMetric}
                disabled={submitting || !metricForm.type || !metricForm.displayName}
                className="inline-flex items-center gap-2 rounded-md bg-blue-600 px-4 py-2 text-sm font-medium text-white hover:bg-blue-700 disabled:opacity-50"
              >
                {submitting && <Loader2 className="h-4 w-4 animate-spin" />}
                Create Metric
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Create Alert Modal */}
      {showCreateAlertModal && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black bg-opacity-50 p-4">
          <div className="w-full max-w-lg rounded-lg bg-white p-6 shadow-xl">
            <h3 className="text-lg font-semibold text-gray-900">Create Alert Policy</h3>
            <p className="mt-1 text-sm text-gray-500">Configure alerting conditions</p>

            <div className="mt-4 space-y-4">
              <div>
                <label className="block text-sm font-medium text-gray-700">Display Name *</label>
                <input
                  type="text"
                  value={alertForm.displayName}
                  onChange={(e) => setAlertForm({ ...alertForm, displayName: e.target.value })}
                  placeholder="High CPU Usage Alert"
                  className="mt-1 w-full rounded-md border border-gray-300 px-3 py-2 text-sm"
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700">Metric Filter *</label>
                <input
                  type="text"
                  value={alertForm.filter}
                  onChange={(e) => setAlertForm({ ...alertForm, filter: e.target.value })}
                  placeholder='metric.type="compute.googleapis.com/instance/cpu/utilization"'
                  className="mt-1 w-full rounded-md border border-gray-300 px-3 py-2 text-sm font-mono"
                />
              </div>

              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700">Threshold Value</label>
                  <input
                    type="number"
                    value={alertForm.threshold}
                    onChange={(e) => setAlertForm({ ...alertForm, threshold: parseFloat(e.target.value) || 0 })}
                    className="mt-1 w-full rounded-md border border-gray-300 px-3 py-2 text-sm"
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700">Duration</label>
                  <input
                    type="text"
                    value={alertForm.duration}
                    onChange={(e) => setAlertForm({ ...alertForm, duration: e.target.value })}
                    placeholder="60s"
                    className="mt-1 w-full rounded-md border border-gray-300 px-3 py-2 text-sm"
                  />
                </div>
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700">Documentation</label>
                <textarea
                  value={alertForm.documentation}
                  onChange={(e) => setAlertForm({ ...alertForm, documentation: e.target.value })}
                  rows={3}
                  placeholder="Alert documentation..."
                  className="mt-1 w-full rounded-md border border-gray-300 px-3 py-2 text-sm"
                />
              </div>
            </div>

            <div className="mt-6 flex justify-end gap-3">
              <button
                onClick={() => {
                  setShowCreateAlertModal(false);
                  setAlertForm({
                    displayName: '',
                    filter: '',
                    threshold: 80,
                    duration: '60s',
                    documentation: '',
                  });
                }}
                disabled={submitting}
                className="rounded-md border border-gray-300 bg-white px-4 py-2 text-sm font-medium text-gray-700 hover:bg-gray-50"
              >
                Cancel
              </button>
              <button
                onClick={handleCreateAlert}
                disabled={submitting || !alertForm.displayName || !alertForm.filter}
                className="inline-flex items-center gap-2 rounded-md bg-blue-600 px-4 py-2 text-sm font-medium text-white hover:bg-blue-700 disabled:opacity-50"
              >
                {submitting && <Loader2 className="h-4 w-4 animate-spin" />}
                Create Alert
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Create Channel Modal */}
      {showCreateChannelModal && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black bg-opacity-50 p-4">
          <div className="w-full max-w-lg rounded-lg bg-white p-6 shadow-xl">
            <h3 className="text-lg font-semibold text-gray-900">Create Notification Channel</h3>
            <p className="mt-1 text-sm text-gray-500">Configure notification delivery</p>

            <div className="mt-4 space-y-4">
              <div>
                <label className="block text-sm font-medium text-gray-700">Display Name *</label>
                <input
                  type="text"
                  value={channelForm.displayName}
                  onChange={(e) => setChannelForm({ ...channelForm, displayName: e.target.value })}
                  placeholder="Team Email"
                  className="mt-1 w-full rounded-md border border-gray-300 px-3 py-2 text-sm"
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700">Type</label>
                <select
                  value={channelForm.type}
                  onChange={(e) => setChannelForm({ ...channelForm, type: e.target.value })}
                  className="mt-1 w-full rounded-md border border-gray-300 px-3 py-2 text-sm"
                >
                  <option value="email">Email</option>
                  <option value="slack">Slack</option>
                  <option value="webhook">Webhook</option>
                </select>
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700">Email Address *</label>
                <input
                  type="email"
                  value={channelForm.email}
                  onChange={(e) => setChannelForm({ ...channelForm, email: e.target.value })}
                  placeholder="team@example.com"
                  className="mt-1 w-full rounded-md border border-gray-300 px-3 py-2 text-sm"
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700">Description</label>
                <input
                  type="text"
                  value={channelForm.description}
                  onChange={(e) => setChannelForm({ ...channelForm, description: e.target.value })}
                  placeholder="Optional description"
                  className="mt-1 w-full rounded-md border border-gray-300 px-3 py-2 text-sm"
                />
              </div>
            </div>

            <div className="mt-6 flex justify-end gap-3">
              <button
                onClick={() => {
                  setShowCreateChannelModal(false);
                  setChannelForm({
                    type: 'email',
                    displayName: '',
                    description: '',
                    email: '',
                  });
                }}
                disabled={submitting}
                className="rounded-md border border-gray-300 bg-white px-4 py-2 text-sm font-medium text-gray-700 hover:bg-gray-50"
              >
                Cancel
              </button>
              <button
                onClick={handleCreateChannel}
                disabled={submitting || !channelForm.displayName || !channelForm.email}
                className="inline-flex items-center gap-2 rounded-md bg-blue-600 px-4 py-2 text-sm font-medium text-white hover:bg-blue-700 disabled:opacity-50"
              >
                {submitting && <Loader2 className="h-4 w-4 animate-spin" />}
                Create Channel
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
 
                            {alert.notificationChannels?.length || 0} channel(s)
                          </div>
                        </div>
                        <span
                          className={`px-3 py-1 rounded-full text-xs font-semibold ${getAlertState(
                            alert.state || 'OK'
                          )}`}
                        >
                          {alert.state || 'OK'}
                        </span>
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </section>

            {/* Auto-Scaling Section */}
            <section>
              <h2 className="text-xl font-bold text-white mb-4 flex items-center gap-2">
                <Settings size={20} className="text-green-400" />
                Auto-Scaling Policies ({autoscalers.length})
              </h2>
              {autoscalers.length === 0 ? (
                <div className="p-6 bg-slate-800/50 border border-slate-700 rounded-lg text-gray-400 text-center">
                  No autoscaling policies configured
                </div>
              ) : (
                <div className="space-y-3">
                  {autoscalers.map((autoscaler, idx) => (
                    <div
                      key={idx}
                      className="p-4 bg-slate-800/50 border border-slate-700 rounded-lg hover:border-cyan-500 transition"
                    >
                      <div className="flex items-start justify-between">
                        <div className="flex-1">
                          <div className="font-semibold text-white">{autoscaler.name?.split('/').pop()}</div>
                          <div className="text-sm text-gray-400 mt-2 space-y-1">
                            <div>Target: {autoscaler.target?.split('/').pop()}</div>
                            <div>
                              Size: {autoscaler.currentSize} / {autoscaler.minReplicas}-{autoscaler.maxReplicas}
                            </div>
                            <div>Last Action: {autoscaler.lastAction || 'None'}</div>
                          </div>
                        </div>
                        <div className="text-right">
                          {getScalingStatus(autoscaler)}
                          <div className="text-xs text-gray-500 mt-2">
                            {autoscaler.enabled ? 'Enabled' : 'Disabled'}
                          </div>
                        </div>
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </section>
          </>
        )}
      </div>
    </div>
  );
};

export default MonitoringDashboard;
