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
}

export type ProjectStore = ProjectState & ProjectActions;

export const useProjectStore = create<ProjectStore>()(
  subscribeWithSelector((set) => ({
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
  }))
);
