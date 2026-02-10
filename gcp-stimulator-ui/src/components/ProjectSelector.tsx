import { Fragment, useState } from 'react';
import { Listbox, Transition, Dialog } from '@headlessui/react';
import { Check, ChevronsUpDown, Plus } from 'lucide-react';
import { useProject } from '../contexts/ProjectContext';

export default function ProjectSelector() {
  const { currentProject, setCurrentProject, projects, isLoading, createProject } = useProject();
  const [isCreateModalOpen, setCreateModalOpen] = useState(false);
  const [newProjectId, setNewProjectId] = useState('');
  const [newProjectName, setNewProjectName] = useState('');
  const [createError, setCreateError] = useState('');
  const [isCreating, setIsCreating] = useState(false);

  const currentProjectData = projects.find(p => p.projectId === currentProject);

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
        <Listbox value={currentProject} onChange={setCurrentProject}>
          <div className="relative">
            <Listbox.Button className="relative cursor-pointer rounded-md bg-white pl-3 pr-8 py-2 text-left border border-gray-300 hover:border-gray-400 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent transition-colors text-sm min-w-[180px]">
              <span className="block truncate font-medium text-gray-900">
                {currentProjectData?.name || currentProject}
              </span>
              <span className="pointer-events-none absolute inset-y-0 right-0 flex items-center pr-2">
                <ChevronsUpDown className="h-4 w-4 text-gray-400" aria-hidden="true" />
              </span>
            </Listbox.Button>

            <Transition
              as={Fragment}
              leave="transition ease-in duration-100"
              leaveFrom="opacity-100"
              leaveTo="opacity-0"
            >
              <Listbox.Options className="absolute right-0 z-10 mt-1 max-h-60 w-64 overflow-auto rounded-md bg-white py-1 text-base shadow-lg ring-1 ring-black ring-opacity-5 focus:outline-none sm:text-sm">
                {projects.map((project) => (
                  <Listbox.Option
                    key={project.projectId}
                    className={({ active }) =>
                      `relative cursor-pointer select-none py-2 pl-3 pr-9 ${
                        active ? 'bg-blue-50 text-gray-900' : 'text-gray-900'
                      }`
                    }
                    value={project.projectId}
                  >
                    {({ selected, active }) => (
                      <>
                        <div className="flex flex-col">
                          <span className={`block truncate text-sm ${selected ? 'font-semibold' : 'font-normal'}`}>
                            {project.name}
                          </span>
                          <span className={`text-xs text-gray-500`}>
                            {project.projectId}
                          </span>
                        </div>

                        {selected ? (
                          <span
                            className="absolute inset-y-0 right-0 flex items-center pr-3 text-blue-600"
                          >
                            <Check className="h-4 w-4" aria-hidden="true" />
                          </span>
                        ) : null}
                      </>
                    )}
                  </Listbox.Option>
                ))}
                
                {/* Create New Project Option */}
                <button
                  onClick={() => setCreateModalOpen(true)}
                  className="w-full flex items-center gap-2 px-3 py-2 text-sm text-blue-600 hover:bg-blue-50 border-t border-gray-200 mt-1"
                >
                  <Plus className="h-4 w-4" />
                  <span className="font-medium">Create New Project</span>
                </button>
              </Listbox.Options>
            </Transition>
          </div>
        </Listbox>
      </div>

      {/* Create Project Modal */}
      <Transition appear show={isCreateModalOpen} as={Fragment}>
        <Dialog as="div" className="relative z-50" onClose={() => !isCreating && setCreateModalOpen(false)}>
          <Transition.Child
            as={Fragment}
            enter="ease-out duration-300"
            enterFrom="opacity-0"
            enterTo="opacity-100"
            leave="ease-in duration-200"
            leaveFrom="opacity-100"
            leaveTo="opacity-0"
          >
            <div className="fixed inset-0 bg-black bg-opacity-25" />
          </Transition.Child>

          <div className="fixed inset-0 overflow-y-auto">
            <div className="flex min-h-full items-center justify-center p-4 text-center">
              <Transition.Child
                as={Fragment}
                enter="ease-out duration-300"
                enterFrom="opacity-0 scale-95"
                enterTo="opacity-100 scale-100"
                leave="ease-in duration-200"
                leaveFrom="opacity-100 scale-100"
                leaveTo="opacity-0 scale-95"
              >
                <Dialog.Panel className="w-full max-w-md transform overflow-hidden rounded-2xl bg-white p-6 text-left align-middle shadow-xl transition-all">
                  <Dialog.Title as="h3" className="text-lg font-medium leading-6 text-gray-900 mb-4">
                    Create New Project
                  </Dialog.Title>

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
                        className="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500 sm:text-sm px-3 py-2 border"
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
                        className="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500 sm:text-sm px-3 py-2 border"
                        placeholder="My Project"
                        disabled={isCreating}
                      />
                    </div>

                    <div className="flex justify-end space-x-3 mt-6">
                      <button
                        type="button"
                        onClick={() => setCreateModalOpen(false)}
                        disabled={isCreating}
                        className="rounded-md bg-white px-4 py-2 text-sm font-semibold text-gray-900 shadow-sm ring-1 ring-inset ring-gray-300 hover:bg-gray-50 disabled:opacity-50"
                      >
                        Cancel
                      </button>
                      <button
                        type="submit"
                        disabled={isCreating || !newProjectId}
                        className="rounded-md bg-blue-600 px-4 py-2 text-sm font-semibold text-white shadow-sm hover:bg-blue-500 focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-blue-600 disabled:opacity-50"
                      >
                        {isCreating ? 'Creating...' : 'Create Project'}
                      </button>
                    </div>
                  </form>
                </Dialog.Panel>
              </Transition.Child>
            </div>
          </div>
        </Dialog>
      </Transition>
    </>
  );
}
