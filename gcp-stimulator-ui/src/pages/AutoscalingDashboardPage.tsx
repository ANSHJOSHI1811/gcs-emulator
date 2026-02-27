import { useState, useEffect, useCallback } from 'react';
import { useProject } from '../contexts/ProjectContext';
import {
  listAutoscalers,
  createAutoscaler,
  updateAutoscaler,
  deleteAutoscaler,
  getScalingHistory,
  AutoscalingPolicy,
  ScalingRule,
  ScalingAction,
  ScalingMetricType,
} from '../api/autoscaling';
import toast from 'react-hot-toast';
import {
  Plus,
  RefreshCw,
  Trash2,
  Loader2,
  ChevronDown,
  ChevronUp,
  Edit,
  History,
  TrendingUp,
  TrendingDown,
  Minus,
  Settings,
  Activity,
} from 'lucide-react';

const ZONES = [
  'us-central1-a',
  'us-central1-b',
  'us-central1-c',
  'us-east1-b',
  'us-east1-c',
  'us-west1-a',
  'us-west1-b',
];

export default function AutoscalingDashboardPage() {
  const { currentProject } = useProject();

  const [selectedZone, setSelectedZone] = useState(ZONES[0]);
  const [policies, setPolicies] = useState<AutoscalingPolicy[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [deleting, setDeleting] = useState<string | null>(null);
  const [expandedPolicy, setExpandedPolicy] = useState<string | null>(null);

  // Modals
  const [showCreateModal, setShowCreateModal] = useState(false);
  const [showEditModal, setShowEditModal] = useState(false);
  const [showHistoryModal, setShowHistoryModal] = useState(false);

  // Form states
  const [formData, setFormData] = useState({
    name: '',
    target: '',
    description: '',
    minReplicas: 1,
    maxReplicas: 10,
  });
  const [scalingRules, setScalingRules] = useState<Partial<ScalingRule>[]>([
    {
      metricType: ScalingMetricType.CPU_UTILIZATION,
      targetValue: 70,
      scaleUpThreshold: 80,
      scaleDownThreshold: 20,
      cooldownSeconds: 300,
    },
  ]);
  const [submitting, setSubmitting] = useState(false);
  const [editingPolicy, setEditingPolicy] = useState<AutoscalingPolicy | null>(null);

  // History
  const [historyPolicy, setHistoryPolicy] = useState<AutoscalingPolicy | null>(null);
  const [scalingHistory, setScalingHistory] = useState<ScalingAction[]>([]);
  const [loadingHistory, setLoadingHistory] = useState(false);

  const fetchPolicies = useCallback(async () => {
    if (!currentProject || !selectedZone) return;

    try {
      setLoading(true);
      const data = await listAutoscalers(selectedZone, currentProject);
      setPolicies(data);
      setError(null);
    } catch (err: unknown) {
      const message = err instanceof Error ? err.message : 'Failed to load autoscaling policies';
      setError(message);
      toast.error(message);
    } finally {
      setLoading(false);
    }
  }, [currentProject, selectedZone]);

  useEffect(() => {
    fetchPolicies();
  }, [fetchPolicies]);

  function getPolicyId(policyName: string): string {
    const parts = policyName.split('/');
    return parts[parts.length - 1] || policyName;
  }

  function resetForm() {
    setFormData({
      name: '',
      target: '',
      description: '',
      minReplicas: 1,
      maxReplicas: 10,
    });
    setScalingRules([
      {
        metricType: ScalingMetricType.CPU_UTILIZATION,
        targetValue: 70,
        scaleUpThreshold: 80,
        scaleDownThreshold: 20,
        cooldownSeconds: 300,
      },
    ]);
  }

  async function handleCreate() {
    if (!currentProject || !selectedZone) return;

    if (!formData.name.trim() || !formData.target.trim()) {
      toast.error('Name and target are required');
      return;
    }

    if (formData.minReplicas >= formData.maxReplicas) {
      toast.error('Min replicas must be less than max replicas');
      return;
    }

    setSubmitting(true);
    try {
      await createAutoscaler(
        selectedZone,
        formData.name,
        formData.target,
        formData.minReplicas,
        formData.maxReplicas,
        scalingRules,
        formData.description || undefined,
        currentProject
      );
      toast.success('Autoscaling policy created successfully');
      setShowCreateModal(false);
      resetForm();
      await fetchPolicies();
    } catch (err: unknown) {
      toast.error(err instanceof Error ? err.message : 'Failed to create policy');
    } finally {
      setSubmitting(false);
    }
  }

  async function handleEdit() {
    if (!currentProject || !selectedZone || !editingPolicy) return;

    if (formData.minReplicas >= formData.maxReplicas) {
      toast.error('Min replicas must be less than max replicas');
      return;
    }

    setSubmitting(true);
    try {
      const policyId = getPolicyId(editingPolicy.name);
      await updateAutoscaler(
        selectedZone,
        policyId,
        {
          minReplicas: formData.minReplicas,
          maxReplicas: formData.maxReplicas,
          scalingRules,
        },
        currentProject
      );
      toast.success('Autoscaling policy updated successfully');
      setShowEditModal(false);
      setEditingPolicy(null);
      resetForm();
      await fetchPolicies();
    } catch (err: unknown) {
      toast.error(err instanceof Error ? err.message : 'Failed to update policy');
    } finally {
      setSubmitting(false);
    }
  }

  async function handleDelete(policy: AutoscalingPolicy) {
    if (!confirm(`Delete autoscaling policy "${getPolicyId(policy.name)}"?`)) {
      return;
    }

    if (!currentProject || !selectedZone) return;

    const policyId = getPolicyId(policy.name);
    setDeleting(policyId);
    try {
      await deleteAutoscaler(selectedZone, policyId, currentProject);
      toast.success('Autoscaling policy deleted');
      await fetchPolicies();
    } catch (err: unknown) {
      toast.error(err instanceof Error ? err.message : 'Failed to delete policy');
    } finally {
      setDeleting(null);
    }
  }

  async function handleToggleEnabled(policy: AutoscalingPolicy) {
    if (!currentProject || !selectedZone) return;

    const policyId = getPolicyId(policy.name);
    try {
      await updateAutoscaler(
        selectedZone,
        policyId,
        { enabled: !policy.enabled },
        currentProject
      );
      toast.success(policy.enabled ? 'Policy disabled' : 'Policy enabled');
      await fetchPolicies();
    } catch (err: unknown) {
      toast.error(err instanceof Error ? err.message : 'Failed to toggle policy');
    }
  }

  function openEditModal(policy: AutoscalingPolicy) {
    setEditingPolicy(policy);
    setFormData({
      name: getPolicyId(policy.name),
      target: policy.target,
      description: policy.description || '',
      minReplicas: policy.minReplicas,
      maxReplicas: policy.maxReplicas,
    });
    setScalingRules(
      policy.scalingRules.map(rule => ({
        metricType: rule.metricType,
        targetValue: rule.targetValue,
        scaleUpThreshold: rule.scaleUpThreshold,
        scaleDownThreshold: rule.scaleDownThreshold,
        cooldownSeconds: rule.cooldownSeconds,
        metricName: rule.metricName,
      }))
    );
    setShowEditModal(true);
  }

  async function openHistoryModal(policy: AutoscalingPolicy) {
    setHistoryPolicy(policy);
    setShowHistoryModal(true);
    setLoadingHistory(true);

    try {
      const policyId = getPolicyId(policy.name);
      const history = await getScalingHistory(selectedZone, policyId, 50, currentProject);
      setScalingHistory(history);
    } catch (err: unknown) {
      toast.error(err instanceof Error ? err.message : 'Failed to load history');
    } finally {
      setLoadingHistory(false);
    }
  }

  function addScalingRule() {
    setScalingRules([
      ...scalingRules,
      {
        metricType: ScalingMetricType.CPU_UTILIZATION,
        targetValue: 70,
        scaleUpThreshold: 80,
        scaleDownThreshold: 20,
        cooldownSeconds: 300,
      },
    ]);
  }

  function removeScalingRule(index: number) {
    setScalingRules(scalingRules.filter((_, i) => i !== index));
  }

  function updateScalingRule(index: number, field: keyof ScalingRule, value: any) {
    const updated = [...scalingRules];
    updated[index] = { ...updated[index], [field]: value };
    setScalingRules(updated);
  }

  function getStatusBadge(policy: AutoscalingPolicy) {
    if (!policy.enabled) {
      return (
        <span className="inline-flex items-center gap-1 rounded-full bg-gray-100 px-2.5 py-0.5 text-xs font-medium text-gray-800">
          Disabled
        </span>
      );
    }

    if (policy.currentSize < policy.minReplicas || policy.currentSize > policy.maxReplicas) {
      return (
        <span className="inline-flex items-center gap-1 rounded-full bg-yellow-100 px-2.5 py-0.5 text-xs font-medium text-yellow-800">
          <Activity className="h-3 w-3" />
          Adjusting
        </span>
      );
    }

    if (policy.currentSize === policy.targetSize) {
      return (
        <span className="inline-flex items-center gap-1 rounded-full bg-green-100 px-2.5 py-0.5 text-xs font-medium text-green-800">
          <Minus className="h-3 w-3" />
          Stable
        </span>
      );
    }

    if (policy.currentSize < (policy.targetSize || policy.currentSize)) {
      return (
        <span className="inline-flex items-center gap-1 rounded-full bg-blue-100 px-2.5 py-0.5 text-xs font-medium text-blue-800">
          <TrendingUp className="h-3 w-3" />
          Scaling Up
        </span>
      );
    }

    return (
      <span className="inline-flex items-center gap-1 rounded-full bg-orange-100 px-2.5 py-0.5 text-xs font-medium text-orange-800">
        <TrendingDown className="h-3 w-3" />
        Scaling Down
      </span>
    );
  }

  const activePolicies = policies.filter(p => p.enabled).length;
  const totalManagedReplicas = policies.reduce((sum, p) => sum + p.currentSize, 0);

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <div className="border-b border-gray-200 bg-white px-6 py-4">
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-xl font-semibold text-gray-900">Autoscaling</h1>
            <p className="mt-0.5 text-sm text-gray-500">{currentProject}</p>
          </div>
          <div className="flex items-center gap-3">
            <select
              value={selectedZone}
              onChange={(e) => setSelectedZone(e.target.value)}
              className="rounded-md border border-gray-300 bg-white px-3 py-1.5 text-sm text-gray-700 focus:border-blue-500 focus:outline-none focus:ring-1 focus:ring-blue-500"
            >
              {ZONES.map((zone) => (
                <option key={zone} value={zone}>
                  {zone}
                </option>
              ))}
            </select>
            <button
              onClick={fetchPolicies}
              className="inline-flex items-center gap-2 rounded-md border border-gray-300 bg-white px-3 py-1.5 text-sm text-gray-700 hover:bg-gray-50"
            >
              <RefreshCw className="h-4 w-4" />
              Refresh
            </button>
            <button
              onClick={() => {
                resetForm();
                setShowCreateModal(true);
              }}
              className="inline-flex items-center gap-2 rounded-md bg-blue-600 px-4 py-1.5 text-sm font-medium text-white hover:bg-blue-700"
            >
              <Plus className="h-4 w-4" />
              Create Policy
            </button>
          </div>
        </div>
      </div>

      {/* Stats */}
      <div className="px-6 py-6">
        <div className="mb-6 grid grid-cols-1 gap-4 sm:grid-cols-3">
          <div className="rounded-lg border border-gray-200 bg-white p-4">
            <p className="text-xs uppercase tracking-wide text-gray-500">Total Policies</p>
            <p className="mt-1 text-3xl font-bold text-gray-900">{policies.length}</p>
          </div>
          <div className="rounded-lg border border-gray-200 bg-white p-4">
            <p className="text-xs uppercase tracking-wide text-gray-500">Active Policies</p>
            <p className="mt-1 text-3xl font-bold text-green-600">{activePolicies}</p>
          </div>
          <div className="rounded-lg border border-gray-200 bg-white p-4">
            <p className="text-xs uppercase tracking-wide text-gray-500">Managed Replicas</p>
            <p className="mt-1 text-3xl font-bold text-blue-600">{totalManagedReplicas}</p>
          </div>
        </div>

        {/* Policies Table */}
        <div className="overflow-hidden rounded-lg border border-gray-200 bg-white">
          {loading ? (
            <div className="flex items-center justify-center py-16">
              <Loader2 className="h-8 w-8 animate-spin text-blue-500" />
            </div>
          ) : error ? (
            <div className="p-4 text-center text-red-600">{error}</div>
          ) : policies.length === 0 ? (
            <div className="py-16 text-center">
              <Settings className="mx-auto h-12 w-12 text-gray-400" />
              <p className="mt-2 font-medium text-gray-600">No autoscaling policies</p>
              <p className="mt-1 text-sm text-gray-400">Create your first policy to get started</p>
            </div>
          ) : (
            <table className="w-full text-sm">
              <thead>
                <tr className="border-b border-gray-200 bg-gray-50 text-left">
                  <th className="px-4 py-3 font-medium text-gray-600">Name</th>
                  <th className="px-4 py-3 font-medium text-gray-600">Target</th>
                  <th className="px-4 py-3 font-medium text-gray-600">Replicas</th>
                  <th className="px-4 py-3 font-medium text-gray-600">Status</th>
                  <th className="px-4 py-3 font-medium text-gray-600">Enabled</th>
                  <th className="px-4 py-3 font-medium text-gray-600">Actions</th>
                  <th className="w-8 px-4 py-3"></th>
                </tr>
              </thead>
              <tbody className="divide-y divide-gray-100">
                {policies.map((policy) => {
                  const policyId = getPolicyId(policy.name);
                  const isExpanded = expandedPolicy === policyId;

                  return (
                    <>
                      <tr key={policy.name} className="hover:bg-gray-50">
                        <td className="px-4 py-3 font-medium text-gray-900">{policyId}</td>
                        <td className="px-4 py-3 text-gray-600">
                          {policy.target.split('/').pop() || policy.target}
                        </td>
                        <td className="px-4 py-3">
                          <span className="font-medium text-gray-900">{policy.currentSize}</span>
                          <span className="text-gray-400"> / </span>
                          <span className="text-gray-600">
                            {policy.minReplicas}-{policy.maxReplicas}
                          </span>
                        </td>
                        <td className="px-4 py-3">{getStatusBadge(policy)}</td>
                        <td className="px-4 py-3">
                          <button
                            onClick={() => handleToggleEnabled(policy)}
                            className={`relative inline-flex h-6 w-11 items-center rounded-full transition-colors ${
                              policy.enabled ? 'bg-blue-600' : 'bg-gray-200'
                            }`}
                          >
                            <span
                              className={`inline-block h-4 w-4 transform rounded-full bg-white transition-transform ${
                                policy.enabled ? 'translate-x-6' : 'translate-x-1'
                              }`}
                            />
                          </button>
                        </td>
                        <td className="px-4 py-3">
                          <div className="flex items-center gap-2">
                            <button
                              onClick={() => openEditModal(policy)}
                              className="rounded p-1 text-gray-500 hover:bg-blue-50 hover:text-blue-600"
                              title="Edit"
                            >
                              <Edit className="h-4 w-4" />
                            </button>
                            <button
                              onClick={() => openHistoryModal(policy)}
                              className="rounded p-1 text-gray-500 hover:bg-purple-50 hover:text-purple-600"
                              title="View history"
                            >
                              <History className="h-4 w-4" />
                            </button>
                            <button
                              onClick={() => handleDelete(policy)}
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
                          </div>
                        </td>
                        <td className="px-4 py-3">
                          <button
                            onClick={() => setExpandedPolicy(isExpanded ? null : policyId)}
                            className="text-gray-400 hover:text-gray-600"
                          >
                            {isExpanded ? (
                              <ChevronUp className="h-4 w-4" />
                            ) : (
                              <ChevronDown className="h-4 w-4" />
                            )}
                          </button>
                        </td>
                      </tr>
                      {isExpanded && (
                        <tr>
                          <td colSpan={7} className="border-t border-gray-100 bg-gray-50 px-4 py-4">
                            <div className="space-y-2">
                              <h4 className="text-sm font-medium text-gray-700">Scaling Rules</h4>
                              {policy.scalingRules.map((rule, idx) => (
                                <div
                                  key={idx}
                                  className="rounded-md border border-gray-200 bg-white p-3 text-xs"
                                >
                                  <div className="grid grid-cols-2 gap-2 sm:grid-cols-4">
                                    <div>
                                      <span className="font-medium text-gray-600">Metric:</span>
                                      <p className="text-gray-900">{rule.metricType}</p>
                                    </div>
                                    <div>
                                      <span className="font-medium text-gray-600">Target:</span>
                                      <p className="text-gray-900">{rule.targetValue}%</p>
                                    </div>
                                    <div>
                                      <span className="font-medium text-gray-600">Thresholds:</span>
                                      <p className="text-gray-900">
                                        ↑ {rule.scaleUpThreshold}% / ↓ {rule.scaleDownThreshold}%
                                      </p>
                                    </div>
                                    <div>
                                      <span className="font-medium text-gray-600">Cooldown:</span>
                                      <p className="text-gray-900">{rule.cooldownSeconds}s</p>
                                    </div>
                                  </div>
                                </div>
                              ))}
                            </div>
                          </td>
                        </tr>
                      )}
                    </>
                  );
                })}
              </tbody>
            </table>
          )}
        </div>
      </div>

      {/* Create Modal */}
      {showCreateModal && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black bg-opacity-50 p-4">
          <div className="max-h-[90vh] w-full max-w-2xl overflow-y-auto rounded-lg bg-white p-6 shadow-xl">
            <h3 className="text-lg font-semibold text-gray-900">Create Autoscaling Policy</h3>
            <p className="mt-1 text-sm text-gray-500">Configure autoscaling for your resources</p>

            <div className="mt-4 space-y-4">
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700">Policy Name *</label>
                  <input
                    type="text"
                    value={formData.name}
                    onChange={(e) => setFormData({ ...formData, name: e.target.value })}
                    placeholder="my-autoscaler"
                    className="mt-1 w-full rounded-md border border-gray-300 px-3 py-2 text-sm focus:border-blue-500 focus:outline-none focus:ring-1 focus:ring-blue-500"
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700">Target *</label>
                  <input
                    type="text"
                    value={formData.target}
                    onChange={(e) => setFormData({ ...formData, target: e.target.value })}
                    placeholder="instance-group-name"
                    className="mt-1 w-full rounded-md border border-gray-300 px-3 py-2 text-sm focus:border-blue-500 focus:outline-none focus:ring-1 focus:ring-blue-500"
                  />
                </div>
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700">Description</label>
                <input
                  type="text"
                  value={formData.description}
                  onChange={(e) => setFormData({ ...formData, description: e.target.value })}
                  placeholder="Optional description"
                  className="mt-1 w-full rounded-md border border-gray-300 px-3 py-2 text-sm focus:border-blue-500 focus:outline-none focus:ring-1 focus:ring-blue-500"
                />
              </div>

              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700">Min Replicas *</label>
                  <input
                    type="number"
                    min="1"
                    value={formData.minReplicas}
                    onChange={(e) =>
                      setFormData({ ...formData, minReplicas: parseInt(e.target.value) || 1 })
                    }
                    className="mt-1 w-full rounded-md border border-gray-300 px-3 py-2 text-sm focus:border-blue-500 focus:outline-none focus:ring-1 focus:ring-blue-500"
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700">Max Replicas *</label>
                  <input
                    type="number"
                    min="1"
                    value={formData.maxReplicas}
                    onChange={(e) =>
                      setFormData({ ...formData, maxReplicas: parseInt(e.target.value) || 1 })
                    }
                    className="mt-1 w-full rounded-md border border-gray-300 px-3 py-2 text-sm focus:border-blue-500 focus:outline-none focus:ring-1 focus:ring -blue-500"
                  />
                </div>
              </div>

              <div>
                <div className="mb-2 flex items-center justify-between">
                  <label className="block text-sm font-medium text-gray-700">Scaling Rules</label>
                  <button
                    onClick={addScalingRule}
                    className="text-sm text-blue-600 hover:text-blue-700"
                  >
                    + Add Rule
                  </button>
                </div>
                {scalingRules.map((rule, idx) => (
                  <div
                    key={idx}
                    className="mb-3 rounded-md border border-gray-200 bg-gray-50 p-3"
                  >
                    <div className="mb-2 flex items-center justify-between">
                      <span className="text-xs font-medium text-gray-600">Rule {idx + 1}</span>
                      {scalingRules.length > 1 && (
                        <button
                          onClick={() => removeScalingRule(idx)}
                          className="text-xs text-red-600 hover:text-red-700"
                        >
                          Remove
                        </button>
                      )}
                    </div>
                    <div className="grid grid-cols-2 gap-2">
                      <div className="col-span-2">
                        <label className="block text-xs text-gray-600">Metric Type</label>
                        <select
                          value={rule.metricType}
                          onChange={(e) =>
                            updateScalingRule(idx, 'metricType', e.target.value as ScalingMetricType)
                          }
                          className="mt-1 w-full rounded-md border border-gray-300 px-2 py-1.5 text-sm"
                        >
                          {Object.values(ScalingMetricType).map((type) => (
                            <option key={type} value={type}>
                              {type.replace(/_/g, ' ')}
                            </option>
                          ))}
                        </select>
                      </div>
                      <div>
                        <label className="block text-xs text-gray-600">Target Value (%)</label>
                        <input
                          type="number"
                          min="0"
                          max="100"
                          value={rule.targetValue}
                          onChange={(e) =>
                            updateScalingRule(idx, 'targetValue', parseInt(e.target.value) || 0)
                          }
                          className="mt-1 w-full rounded-md border border-gray-300 px-2 py-1.5 text-sm"
                        />
                      </div>
                      <div>
                        <label className="block text-xs text-gray-600">Cooldown (s)</label>
                        <input
                          type="number"
                          min="0"
                          value={rule.cooldownSeconds}
                          onChange={(e) =>
                            updateScalingRule(idx, 'cooldownSeconds', parseInt(e.target.value) || 0)
                          }
                          className="mt-1 w-full rounded-md border border-gray-300 px-2 py-1.5 text-sm"
                        />
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            </div>

            <div className="mt-6 flex justify-end gap-3">
              <button
                onClick={() => {
                  setShowCreateModal(false);
                  resetForm();
                }}
                disabled={submitting}
                className="rounded-md border border-gray-300 bg-white px-4 py-2 text-sm font-medium text-gray-700 hover:bg-gray-50 disabled:opacity-50"
              >
                Cancel
              </button>
              <button
                onClick={handleCreate}
                disabled={submitting || !formData.name || !formData.target}
                className="inline-flex items-center gap-2 rounded-md bg-blue-600 px-4 py-2 text-sm font-medium text-white hover:bg-blue-700 disabled:opacity-50"
              >
                {submitting && <Loader2 className="h-4 w-4 animate-spin" />}
                Create Policy
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Edit Modal */}
      {showEditModal && editingPolicy && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black bg-opacity-50 p-4">
          <div className="max-h-[90vh] w-full max-w-2xl overflow-y-auto rounded-lg bg-white p-6 shadow-xl">
            <h3 className="text-lg font-semibold text-gray-900">Edit Autoscaling Policy</h3>
            <p className="mt-1 text-sm text-gray-500">{getPolicyId(editingPolicy.name)}</p>

            <div className="mt-4 space-y-4">
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700">Min Replicas</label>
                  <input
                    type="number"
                    min="1"
                    value={formData.minReplicas}
                    onChange={(e) =>
                      setFormData({ ...formData, minReplicas: parseInt(e.target.value) || 1 })
                    }
                    className="mt-1 w-full rounded-md border border-gray-300 px-3 py-2 text-sm"
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700">Max Replicas</label>
                  <input
                    type="number"
                    min="1"
                    value={formData.maxReplicas}
                    onChange={(e) =>
                      setFormData({ ...formData, maxReplicas: parseInt(e.target.value) || 1 })
                    }
                    className="mt-1 w-full rounded-md border border-gray-300 px-3 py-2 text-sm"
                  />
                </div>
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700">Scaling Rules</label>
                {scalingRules.map((rule, idx) => (
                  <div key={idx} className="mt-2 rounded-md border border-gray-200 p-3">
                    <div className="grid grid-cols-2 gap-2">
                      <div>
                        <label className="block text-xs text-gray-600">Target Value (%)</label>
                        <input
                          type="number"
                          value={rule.targetValue}
                          onChange={(e) =>
                            updateScalingRule(idx, 'targetValue', parseInt(e.target.value) || 0)
                          }
                          className="mt-1 w-full rounded-md border border-gray-300 px-2 py-1 text-sm"
                        />
                      </div>
                      <div>
                        <label className="block text-xs text-gray-600">Cooldown (s)</label>
                        <input
                          type="number"
                          value={rule.cooldownSeconds}
                          onChange={(e) =>
                            updateScalingRule(idx, 'cooldownSeconds', parseInt(e.target.value) || 0)
                          }
                          className="mt-1 w-full rounded-md border border-gray-300 px-2 py-1 text-sm"
                        />
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            </div>

            <div className="mt-6 flex justify-end gap-3">
              <button
                onClick={() => {
                  setShowEditModal(false);
                  setEditingPolicy(null);
                  resetForm();
                }}
                disabled={submitting}
                className="rounded-md border border-gray-300 bg-white px-4 py-2 text-sm font-medium text-gray-700 hover:bg-gray-50"
              >
                Cancel
              </button>
              <button
                onClick={handleEdit}
                disabled={submitting}
                className="inline-flex items-center gap-2 rounded-md bg-blue-600 px-4 py-2 text-sm font-medium text-white hover:bg-blue-700"
              >
                {submitting && <Loader2 className="h-4 w-4 animate-spin" />}
                Save Changes
              </button>
            </div>
          </div>
        </div>
      )}

      {/* History Modal */}
      {showHistoryModal && historyPolicy && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black bg-opacity-50 p-4">
          <div className="max-h-[90vh] w-full max-w-3xl overflow-y-auto rounded-lg bg-white p-6 shadow-xl">
            <h3 className="text-lg font-semibold text-gray-900">Scaling History</h3>
            <p className="mt-1 text-sm text-gray-500">{getPolicyId(historyPolicy.name)}</p>

            <div className="mt-4">
              {loadingHistory ? (
                <div className="flex items-center justify-center py-12">
                  <Loader2 className="h-6 w-6 animate-spin text-blue-500" />
                </div>
              ) : scalingHistory.length === 0 ? (
                <p className="py-8 text-center text-sm text-gray-500">No scaling history yet</p>
              ) : (
                <div className="space-y-3">
                  {scalingHistory.map((action, idx) => (
                    <div key={idx} className="flex items-start gap-3 rounded-lg border border-gray-200 p-3">
                      <div className="mt-1">
                        {action.action === 'SCALE_UP' ? (
                          <TrendingUp className="h-5 w-5 text-blue-600" />
                        ) : action.action === 'SCALE_DOWN' ? (
                          <TrendingDown className="h-5 w-5 text-orange-600" />
                        ) : (
                          <Minus className="h-5 w-5 text-gray-400" />
                        )}
                      </div>
                      <div className="flex-1">
                        <div className="flex items-center justify-between">
                          <span className="font-medium text-gray-900">
                            {action.action.replace(/_/g, ' ')}
                          </span>
                          <span className="text-xs text-gray-500">
                            {new Date(action.timestamp).toLocaleString()}
                          </span>
                        </div>
                        <p className="mt-1 text-sm text-gray-600">
                          Size: {action.oldSize} → {action.newSize}
                        </p>
                        <p className="text-xs text-gray-500">{action.reason}</p>
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </div>

            <div className="mt-6 flex justify-end">
              <button
                onClick={() => {
                  setShowHistoryModal(false);
                  setHistoryPolicy(null);
                  setScalingHistory([]);
                }}
                className="rounded-md bg-gray-900 px-4 py-2 text-sm font-medium text-white hover:bg-gray-800"
              >
                Close
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
