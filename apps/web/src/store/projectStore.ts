import { create } from 'zustand';
import { subscribeWithSelector } from 'zustand/middleware';
import { apiClient } from '../lib/api-client';

export interface Project {
  id: number;
  name: string;
  industry: string;
}

export interface ProjectState {
  projects: Project[];
  isLoading: boolean;
  error: string | null;
}

export interface ProjectActions {
  fetchProjects: () => Promise<void>;
  createProject: (data: { name: string; industry: string; keywords: string[] }) => Promise<void>;
}

export type ProjectStore = ProjectState & ProjectActions;

export const useProjectStore = create<ProjectStore>()(
  subscribeWithSelector((set, get) => ({
    projects: [],
    isLoading: false,
    error: null,
    fetchProjects: async () => {
      set({ isLoading: true, error: null });
      try {
        const response = await apiClient.get<Project[]>('/projects');
        set({ projects: response.data, isLoading: false });
      } catch {
        set({ error: 'Failed to fetch projects', isLoading: false });
      }
    },
    createProject: async (data) => {
      set({ isLoading: true, error: null });
      try {
        const response = await apiClient.post<Project>('/projects', data);
        // Refresh the list immediately
        await get().fetchProjects();
      } catch (err: any) {
        console.error("Failed to create project", err);
        set({ error: 'Failed to create project', isLoading: false });
        throw err;
      }
    },
  }))
);
