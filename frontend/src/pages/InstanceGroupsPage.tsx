import { useState, useEffect, useCallback } from 'react';
import { useProject } from '../contexts/ProjectContext';
import {
  listInstanceGroups,
  createInstanceGroup,
  deleteInstanceGroup,
  addInstancesToGroup,
  removeInstancesFromGroup,
  listGroupMembers,
  InstanceGroupItem,
  GroupMember,
  NamedPort,
} from '../api/instanceGroups';
import { listInstances } from '../api/autoscaling';
import toast from 'react-hot-toast';
import {
  Plus,
  RefreshCw,
  Trash2,
  Loader2,
  ChevronDown,
  ChevronUp,
  Server,
  Settings,
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

export default function InstanceGroupsPage() {
  const { currentProject } = useProject();

  const [selectedZone, setSelectedZone] = useState(ZONES[0]);
  const [groups, setGroups] = useState<InstanceGroupItem[]>([]);
  const [availableInstances, setAvailableInstances] = useState<{ name: string; status: string }[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [deleting, setDeleting] = useState<string | null>(null);
  const [expandedGroup, setExpandedGroup] = useState<string | null>(null);
  const [groupMembers, setGroupMembers] = useState<Record<string, GroupMember[]>>({});

  // Modals
  const [showCreateModal, setShowCreateModal] = useState(false);
  const [showAddMembersModal, setShowAddMembersModal] = useState(false);
  const [selectedGroupName, setSelectedGroupName] = useState<string | null>(null);

  // Form states
  const [formData, setFormData] = useState({
    name: '',
    description: '',
  });
  const [selectedMembers, setSelectedMembers] = useState<string[]>([]);
  const [submitting, setSubmitting] = useState(false);

  const fetchGroups = useCallback(async () => {
    if (!currentProject || !selectedZone) return;

    try {
      setLoading(true);
      const data = await listInstanceGroups(selectedZone, currentProject);
      setGroups(data);
      setError(null);
    } catch (err: unknown) {
      const message = err instanceof Error ? err.message : 'Failed to load instance groups';
      setError(message);
      toast.error(message);
    } finally {
      setLoading(false);
    }
  }, [currentProject, selectedZone]);

  const fetchInstances = useCallback(async () => {
    if (!currentProject || !selectedZone) return;

    try {
      const instances = await listInstances(selectedZone, currentProject);
      setAvailableInstances(instances);
    } catch {
      setAvailableInstances([]);
    }
  }, [currentProject, selectedZone]);

  const fetchGroupMembers = useCallback(
    async (groupName: string) => {
      if (!currentProject || !selectedZone) return;

      try {
        const members = await listGroupMembers(selectedZone, groupName, currentProject);
        setGroupMembers((prev) => ({
          ...prev,
          [groupName]: members,
        }));
      } catch (err: unknown) {
        console.error(`Failed to fetch members for ${groupName}:`, err);
      }
    },
    [currentProject, selectedZone]
  );

  useEffect(() => {
    fetchGroups();
    fetchInstances();
  }, [fetchGroups, fetchInstances]);

  const handleCreateGroup = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!formData.name.trim()) {
      toast.error('Group name is required');
      return;
    }

    setSubmitting(true);
    try {
      await createInstanceGroup(
        selectedZone,
        formData.name,
        formData.description || undefined,
        [],
        currentProject
      );
      toast.success('Instance group created successfully');
      setShowCreateModal(false);
      setFormData({ name: '', description: '' });
      await fetchGroups();
    } catch (err: unknown) {
      const message = err instanceof Error ? err.message : 'Failed to create instance group';
      toast.error(message);
    } finally {
      setSubmitting(false);
    }
  };

  const handleDeleteGroup = async (groupName: string) => {
    if (!window.confirm(`Delete instance group "${groupName}"?`)) return;

    setDeleting(groupName);
    try {
      await deleteInstanceGroup(selectedZone, groupName, currentProject);
      toast.success('Instance group deleted');
      await fetchGroups();
    } catch (err: unknown) {
      const message = err instanceof Error ? err.message : 'Failed to delete instance group';
      toast.error(message);
    } finally {
      setDeleting(null);
    }
  };

  const handleAddMembers = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!selectedGroupName || selectedMembers.length === 0) {
      toast.error('Select at least one instance');
      return;
    }

    setSubmitting(true);
    try {
      await addInstancesToGroup(
        selectedZone,
        selectedGroupName,
        selectedMembers,
        currentProject
      );
      toast.success(`Added ${selectedMembers.length} instance(s) to group`);
      setShowAddMembersModal(false);
      setSelectedMembers([]);
      setSelectedGroupName(null);
      await fetchGroups();
      await fetchGroupMembers(selectedGroupName);
    } catch (err: unknown) {
      const message = err instanceof Error ? err.message : 'Failed to add instances';
      toast.error(message);
    } finally {
      setSubmitting(false);
    }
  };

  const handleExpandGroup = async (groupName: string) => {
    if (expandedGroup === groupName) {
      setExpandedGroup(null);
    } else {
      setExpandedGroup(groupName);
      await fetchGroupMembers(groupName);
    }
  };

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-3xl font-bold text-gray-900">Instance Groups</h1>
        <p className="mt-2 text-gray-600">Create and manage instance groups for autoscaling</p>
      </div>

      {/* Zone Selection & Actions */}
      <div className="flex items-center justify-between rounded-lg bg-white p-4 shadow-sm">
        <div>
          <label className="block text-sm font-medium text-gray-700">Zone</label>
          <select
            value={selectedZone}
            onChange={(e) => setSelectedZone(e.target.value)}
            className="mt-1 block rounded-md border border-gray-300 px-3 py-2 text-sm focus:border-blue-500 focus:outline-none"
          >
            {ZONES.map((zone) => (
              <option key={zone} value={zone}>
                {zone}
              </option>
            ))}
          </select>
        </div>

        <div className="flex gap-2">
          <button
            onClick={() => {
              fetchGroups();
              fetchInstances();
            }}
            className="inline-flex items-center gap-2 rounded-md bg-gray-100 px-4 py-2 text-sm font-medium text-gray-700 hover:bg-gray-200"
          >
            <RefreshCw className="h-4 w-4" />
            Refresh
          </button>
          <button
            onClick={() => setShowCreateModal(true)}
            className="inline-flex items-center gap-2 rounded-md bg-blue-600 px-4 py-2 text-sm font-medium text-white hover:bg-blue-700"
          >
            <Plus className="h-4 w-4" />
            Create Group
          </button>
        </div>
      </div>

      {/* Error Message */}
      {error && (
        <div className="rounded-md bg-red-50 p-4">
          <p className="text-sm text-red-800">{error}</p>
        </div>
      )}

      {/* Loading State */}
      {loading && (
        <div className="flex h-64 items-center justify-center">
          <Loader2 className="h-8 w-8 animate-spin text-blue-600" />
        </div>
      )}

      {/* Groups List */}
      {!loading && (
        <div className="rounded-lg bg-white shadow-sm overflow-hidden">
          {groups.length === 0 ? (
            <div className="p-8 text-center">
              <Server className="mx-auto h-12 w-12 text-gray-400" />
              <p className="mt-2 text-gray-600">No instance groups created yet</p>
            </div>
          ) : (
            <div className="divide-y">
              {groups.map((group) => (
                <div key={group.name} className="p-4">
                  <div
                    className="flex cursor-pointer items-center justify-between"
                    onClick={() => handleExpandGroup(group.name)}
                  >
                    <div className="flex items-center gap-3 flex-1">
                      <button className="rounded-md bg-gray-100 p-2">
                        {expandedGroup === group.name ? (
                          <ChevronUp className="h-4 w-4" />
                        ) : (
                          <ChevronDown className="h-4 w-4" />
                        )}
                      </button>
                      <div>
                        <h3 className="font-semibold text-gray-900">{group.name}</h3>
                        {group.description && (
                          <p className="text-sm text-gray-600">{group.description}</p>
                        )}
                      </div>
                    </div>

                    <div className="flex items-center gap-6">
                      <div className="text-right">
                        <p className="text-sm font-medium text-gray-900">
                          {group.size} instance{group.size !== 1 ? 's' : ''}
                        </p>
                        <p className="text-xs text-gray-500">{group.status}</p>
                      </div>

                      <div className="flex gap-2">
                        <button
                          onClick={(e) => {
                            e.stopPropagation();
                            setSelectedGroupName(group.name);
                            setShowAddMembersModal(true);
                          }}
                          className="rounded-md bg-blue-50 px-3 py-1 text-xs font-medium text-blue-700 hover:bg-blue-100"
                        >
                          Add Members
                        </button>
                        <button
                          onClick={(e) => {
                            e.stopPropagation();
                            handleDeleteGroup(group.name);
                          }}
                          disabled={deleting === group.name}
                          className="rounded-md bg-red-50 px-3 py-1 text-xs font-medium text-red-700 hover:bg-red-100 disabled:opacity-50"
                        >
                          {deleting === group.name ? (
                            <Loader2 className="inline h-3 w-3 animate-spin" />
                          ) : (
                            <Trash2 className="inline h-3 w-3" />
                          )}
                        </button>
                      </div>
                    </div>
                  </div>

                  {/* Expanded Members */}
                  {expandedGroup === group.name && (
                    <div className="mt-4 ml-12 border-l-2 border-gray-200 pl-4">
                      <h4 className="text-sm font-medium text-gray-900 mb-3">Members:</h4>
                      {groupMembers[group.name]?.length === 0 ? (
                        <p className="text-sm text-gray-500">No instances in this group</p>
                      ) : (
                        <div className="space-y-2">
                          {groupMembers[group.name]?.map((member) => {
                            const instanceName = member.instance.split('/').pop() || member.instance;
                            return (
                              <div
                                key={instanceName}
                                className="flex items-center justify-between bg-gray-50 p-2 rounded text-sm"
                              >
                                <span className="text-gray-900">{instanceName}</span>
                                <span className="text-xs bg-green-100 text-green-800 px-2 py-1 rounded">
                                  {member.status}
                                </span>
                              </div>
                            );
                          })}
                        </div>
                      )}
                    </div>
                  )}
                </div>
              ))}
            </div>
          )}
        </div>
      )}

      {/* Create Group Modal */}
      {showCreateModal && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black bg-opacity-50 p-4">
          <div className="w-full max-w-md rounded-lg bg-white p-6 shadow-xl">
            <h3 className="text-lg font-semibold text-gray-900">Create Instance Group</h3>

            <form onSubmit={handleCreateGroup} className="mt-4 space-y-4">
              <div>
                <label className="block text-sm font-medium text-gray-700">Group Name *</label>
                <input
                  type="text"
                  value={formData.name}
                  onChange={(e) => setFormData({ ...formData, name: e.target.value })}
                  placeholder="my-group"
                  className="mt-1 block w-full rounded-md border border-gray-300 px-3 py-2 text-sm focus:border-blue-500 focus:outline-none"
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700">Description</label>
                <input
                  type="text"
                  value={formData.description}
                  onChange={(e) => setFormData({ ...formData, description: e.target.value })}
                  placeholder="Optional description"
                  className="mt-1 block w-full rounded-md border border-gray-300 px-3 py-2 text-sm focus:border-blue-500 focus:outline-none"
                />
              </div>

              <div className="mt-6 flex justify-end gap-3">
                <button
                  type="button"
                  onClick={() => setShowCreateModal(false)}
                  disabled={submitting}
                  className="rounded-md border border-gray-300 bg-white px-4 py-2 text-sm font-semibold text-gray-900 hover:bg-gray-50 disabled:opacity-50"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  disabled={submitting}
                  className="rounded-md bg-blue-600 px-4 py-2 text-sm font-semibold text-white hover:bg-blue-700 disabled:opacity-50 inline-flex items-center gap-2"
                >
                  {submitting && <Loader2 className="h-4 w-4 animate-spin" />}
                  Create
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* Add Members Modal */}
      {showAddMembersModal && selectedGroupName && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black bg-opacity-50 p-4">
          <div className="w-full max-w-md rounded-lg bg-white p-6 shadow-xl">
            <h3 className="text-lg font-semibold text-gray-900">Add Instances to {selectedGroupName}</h3>

            <form onSubmit={handleAddMembers} className="mt-4 space-y-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Select Instances
                </label>
                <div className="space-y-2 max-h-48 overflow-y-auto">
                  {availableInstances.length === 0 ? (
                    <p className="text-sm text-gray-500">No instances available</p>
                  ) : (
                    availableInstances.map((instance) => (
                      <label key={instance.name} className="flex items-center gap-2">
                        <input
                          type="checkbox"
                          checked={selectedMembers.includes(instance.name)}
                          onChange={(e) => {
                            if (e.target.checked) {
                              setSelectedMembers([...selectedMembers, instance.name]);
                            } else {
                              setSelectedMembers(
                                selectedMembers.filter((name) => name !== instance.name)
                              );
                            }
                          }}
                          className="rounded border-gray-300"
                        />
                        <span className="text-sm text-gray-900">{instance.name}</span>
                        <span className="text-xs text-gray-500">({instance.status})</span>
                      </label>
                    ))
                  )}
                </div>
              </div>

              <div className="mt-6 flex justify-end gap-3">
                <button
                  type="button"
                  onClick={() => {
                    setShowAddMembersModal(false);
                    setSelectedMembers([]);
                  }}
                  disabled={submitting}
                  className="rounded-md border border-gray-300 bg-white px-4 py-2 text-sm font-semibold text-gray-900 hover:bg-gray-50 disabled:opacity-50"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  disabled={submitting || selectedMembers.length === 0}
                  className="rounded-md bg-blue-600 px-4 py-2 text-sm font-semibold text-white hover:bg-blue-700 disabled:opacity-50 inline-flex items-center gap-2"
                >
                  {submitting && <Loader2 className="h-4 w-4 animate-spin" />}
                  Add {selectedMembers.length} Instance{selectedMembers.length !== 1 ? 's' : ''}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
}
