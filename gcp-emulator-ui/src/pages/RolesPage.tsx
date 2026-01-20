import { useEffect, useState } from 'react';
import { fetchRoles, createRole, deleteRole, Role } from '../api/iam';
import { Plus, Trash2, Shield, Lock } from 'lucide-react';

export default function RolesPage() {
  const [roles, setRoles] = useState<Role[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [isCreateModalOpen, setIsCreateModalOpen] = useState(false);
  const [showCustomOnly, setShowCustomOnly] = useState(false);
  
  // Form state
  const [roleId, setRoleId] = useState('');
  const [title, setTitle] = useState('');
  const [description, setDescription] = useState('');
  const [permissions, setPermissions] = useState('');

  const loadRoles = async () => {
    try {
      setIsLoading(true);
      // Load both predefined and custom roles
      const [predefinedRoles, customRoles] = await Promise.all([
        fetchRoles(),
        fetchRoles('my-project'),
      ]);
      setRoles([...predefinedRoles, ...customRoles]);
      setError(null);
    } catch (err: any) {
      setError(err.message || 'Failed to load roles');
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    loadRoles();
  }, []);

  const handleCreate = async (e: React.FormEvent) => {
    e.preventDefault();
    try {
      const permissionList = permissions
        .split('\n')
        .map(p => p.trim())
        .filter(p => p.length > 0);
      
      await createRole(roleId, title, description, permissionList);
      setIsCreateModalOpen(false);
      setRoleId('');
      setTitle('');
      setDescription('');
      setPermissions('');
      loadRoles();
    } catch (err: any) {
      alert(err.message || 'Failed to create role');
    }
  };

  const handleDelete = async (roleName: string) => {
    if (!confirm(`Delete role ${roleName}?`)) return;
    
    try {
      await deleteRole(roleName);
      loadRoles();
    } catch (err: any) {
      alert(err.message || 'Failed to delete role');
    }
  };

  const filteredRoles = showCustomOnly 
    ? roles.filter(role => role.name.includes('/projects/'))
    : roles;

  if (isLoading) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600"></div>
      </div>
    );
  }

  return (
    <div className="container mx-auto px-4 py-8">
      <div className="mb-8">
        <div className="flex justify-between items-center">
          <div>
            <h1 className="text-3xl font-bold text-gray-900">IAM Roles</h1>
            <p className="mt-2 text-gray-600">Manage predefined and custom IAM roles</p>
          </div>
          <button
            onClick={() => setIsCreateModalOpen(true)}
            className="flex items-center gap-2 bg-blue-600 text-white px-4 py-2 rounded-lg hover:bg-blue-700 transition"
          >
            <Plus size={20} />
            Create Custom Role
          </button>
        </div>
      </div>

      {error && (
        <div className="mb-4 p-4 bg-red-50 border border-red-200 rounded-lg text-red-700">
          {error}
        </div>
      )}

      <div className="mb-4 flex items-center gap-4">
        <label className="flex items-center gap-2 text-sm text-gray-700">
          <input
            type="checkbox"
            checked={showCustomOnly}
            onChange={(e) => setShowCustomOnly(e.target.checked)}
            className="rounded border-gray-300"
          />
          Show custom roles only
        </label>
        <span className="text-sm text-gray-500">
          ({filteredRoles.length} roles)
        </span>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
        {filteredRoles.map((role) => {
          const isCustom = role.name.includes('/projects/');
          return (
            <div
              key={role.name}
              className={`bg-white rounded-lg shadow-sm border p-4 hover:shadow-md transition ${
                role.deleted ? 'opacity-50' : ''
              }`}
            >
              <div className="flex items-start justify-between mb-3">
                <div className="flex items-center gap-2">
                  {isCustom ? (
                    <Shield className="h-5 w-5 text-blue-600" />
                  ) : (
                    <Lock className="h-5 w-5 text-gray-400" />
                  )}
                  <h3 className="font-semibold text-gray-900">{role.title}</h3>
                </div>
                {isCustom && !role.deleted && (
                  <button
                    onClick={() => handleDelete(role.name)}
                    className="text-red-600 hover:text-red-800"
                    title="Delete"
                  >
                    <Trash2 size={16} />
                  </button>
                )}
              </div>
              
              <p className="text-xs font-mono text-gray-500 mb-2 break-all">
                {role.name}
              </p>
              
              {role.description && (
                <p className="text-sm text-gray-600 mb-3">{role.description}</p>
              )}
              
              <div className="flex items-center gap-2 mb-2">
                <span className={`px-2 py-1 text-xs rounded ${
                  isCustom 
                    ? 'bg-blue-100 text-blue-700' 
                    : 'bg-gray-100 text-gray-700'
                }`}>
                  {isCustom ? 'Custom' : 'Predefined'}
                </span>
                <span className="px-2 py-1 text-xs bg-gray-100 text-gray-700 rounded">
                  {role.stage}
                </span>
                {role.deleted && (
                  <span className="px-2 py-1 text-xs bg-red-100 text-red-700 rounded">
                    Deleted
                  </span>
                )}
              </div>
              
              <div className="mt-3 pt-3 border-t border-gray-200">
                <p className="text-xs text-gray-500 mb-1">Permissions:</p>
                <div className="max-h-24 overflow-y-auto">
                  {role.includedPermissions.length > 0 ? (
                    <ul className="text-xs space-y-1">
                      {role.includedPermissions.slice(0, 5).map((perm, idx) => (
                        <li key={idx} className="text-gray-600 font-mono">
                          • {perm}
                        </li>
                      ))}
                      {role.includedPermissions.length > 5 && (
                        <li className="text-gray-500 italic">
                          + {role.includedPermissions.length - 5} more
                        </li>
                      )}
                    </ul>
                  ) : (
                    <p className="text-xs text-gray-400 italic">No permissions</p>
                  )}
                </div>
              </div>
            </div>
          );
        })}
      </div>

      {/* Create Modal */}
      {isCreateModalOpen && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <div className="bg-white rounded-lg p-6 w-full max-w-lg">
            <h2 className="text-xl font-bold mb-4">Create Custom Role</h2>
            <form onSubmit={handleCreate}>
              <div className="mb-4">
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Role ID *
                </label>
                <input
                  type="text"
                  value={roleId}
                  onChange={(e) => setRoleId(e.target.value)}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
                  placeholder="customRole"
                  required
                />
              </div>
              
              <div className="mb-4">
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Title *
                </label>
                <input
                  type="text"
                  value={title}
                  onChange={(e) => setTitle(e.target.value)}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
                  placeholder="Custom Role"
                  required
                />
              </div>
              
              <div className="mb-4">
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Description
                </label>
                <textarea
                  value={description}
                  onChange={(e) => setDescription(e.target.value)}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
                  rows={2}
                  placeholder="Role description"
                />
              </div>
              
              <div className="mb-6">
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Permissions (one per line)
                </label>
                <textarea
                  value={permissions}
                  onChange={(e) => setPermissions(e.target.value)}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 font-mono text-sm"
                  rows={6}
                  placeholder="storage.objects.get&#10;storage.objects.list&#10;storage.buckets.get"
                />
              </div>

              <div className="flex justify-end gap-3">
                <button
                  type="button"
                  onClick={() => setIsCreateModalOpen(false)}
                  className="px-4 py-2 text-gray-700 bg-gray-100 rounded-lg hover:bg-gray-200"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700"
                >
                  Create
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
}
