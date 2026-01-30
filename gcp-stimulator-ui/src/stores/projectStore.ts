import { create } from 'zustand';
import { persist } from 'zustand/middleware';

interface ProjectState {
  selectedProject: string | null;
  setSelectedProject: (projectId: string) => void;
}

export const useProjectStore = create<ProjectState>()(
  persist(
    (set) => ({
      selectedProject: 'test-project',
      setSelectedProject: (projectId) => set({ selectedProject: projectId }),
    }),
    {
      name: 'project-storage',
    }
  )
);
