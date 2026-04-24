import { useEffect, useState } from 'react';
import { useProject } from '../contexts/ProjectContext';
import { Shield, Plus, Users, Key, BookOpen, Trash2, Download, X, Clock } from 'lucide-react';
import { apiClient } from '../api/client';
import { Modal, ModalFooter, ModalButton } from '../components/Modal';
import { FormField, Input, Textarea } from '../components/FormFields';

interface ServiceAccount {
  name: string;
  email: string;
  uniqueId: string;
  displayName: string;
  disabled: boolean;
  description?: string;
  projectId: string;
}

interface SAKey {
  name: string;
  keyId: string;
  serviceAccountEmail?: string;
  keyType?: string;
  keyAlgorithm?: string;
  validAfterTime?: string;
  disabled?: boolean;
  privateKeyData?: string;
}

interface IamBinding {
  principal: string;
  role: string;
  condition?: string;
}

interface GCPRole {
  name: string;
  title: string;
  description?: string;
  stage?: string;
  includedPermissions?: string[];
}

type ActiveTab = 'members' | 'roles' | 'serviceaccounts' | 'keys';

const IAMDashboardPage = () => {
  const { currentProject } = useProject();
  const [activeTab, setActiveTab] = useState<ActiveTab>('members');

  // Service Accounts
  const [serviceAccounts, setServiceAccounts] = useState<ServiceAccount[]>([]);
  const [loading, setLoading] = useState(true);
  const [showCreateModal, setShowCreateModal] = useState(false);
  const [showDetailsModal, setShowDetailsModal] = useState(false);
  const [selectedAccount, setSelectedAccount] = useState<ServiceAccount | null>(null);
  const [createLoading, setCreateLoading] = useState(false);
  const [deleteLoading, setDeleteLoading] = useState(false);
  const [formData, setFormData] = useState({ accountId: '', displayName: '', description: '' });

  // SA Keys
  const [saKeys, setSaKeys] = useState<SAKey[]>([]);
  const [keysLoading, setKeysLoading] = useState(false);
  const [selectedSAForKeys, setSelectedSAForKeys] = useState<string>('');
  const [creatingKey, setCreatingKey] = useState(false);
  const [newKeyData, setNewKeyData] = useState<string | null>(null);

  // IAM Bindings
  const [bindings, setBindings] = useState<IamBinding[]>([]);
  const [bindingsLoading, setBindingsLoading] = useState(false);
  const [showAddBinding, setShowAddBinding] = useState(false);
  const [bindingForm, setBindingForm] = useState({ principal: '', role: '' });
  const [addingBinding, setAddingBinding] = useState(false);

  // Roles
  const [predefinedRoles, setPredefinedRoles] = useState<GCPRole[]>([]);
  const [customRoles, setCustomRoles] = useState<GCPRole[]>([]);
  const [rolesLoading, setRolesLoading] = useState(false);
  const [showCreateRole, setShowCreateRole] = useState(false);
  const [roleForm, setRoleForm] = useState({ roleId: '', title: '', description: '', permissions: '' });
  const [creatingRole, setCreatingRole] = useState(false);
  const [roleSearch, setRoleSearch] = useState('');

  // Computed values
  const activeAccounts = serviceAccounts.filter(acc => !acc.disabled).length;
  const recentAccounts = [...serviceAccounts].slice(0, 5);

  useEffect(() => {
    loadServiceAccounts();
    const interval = setInterval(loadServiceAccounts, 10000);
    return () => clearInterval(interval);
  }, [currentProject]);

  useEffect(() => {
    if (activeTab === 'members') loadBindings();
    if (activeTab === 'roles') loadRoles();
    if (activeTab === 'keys' && serviceAccounts.length > 0 && !selectedSAForKeys) {
      setSelectedSAForKeys(serviceAccounts[0].email);
    }
  }, [activeTab, currentProject]);

  useEffect(() => {
    if (activeTab === 'keys' && selectedSAForKeys) loadKeys(selectedSAForKeys);
  }, [selectedSAForKeys, activeTab]);

  const loadServiceAccounts = async () => {
    try {
      const res = await apiClient.get(`/v1/projects/${currentProject}/serviceAccounts`);
      setServiceAccounts(res.data.accounts || []);
    } catch { /* silent */ } finally {
      setLoading(false);
    }
  };

  const loadBindings = async () => {
    setBindingsLoading(true);
    try {
      const res = await apiClient.post(`/v1/projects/${currentProject}:getIamPolicy`, {});
      const policy = res.data.policy || res.data;
      const rawBindings: Array<{ role: string; members?: string[] }> = policy.bindings || [];
      const flat: IamBinding[] = [];
      rawBindings.forEach(b => (b.members || []).forEach(m => flat.push({ principal: m, role: b.role })));
      setBindings(flat);
    } catch { /* silent */ } finally {
      setBindingsLoading(false);
    }
  };

  const loadRoles = async () => {
    setRolesLoading(true);
    try {
      const [predRes, custRes] = await Promise.all([
        apiClient.get(`/v1/roles`),
        apiClient.get(`/v1/projects/${currentProject}/roles`),
      ]);
      setPredefinedRoles(predRes.data.roles || []);
      setCustomRoles(custRes.data.roles || []);
    } catch { /* silent */ } finally {
      setRolesLoading(false);
    }
  };

  const loadKeys = async (email: string) => {
    setKeysLoading(true);
    try {
      const res = await apiClient.get(`/v1/projects/${currentProject}/serviceAccounts/${email}/keys`);
      setSaKeys(res.data.keys || []);
    } catch { setSaKeys([]); } finally {
      setKeysLoading(false);
    }
  };

  const handleCreateSA = async (e: React.FormEvent) => {
    e.preventDefault();
    setCreateLoading(true);
    try {
      await apiClient.post(`/v1/projects/${currentProject}/serviceAccounts`, {
        accountId: formData.accountId,
        serviceAccount: { displayName: formData.displayName, description: formData.description }
      });
      setShowCreateModal(false);
      setFormData({ accountId: '', displayName: '', description: '' });
      await loadServiceAccounts();
    } catch (err: any) {
      alert(err.response?.data?.detail || 'Failed to create service account');
    } finally { setCreateLoading(false); }
  };

  const handleDeleteSA = async (email: string) => {
    if (!confirm('Delete this service account?')) return;
    setDeleteLoading(true);
    try {
      await apiClient.delete(`/v1/projects/${currentProject}/serviceAccounts/${email}`);
      setShowDetailsModal(false);
      setSelectedAccount(null);
      await loadServiceAccounts();
    } catch (err: any) {
      alert(err.response?.data?.detail || 'Failed to delete service account');
    } finally { setDeleteLoading(false); }
  };

  const handleAddBinding = async () => {
    if (!bindingForm.principal || !bindingForm.role) return;
    setAddingBinding(true);
    try {
      await apiClient.post(`/v1/projects/${currentProject}/iam:addBinding`, bindingForm);
      setBindingForm({ principal: '', role: '' });
      setShowAddBinding(false);
      loadBindings();
    } catch (err: any) {
      alert(err.response?.data?.detail || 'Failed to add binding');
    } finally { setAddingBinding(false); }
  };

  const handleRemoveBinding = async (binding: IamBinding) => {
    if (!confirm(`Remove ${binding.principal} from ${binding.role}?`)) return;
    try {
      await apiClient.post(`/v1/projects/${currentProject}/iam:removeBinding`, binding);
      loadBindings();
    } catch (err: any) {
      alert(err.response?.data?.detail || 'Failed to remove binding');
    }
  };

  const handleCreateRole = async () => {
    if (!roleForm.roleId || !roleForm.title) return;
    setCreatingRole(true);
    try {
      await apiClient.post(`/v1/projects/${currentProject}/roles`, {
        roleId: roleForm.roleId,
        role: {
          title: roleForm.title,
          description: roleForm.description,
          includedPermissions: roleForm.permissions.split('\n').map(p => p.trim()).filter(Boolean),
        }
      });
      setShowCreateRole(false);
      setRoleForm({ roleId: '', title: '', description: '', permissions: '' });
      loadRoles();
    } catch (err: any) {
      alert(err.response?.data?.detail || 'Failed to create role');
    } finally { setCreatingRole(false); }
  };

  const handleCreateKey = async (email: string) => {
    setCreatingKey(true);
    try {
      const res = await apiClient.post(`/v1/projects/${currentProject}/serviceAccounts/${email}/keys`, {});
      setNewKeyData(res.data.privateKeyData || null);
      setSaKeys(prev => [res.data, ...prev]);
    } catch (err: any) {
      alert(err.response?.data?.detail || 'Failed to create key');
    } finally { setCreatingKey(false); }
  };

  const handleDeleteKey = async (key: SAKey, email: string) => {
    if (!confirm(`Delete key ${key.keyId?.substring(0, 12)}...?`)) return;
    try {
      await apiClient.delete(`/v1/projects/${currentProject}/serviceAccounts/${email}/keys/${key.keyId || key.name?.split('/').pop()}`);
      loadKeys(email);
    } catch (err: any) {
      alert(err.response?.data?.detail || 'Failed to delete key');
    }
  };

  const downloadKey = (keyData: string, email: string) => {
    const blob = new Blob([atob(keyData)], { type: 'application/json' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `${email.split('@')[0]}-key.json`;
    a.click();
    URL.revokeObjectURL(url);
  };

  const filteredPredefined = predefinedRoles.filter(r =>
    r.name.toLowerCase().includes(roleSearch.toLowerCase()) ||
    r.title.toLowerCase().includes(roleSearch.toLowerCase())
  );

  const tabs: Array<{ key: ActiveTab; label: string; icon: typeof Shield }> = [
    { key: 'members', label: 'Members & Permissions', icon: Users },
    { key: 'roles', label: 'Roles', icon: BookOpen },
    { key: 'serviceaccounts', label: 'Service Accounts', icon: Shield },
    { key: 'keys', label: 'Keys', icon: Key },
  ];

  return (
    <div className="min-h-screen bg-[#f8f9fa]">
      {/* Header */}
      <div className="bg-white border-b border-gray-200">
        <div className="max-w-[1280px] mx-auto px-8 py-6">
          <div className="flex items-start gap-4 mb-4">
            <div className="p-3 bg-blue-50 rounded-xl">
              <Shield className="w-8 h-8 text-blue-600" />
            </div>
            <div className="flex-1">
              <h1 className="text-[28px] font-bold text-gray-900 mb-1">IAM & Admin</h1>
              <p className="text-[14px] text-gray-600">Manage identities, roles, and access control for {currentProject}</p>
            </div>
            <div className="flex gap-2">
              {activeTab === 'serviceaccounts' && (
                <button onClick={() => setShowCreateModal(true)}
                  className="inline-flex items-center gap-2 px-4 h-10 bg-blue-600 text-white rounded-lg hover:bg-blue-700 text-[13px] font-medium">
                  <Plus className="w-4 h-4" /> Create Service Account
                </button>
              )}
              {activeTab === 'members' && (
                <button onClick={() => setShowAddBinding(true)}
                  className="inline-flex items-center gap-2 px-4 h-10 bg-blue-600 text-white rounded-lg hover:bg-blue-700 text-[13px] font-medium">
                  <Plus className="w-4 h-4" /> Grant Access
                </button>
              )}
              {activeTab === 'roles' && (
                <button onClick={() => setShowCreateRole(true)}
                  className="inline-flex items-center gap-2 px-4 h-10 bg-blue-600 text-white rounded-lg hover:bg-blue-700 text-[13px] font-medium">
                  <Plus className="w-4 h-4" /> Create Role
                </button>
              )}
            </div>
          </div>

          {/* Tabs */}
          <div className="flex gap-1">
            {tabs.map(({ key, label, icon: Icon }) => (
              <button key={key} onClick={() => setActiveTab(key)}
                className={`flex items-center gap-2 px-4 py-2 rounded-lg text-[13px] font-medium transition-colors ${
                  activeTab === key ? 'bg-blue-50 text-blue-700' : 'text-gray-600 hover:bg-gray-100'
                }`}>
                <Icon className="w-4 h-4" /> {label}
              </button>
            ))}
          </div>
        </div>
      </div>

      <div className="max-w-[1280px] mx-auto px-8 py-8">

        {/* Members & Permissions Tab */}
        {activeTab === 'members' && (
          <div className="space-y-6">
            {/* Quick Stats */}
            <div className="flex items-center gap-4 text-sm">
              <div className="flex items-center gap-2">
                <span className="text-gray-600">IAM Bindings:</span>
                <span className="px-3 py-1 bg-blue-50 text-blue-700 font-semibold rounded-md">
                  {bindings.length}
                </span>
              </div>
            </div>

            {/* IAM Bindings Table */}
            <div className="bg-white rounded-lg shadow-[0_1px_3px_rgba(0,0,0,0.07)]">
              <div className="px-6 py-4 border-b border-gray-200 flex items-center justify-between">
                <h2 className="text-base font-semibold text-gray-900">IAM Policy Bindings</h2>
                <button
                  onClick={() => setShowAddBinding(true)}
                  className="px-4 py-2 bg-blue-600 text-white text-sm font-medium rounded-md hover:bg-blue-700"
                >
                  Grant Access
                </button>
              </div>

              {bindingsLoading ? (
                <div className="p-12 text-center">
                  <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto"></div>
                  <p className="text-gray-600 mt-4 text-sm">Loading IAM bindings...</p>
                </div>
              ) : bindings.length === 0 ? (
                <div className="p-12 text-center">
                  <Shield className="w-16 h-16 text-gray-300 mx-auto mb-4" />
                  <h3 className="text-base font-medium text-gray-900 mb-2">No IAM bindings</h3>
                  <p className="text-sm text-gray-500 mb-6">
                    Grant access to members by assigning them roles
                  </p>
                </div>
              ) : (
                <div className="overflow-x-auto">
                  <table className="min-w-full divide-y divide-gray-200">
                    <thead className="bg-gray-50">
                      <tr>
                        <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                          Member
                        </th>
                        <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                          Role
                        </th>
                        <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                          Actions
                        </th>
                      </tr>
                    </thead>
                    <tbody className="bg-white divide-y divide-gray-200">
                      {bindings.map((binding, index) => (
                        <tr key={index} className="hover:bg-gray-50 transition-colors">
                          <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                            {binding.principal}
                          </td>
                          <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-600">
                            {binding.role}
                          </td>
                          <td className="px-6 py-4 whitespace-nowrap text-sm">
                            <button
                              onClick={() => handleRemoveBinding(binding)}
                              className="text-red-600 hover:text-red-700 font-medium"
                            >
                              Remove
                            </button>
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              )}
            </div>
          </div>
        )}

        {/* Roles Tab */}
        {activeTab === 'roles' && (
          <div className="space-y-6">
            {/* Quick Stats */}
            <div className="flex items-center gap-4 text-sm">
              <div className="flex items-center gap-2">
                <span className="text-gray-600">Custom Roles:</span>
                <span className="px-3 py-1 bg-purple-50 text-purple-700 font-semibold rounded-md">
                  {customRoles.length}
                </span>
              </div>
              <div className="flex items-center gap-2">
                <span className="text-gray-600">Predefined Roles:</span>
                <span className="px-3 py-1 bg-blue-50 text-blue-700 font-semibold rounded-md">
                  {predefinedRoles.length}
                </span>
              </div>
            </div>

            {/* Custom Roles Section */}
            <div className="bg-white rounded-lg shadow-[0_1px_3px_rgba(0,0,0,0.07)]">
              <div className="px-6 py-4 border-b border-gray-200 flex items-center justify-between">
                <h2 className="text-base font-semibold text-gray-900">Custom Roles</h2>
                <button
                  onClick={() => setShowCreateRole(true)}
                  className="px-4 py-2 bg-blue-600 text-white text-sm font-medium rounded-md hover:bg-blue-700"
                >
                  Create Role
                </button>
              </div>

              {rolesLoading ? (
                <div className="p-12 text-center">
                  <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto"></div>
                  <p className="text-gray-600 mt-4 text-sm">Loading roles...</p>
                </div>
              ) : customRoles.length === 0 ? (
                <div className="p-12 text-center">
                  <BookOpen className="w-16 h-16 text-gray-300 mx-auto mb-4" />
                  <h3 className="text-base font-medium text-gray-900 mb-2">No custom roles</h3>
                  <p className="text-sm text-gray-500 mb-6">
                    Create custom roles with specific permissions
                  </p>
                </div>
              ) : (
                <div className="overflow-x-auto">
                  <table className="min-w-full divide-y divide-gray-200">
                    <thead className="bg-gray-50">
                      <tr>
                        <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                          Role Name
                        </th>
                        <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                          Title
                        </th>
                        <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                          Permissions
                        </th>
                      </tr>
                    </thead>
                    <tbody className="bg-white divide-y divide-gray-200">
                      {customRoles.map((role) => (
                        <tr key={role.name} className="hover:bg-gray-50 transition-colors">
                          <td className="px-6 py-4 whitespace-nowrap text-sm font-medium text-gray-900">
                            {role.name}
                          </td>
                          <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-600">
                            {role.title}
                          </td>
                          <td className="px-6 py-4 text-sm text-gray-600">
                            {(role.includedPermissions || []).length} permissions
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              )}
            </div>

            {/* Predefined Roles Section */}
            <div className="bg-white rounded-lg shadow-[0_1px_3px_rgba(0,0,0,0.07)]">
              <div className="px-6 py-4 border-b border-gray-200">
                <h2 className="text-base font-semibold text-gray-900">Predefined Roles</h2>
              </div>

              {predefinedRoles.length === 0 ? (
                <div className="p-12 text-center">
                  <BookOpen className="w-16 h-16 text-gray-300 mx-auto mb-4" />
                  <p className="text-sm text-gray-500">Loading predefined roles...</p>
                </div>
              ) : (
                <div className="overflow-x-auto">
                  <table className="min-w-full divide-y divide-gray-200">
                    <thead className="bg-gray-50">
                      <tr>
                        <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                          Role Name
                        </th>
                        <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                          Title
                        </th>
                        <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                          Description
                        </th>
                      </tr>
                    </thead>
                    <tbody className="bg-white divide-y divide-gray-200">
                      {predefinedRoles.map((role) => (
                        <tr key={role.name} className="hover:bg-gray-50 transition-colors">
                          <td className="px-6 py-4 whitespace-nowrap text-sm font-medium text-gray-900">
                            {role.name}
                          </td>
                          <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-600">
                            {role.title}
                          </td>
                          <td className="px-6 py-4 text-sm text-gray-600">
                            {role.description}
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              )}
            </div>
          </div>
        )}

        {/* Service Accounts Tab */}
        {activeTab === 'serviceaccounts' && (
          <div className="space-y-6">
            {/* Quick Stats */}
            <div className="flex items-center gap-4 text-sm">
              <div className="flex items-center gap-2">
                <span className="text-gray-600">Service Accounts:</span>
                <span className="px-3 py-1 bg-blue-50 text-blue-700 font-semibold rounded-md">
                  {serviceAccounts.length}
                </span>
              </div>
              <div className="flex items-center gap-2">
                <span className="text-gray-600">Active:</span>
                <span className="px-3 py-1 bg-green-50 text-green-700 font-semibold rounded-md">
                  {activeAccounts}
                </span>
              </div>
            </div>

            {/* Service Accounts Table */}
            <div className="bg-white rounded-lg shadow-[0_1px_3px_rgba(0,0,0,0.07)]">
              <div className="px-6 py-4 border-b border-gray-200">
                <h2 className="text-base font-semibold text-gray-900">Service Accounts</h2>
              </div>

              {loading ? (
                <div className="p-12 text-center">
                  <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto"></div>
                  <p className="text-gray-600 mt-4 text-sm">Loading service accounts...</p>
                </div>
              ) : serviceAccounts.length === 0 ? (
                <div className="p-12 text-center">
                  <Shield className="w-16 h-16 text-gray-300 mx-auto mb-4" />
                  <h3 className="text-base font-medium text-gray-900 mb-2">No service accounts</h3>
                  <p className="text-sm text-gray-500 mb-6">
                    Create a service account to manage API access
                  </p>
                </div>
              ) : (
                <div className="overflow-x-auto">
                  <table className="min-w-full divide-y divide-gray-200">
                    <thead className="bg-gray-50">
                      <tr>
                        <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                          Email
                        </th>
                        <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                          Display Name
                        </th>
                        <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                          Status
                        </th>
                        <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                          Actions
                        </th>
                      </tr>
                    </thead>
                    <tbody className="bg-white divide-y divide-gray-200">
                      {serviceAccounts.map((account) => (
                        <tr key={account.uniqueId} className="hover:bg-gray-50 transition-colors">
                          <td className="px-6 py-4 whitespace-nowrap">
                            <button
                              onClick={() => {
                                setSelectedAccount(account);
                                setShowDetailsModal(true);
                              }}
                              className="flex items-center text-blue-600 hover:text-blue-700 font-medium text-sm"
                            >
                              <Users className="w-4 h-4 mr-2 text-gray-400" />
                              {account.email}
                            </button>
                          </td>
                          <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-600">
                            {account.displayName || '-'}
                          </td>
                          <td className="px-6 py-4 whitespace-nowrap">
                            <span
                              className={`px-2 py-1 text-xs font-medium rounded-full ${
                                account.disabled
                                  ? 'bg-red-100 text-red-800'
                                  : 'bg-green-100 text-green-800'
                              }`}
                            >
                              {account.disabled ? 'Disabled' : 'Active'}
                            </span>
                          </td>
                          <td className="px-6 py-4 whitespace-nowrap text-sm">
                            <button
                              onClick={() => handleDeleteSA(account.email)}
                              disabled={deleteLoading}
                              className="text-red-600 hover:text-red-700 font-medium disabled:opacity-50"
                            >
                              Delete
                            </button>
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              )}
            </div>

            {/* Recent Activity */}
            {recentAccounts.length > 0 && (
              <div className="bg-white rounded-lg shadow-[0_1px_3px_rgba(0,0,0,0.07)]">
                <div className="px-6 py-4 border-b border-gray-200">
                  <h2 className="text-base font-semibold text-gray-900 flex items-center gap-2">
                    <Clock className="w-4 h-4" />
                    Recent Activity
                  </h2>
                </div>
                <div className="p-6">
                  <div className="space-y-3">
                    {recentAccounts.map((account) => (
                      <div
                        key={account.uniqueId}
                        className="flex items-center justify-between py-3 border-b border-gray-100 last:border-0"
                      >
                        <div className="flex items-center gap-3">
                          <div className="w-8 h-8 bg-blue-50 rounded-full flex items-center justify-center">
                            <Users className="w-4 h-4 text-blue-600" />
                          </div>
                          <div>
                            <p className="text-sm font-medium text-gray-900">{account.email}</p>
                            <p className="text-xs text-gray-500">{account.displayName || 'No display name'}</p>
                          </div>
                        </div>
                        <span
                          className={`px-2 py-1 text-xs font-medium rounded-full ${
                            account.disabled
                              ? 'bg-red-100 text-red-800'
                              : 'bg-green-100 text-green-800'
                          }`}
                        >
                          {account.disabled ? 'Disabled' : 'Active'}
                        </span>
                      </div>
                    ))}
                  </div>
                </div>
              </div>
            )}
          </div>
        )}

        {/* Keys Tab */}
        {activeTab === 'keys' && (
          <div className="space-y-6">
            {/* Quick Stats */}
            <div className="flex items-center gap-4 text-sm">
              <div className="flex items-center gap-2">
                <span className="text-gray-600">Total Keys:</span>
                <span className="px-3 py-1 bg-blue-50 text-blue-700 font-semibold rounded-md">
                  {saKeys.length}
                </span>
              </div>
            </div>

            {/* Service Account Selector */}
            <div className="bg-white rounded-lg shadow-[0_1px_3px_rgba(0,0,0,0.07)] p-6">
              <label className="block text-sm font-medium text-gray-700 mb-3">
                Select Service Account
              </label>
              <select
                value={selectedSAForKeys}
                onChange={(e) => setSelectedSAForKeys(e.target.value)}
                className="w-full px-4 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
              >
                <option value="">-- Select a service account --</option>
                {serviceAccounts.map((account) => (
                  <option key={account.uniqueId} value={account.email}>
                    {account.email}
                  </option>
                ))}
              </select>

              {selectedSAForKeys && (
                <button
                  onClick={() => handleCreateKey(selectedSAForKeys)}
                  disabled={creatingKey}
                  className="mt-4 px-4 py-2 bg-blue-600 text-white text-sm font-medium rounded-md hover:bg-blue-700 disabled:opacity-50"
                >
                  {creatingKey ? 'Creating...' : 'Create Key'}
                </button>
              )}
            </div>

            {/* Keys Table */}
            {selectedSAForKeys && (
              <div className="bg-white rounded-lg shadow-[0_1px_3px_rgba(0,0,0,0.07)]">
                <div className="px-6 py-4 border-b border-gray-200">
                  <h2 className="text-base font-semibold text-gray-900">Keys for {selectedSAForKeys}</h2>
                </div>

                {keysLoading ? (
                  <div className="p-12 text-center">
                    <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto"></div>
                    <p className="text-gray-600 mt-4 text-sm">Loading keys...</p>
                  </div>
                ) : saKeys.length === 0 ? (
                  <div className="p-12 text-center">
                    <Key className="w-16 h-16 text-gray-300 mx-auto mb-4" />
                    <h3 className="text-base font-medium text-gray-900 mb-2">No keys found</h3>
                    <p className="text-sm text-gray-500 mb-6">
                      Create a key to authenticate as this service account
                    </p>
                  </div>
                ) : (
                  <div className="overflow-x-auto">
                    <table className="min-w-full divide-y divide-gray-200">
                      <thead className="bg-gray-50">
                        <tr>
                          <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                            Key ID
                          </th>
                          <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                            Created
                          </th>
                          <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                            Algorithm
                          </th>
                          <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                            Actions
                          </th>
                        </tr>
                      </thead>
                      <tbody className="bg-white divide-y divide-gray-200">
                        {saKeys.map((key) => (
                          <tr key={key.keyId || key.name} className="hover:bg-gray-50 transition-colors">
                            <td className="px-6 py-4 whitespace-nowrap text-sm font-mono text-gray-900">
                              {(key.keyId || key.name?.split('/').pop() || '').substring(0, 16)}...
                            </td>
                            <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-600">
                              {key.validAfterTime ? new Date(key.validAfterTime).toLocaleString() : 'N/A'}
                            </td>
                            <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-600">
                              {key.keyAlgorithm || 'KEY_ALG_RSA_2048'}
                            </td>
                            <td className="px-6 py-4 whitespace-nowrap text-sm space-x-3">
                              {key.privateKeyData && selectedSAForKeys && (
                                <button
                                  onClick={() => downloadKey(key.privateKeyData!, selectedSAForKeys)}
                                  className="text-blue-600 hover:text-blue-700 font-medium inline-flex items-center gap-1"
                                >
                                  <Download className="w-4 h-4" />
                                  Download
                                </button>
                              )}
                              <button
                                onClick={() => handleDeleteKey(key, selectedSAForKeys)}
                                className="text-red-600 hover:text-red-700 font-medium inline-flex items-center gap-1"
                              >
                                <Trash2 className="w-4 h-4" />
                                Delete
                              </button>
                            </td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                )}
              </div>
            )}
          </div>
        )}
      </div>

      {/* Create Service Account Modal */}
      <Modal
        isOpen={showCreateModal}
        onClose={() => setShowCreateModal(false)}
        title="Create Service Account"
        description="Create a new service account for API access"
        size="md"
      >
        <form onSubmit={handleCreateSA} className="space-y-5">
          <FormField
            label="Account ID"
            required
            help="Lowercase letters, numbers, and hyphens only"
          >
            <Input
              type="text"
              required
              value={formData.accountId}
              onChange={(e) => setFormData({ ...formData, accountId: e.target.value })}
              placeholder="my-service-account"
              pattern="[a-z0-9-]+"
            />
          </FormField>

          <FormField label="Display Name">
            <Input
              type="text"
              value={formData.displayName}
              onChange={(e) => setFormData({ ...formData, displayName: e.target.value })}
              placeholder="My Service Account"
            />
          </FormField>

          <FormField label="Description">
            <Textarea
              value={formData.description}
              onChange={(e) => setFormData({ ...formData, description: e.target.value })}
              rows={3}
              placeholder="Service account description..."
            />
          </FormField>

          <ModalFooter>
            <ModalButton
              variant="secondary"
              onClick={() => setShowCreateModal(false)}
            >
              Cancel
            </ModalButton>
            <ModalButton
              variant="primary"
              type="submit"
              loading={createLoading}
            >
              Create
            </ModalButton>
          </ModalFooter>
        </form>
      </Modal>

      {/* Service Account Details Modal */}
      {selectedAccount && (
        <Modal
          isOpen={showDetailsModal}
          onClose={() => {
            setShowDetailsModal(false);
            setSelectedAccount(null);
          }}
          title="Service Account Details"
          description={selectedAccount.email}
          size="md"
        >
          <div className="space-y-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">Email</label>
              <p className="text-sm text-gray-900 bg-gray-50 p-3 rounded-md font-mono">
                {selectedAccount.email}
              </p>
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">Display Name</label>
              <p className="text-sm text-gray-900">{selectedAccount.displayName || '-'}</p>
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">Unique ID</label>
              <p className="text-sm text-gray-900 bg-gray-50 p-3 rounded-md font-mono">
                {selectedAccount.uniqueId}
              </p>
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">Project</label>
              <p className="text-sm text-gray-900">{selectedAccount.projectId}</p>
            </div>

            {selectedAccount.description && (
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Description</label>
                <p className="text-sm text-gray-600">{selectedAccount.description}</p>
              </div>
            )}

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">Status</label>
              <span
                className={`inline-flex px-2 py-1 text-xs font-medium rounded-full ${
                  selectedAccount.disabled
                    ? 'bg-red-100 text-red-800'
                    : 'bg-green-100 text-green-800'
                }`}
              >
                {selectedAccount.disabled ? 'Disabled' : 'Active'}
              </span>
            </div>
          </div>

          <ModalFooter>
            <ModalButton
              variant="primary"
              onClick={() => handleDeleteSA(selectedAccount.email)}
              loading={deleteLoading}
            >
              Delete Service Account
            </ModalButton>
            <ModalButton
              variant="secondary"
              onClick={() => {
                setShowDetailsModal(false);
                setSelectedAccount(null);
              }}
            >
              Close
            </ModalButton>
          </ModalFooter>
        </Modal>
      )}

      {/* Add IAM Binding Modal */}
      <Modal
        isOpen={showAddBinding}
        onClose={() => {
          setShowAddBinding(false);
          setBindingForm({ principal: '', role: '' });
        }}
        title="Grant Access"
        description="Add a new IAM policy binding"
        size="md"
      >
        <form onSubmit={(e) => { e.preventDefault(); handleAddBinding(); }} className="space-y-5">
          <FormField
            label="Member"
            required
            help="Format: user:email@example.com, serviceAccount:name@project.iam.gserviceaccount.com, group:group@example.com"
          >
            <Input
              type="text"
              required
              value={bindingForm.principal}
              onChange={(e) => setBindingForm({ ...bindingForm, principal: e.target.value })}
              placeholder="user:user@example.com"
            />
          </FormField>

          <FormField
            label="Role"
            required
            help="Format: roles/viewer, roles/editor, roles/owner"
          >
            <Input
              type="text"
              required
              value={bindingForm.role}
              onChange={(e) => setBindingForm({ ...bindingForm, role: e.target.value })}
              placeholder="roles/viewer"
            />
          </FormField>

          <ModalFooter>
            <ModalButton
              variant="secondary"
              onClick={() => {
                setShowAddBinding(false);
                setBindingForm({ principal: '', role: '' });
              }}
            >
              Cancel
            </ModalButton>
            <ModalButton variant="primary" type="submit" loading={addingBinding}>
              Grant Access
            </ModalButton>
          </ModalFooter>
        </form>
      </Modal>

      {/* Create Custom Role Modal */}
      <Modal
        isOpen={showCreateRole}
        onClose={() => {
          setShowCreateRole(false);
          setRoleForm({ roleId: '', title: '', description: '', permissions: '' });
        }}
        title="Create Custom Role"
        description="Define a custom IAM role with specific permissions"
        size="md"
      >
        <form onSubmit={(e) => { e.preventDefault(); handleCreateRole(); }} className="space-y-5">
          <FormField
            label="Role ID"
            required
            help="Lowercase letters, numbers, and underscores only"
          >
            <Input
              type="text"
              required
              value={roleForm.roleId}
              onChange={(e) => setRoleForm({ ...roleForm, roleId: e.target.value })}
              placeholder="custom_role_name"
              pattern="[a-z0-9_]+"
            />
          </FormField>

          <FormField label="Title" required>
            <Input
              type="text"
              required
              value={roleForm.title}
              onChange={(e) => setRoleForm({ ...roleForm, title: e.target.value })}
              placeholder="Custom Role Title"
            />
          </FormField>

          <FormField label="Description">
            <Textarea
              value={roleForm.description}
              onChange={(e) => setRoleForm({ ...roleForm, description: e.target.value })}
              rows={3}
              placeholder="Role description..."
            />
          </FormField>

          <FormField
            label="Permissions"
            help="Each permission on a new line (e.g., compute.instances.list)"
          >
            <Textarea
              value={roleForm.permissions}
              onChange={(e) => setRoleForm({ ...roleForm, permissions: e.target.value })}
              rows={4}
              placeholder="compute.instances.list&#10;storage.buckets.get"
            />
          </FormField>

          <ModalFooter>
            <ModalButton
              variant="secondary"
              onClick={() => {
                setShowCreateRole(false);
                setRoleForm({ roleId: '', title: '', description: '', permissions: '' });
              }}
            >
              Cancel
            </ModalButton>
            <ModalButton variant="primary" type="submit" loading={creatingRole}>
              Create Role
            </ModalButton>
          </ModalFooter>
        </form>
      </Modal>

      {/* Key Downloaded Modal */}
      {newKeyData && (
        <Modal
          isOpen={!!newKeyData}
          onClose={() => setNewKeyData(null)}
          title="Service Account Key Created"
          description="Your private key has been created"
          size="md"
        >
          <div className="space-y-4">
            <div className="bg-green-50 border border-green-200 rounded-md p-4">
              <p className="text-sm text-green-800">
                <strong>Success!</strong> Your service account key has been created.
              </p>
            </div>

            <div className="bg-yellow-50 border border-yellow-200 rounded-md p-4">
              <p className="text-sm text-yellow-800">
                <strong>Warning:</strong> This is the only time you can download this key.
                Keep it secure and do not share it.
              </p>
            </div>

            <button
              onClick={() => {
                downloadKey(newKeyData, selectedSAForKeys);
                setNewKeyData(null);
              }}
              className="w-full px-4 py-2 bg-blue-600 text-white text-sm font-medium rounded-md hover:bg-blue-700 flex items-center justify-center gap-2"
            >
              <Download className="w-4 h-4" />
              Download Key
            </button>
          </div>

          <ModalFooter>
            <ModalButton
              variant="secondary"
              onClick={() => setNewKeyData(null)}
            >
              Close
            </ModalButton>
          </ModalFooter>
        </Modal>
      )}
    </div>
  );
};

export default IAMDashboardPage;
