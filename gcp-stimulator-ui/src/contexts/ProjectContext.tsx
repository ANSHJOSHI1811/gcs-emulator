import { createContext, useContext, useState, useEffect, ReactNode } from 'react';
import apiClient from '../api/client';

interface Project {
  projectId: string;
  name: string;
  projectNumber: string;
  lifecycleState: string;
  createTime: string;
}

interface ProjectContextType {
  currentProject: string;
  setCurrentProject: (projectId: string) => void;
  projects: Project[];
  isLoading: boolean;
  refreshProjects: () => Promise<void>;
  createProject: (projectId: string, name?: string) => Promise<void>;
}

const ProjectContext = createContext<ProjectContextType | undefined>(undefined);

export function ProjectProvider({ children }: { children: ReactNode }) {
  const [currentProject, setCurrentProjectState] = useState<string>(() => {
    return localStorage.getItem('gcp-stimulator-project') || 'demo-project';
  });
  const [projects, setProjects] = useState<Project[]>([]);
  const [isLoading, setIsLoading] = useState(true);

  const refreshProjects = async () => {
    try {
      setIsLoading(true);
      const response = await apiClient.get('/cloudresourcemanager/v1/projects');
      setProjects(response.data.projects || []);
      
      // If current project doesn't exist, switch to first available or demo-project
      const projectIds = response.data.projects.map((p: Project) => p.projectId);
      if (!projectIds.includes(currentProject)) {
        const fallbackProject = projectIds.length > 0 ? projectIds[0] : 'demo-project';
        setCurrentProject(fallbackProject);
      }
    } catch (error) {
      console.error('Failed to fetch projects:', error);
      setProjects([]);
    } finally {
      setIsLoading(false);
    }
  };

  const setCurrentProject = (projectId: string) => {
    setCurrentProjectState(projectId);
    localStorage.setItem('gcp-stimulator-project', projectId);
  };

  const createProject = async (projectId: string, name?: string) => {
    try {
      await apiClient.post('/cloudresourcemanager/v1/projects', {
        projectId,
        name: name || projectId
      });
      await refreshProjects();
      setCurrentProject(projectId);
    } catch (error: any) {
      if (error.response?.data?.error?.message) {
        throw new Error(error.response.data.error.message);
      }
      throw error;
    }
  };

  useEffect(() => {
    refreshProjects();
  }, []);

  return (
    <ProjectContext.Provider
      value={{
        currentProject,
        setCurrentProject,
        projects,
        isLoading,
        refreshProjects,
        createProject
      }}
    >
      {children}
    </ProjectContext.Provider>
  );
}

export function useProject() {
  const context = useContext(ProjectContext);
  if (context === undefined) {
    throw new Error('useProject must be used within a ProjectProvider');
  }
  return context;
}
