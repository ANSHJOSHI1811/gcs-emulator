import { useState } from 'react';
import { Plus } from 'lucide-react';
import { useProject } from '../contexts/ProjectContext';

export default function ProjectSelector() {
  const { currentProject, setCurrentProject, projects, isLoading, createProject } = useProject();
  const [isCreateModalOpen, setCreateModalOpen] = useState(false);
  const [newProjectId, setNewProjectId] = useState('');
  const [newProjectName, setNewProjectName] = useState('');
  const [createError, setCreateError] = useState('');
  const [isCreating, setIsCreating] = useState(false);

  const handleCreateProject = async (e: React.FormEvent) => {
    e.preventDefault();
    setCreateError('');
    setIsCreating(true);

    try {
      await createProject(newProjectId, newProjectName || newProjectId);
      setCreateModalOpen(false);
      setNewProjectId('');
      setNewProjectName('');
    } catch (error: any) {
      setCreateError(error.message || 'Failed to create project');
    } finally {
      setIsCreating(false);
    }
  };

  if (isLoading) {
    return (
      <div className="w-72">
        <div className="h-10 bg-gray-200 rounded animate-pulse"></div>
      </div>
    );
  }

  return (
    <>
      <div className="flex items-center gap-2">
        <select
          value={currentProject}
          onChange={(e) => setCurrentProject(e.target.value)}
          className="h-10 min-w-[220px] rounded-md border border-gray-300 bg-white px-3 text-sm text-gray-900 focus:border-blue-500 focus:outline-none focus:ring-2 focus:ring-blue-500"
        >
          {projects.map((project) => (
            <option key={project.projectId} value={project.projectId}>
              {project.name} ({project.projectId})
            </option>
          ))}
        </select>

        <button
          type="button"
          onClick={() => setCreateModalOpen(true)}
          className="inline-flex h-10 items-center gap-2 rounded-md border border-blue-200 bg-blue-50 px-3 text-sm font-medium text-blue-700 hover:bg-blue-100"
        >
          <Plus className="h-4 w-4" />
          New
        </button>
      </div>

      {isCreateModalOpen && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/25 p-4">
          <div className="w-full max-w-md rounded-xl bg-white p-6 shadow-xl">
            <h3 className="mb-4 text-lg font-medium text-gray-900">Create New Project</h3>

            <form onSubmit={handleCreateProject} className="space-y-4">
              {createError && (
                <div className="rounded-md bg-red-50 p-3">
                  <p className="text-sm text-red-800">{createError}</p>
                </div>
              )}

              <div>
                <label htmlFor="projectId" className="block text-sm font-medium text-gray-700">
                  Project ID *
                </label>
                <input
                  type="text"
                  id="projectId"
                  required
                  value={newProjectId}
                  onChange={(e) => setNewProjectId(e.target.value)}
                  pattern="[a-z]([a-z0-9-]{4,28}[a-z0-9])?"
                  className="mt-1 block w-full rounded-md border border-gray-300 px-3 py-2 text-sm shadow-sm focus:border-blue-500 focus:ring-blue-500"
                  placeholder="my-project-123"
                  disabled={isCreating}
                />
                <p className="mt-1 text-xs text-gray-500">
                  6-30 characters: lowercase letters, numbers, and hyphens
                </p>
              </div>

              <div>
                <label htmlFor="projectName" className="block text-sm font-medium text-gray-700">
                  Project Name (optional)
                </label>
                <input
                  type="text"
                  id="projectName"
                  value={newProjectName}
                  onChange={(e) => setNewProjectName(e.target.value)}
                  className="mt-1 block w-full rounded-md border border-gray-300 px-3 py-2 text-sm shadow-sm focus:border-blue-500 focus:ring-blue-500"
                  placeholder="My Project"
                  disabled={isCreating}
                />
              </div>

              <div className="mt-6 flex justify-end gap-3">
                <button
                  type="button"
                  onClick={() => setCreateModalOpen(false)}
                  disabled={isCreating}
                  className="rounded-md border border-gray-300 bg-white px-4 py-2 text-sm font-semibold text-gray-900 hover:bg-gray-50 disabled:opacity-50"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  disabled={isCreating || !newProjectId}
                  className="rounded-md bg-blue-600 px-4 py-2 text-sm font-semibold text-white hover:bg-blue-500 disabled:opacity-50"
                >
                  {isCreating ? 'Creating...' : 'Create Project'}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </>
  );
}
