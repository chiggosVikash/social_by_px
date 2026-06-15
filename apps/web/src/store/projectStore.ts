import { create } from 'zustand';
import { subscribeWithSelector } from 'zustand/middleware';
import { apiClient } from '../lib/api-client';

export interface Project {
  id: number;
  name: string;
  industry: string;
  avoid_image_generation: boolean;
  background_image_url: string | null;
}

export interface ProjectState {
  projects: Project[];
  isLoading: boolean;
  error: string | null;
}

export interface ProjectActions {
  fetchProjects: () => Promise<void>;
  createProject: (data: { name: string; industry: string; keywords: string[]; avoid_image_generation: boolean; style_preset?: string }) => Promise<void>;
  updateProjectSettings: (projectId: number, data: { name?: string; industry?: string; avoid_image_generation?: boolean }) => Promise<void>;
  runWorkflow: (projectId: number) => Promise<void>;
  fetchProjectStatus: (projectId: number) => Promise<string>;
  deleteProject: (projectId: number) => Promise<void>;
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
        await apiClient.post<Project>('/projects', data);
        await get().fetchProjects();
      } catch (err: any) {
        console.error("Failed to create project", err);
        set({ error: 'Failed to create project', isLoading: false });
        throw err;
      }
    },
    updateProjectSettings: async (projectId, data) => {
      set({ isLoading: true, error: null });
      try {
        await apiClient.put<Project>(`/projects/${projectId}`, data);
        await get().fetchProjects();
      } catch (err: any) {
        console.error("Failed to update project settings", err);
        set({ error: 'Failed to update project settings', isLoading: false });
        throw err;
      }
    },
    runWorkflow: async (projectId) => {
      try {
        await apiClient.post(`/projects/${projectId}/workflow`);
      } catch (err: any) {
        console.error("Failed to queue workflow", err);
        throw err;
      }
    },
    fetchProjectStatus: async (projectId) => {
      try {
        const response = await apiClient.get<{status: string}>(`/projects/${projectId}/status`);
        return response.data.status;
      } catch (err) {
        console.error("Failed to fetch status", err);
        return "Unknown";
      }
    },
    deleteProject: async (projectId) => {
      set({ isLoading: true, error: null });
      try {
        await apiClient.delete(`/projects/${projectId}`);
        await get().fetchProjects();
      } catch (err: any) {
        console.error("Failed to delete project", err);
        set({ error: 'Failed to delete project', isLoading: false });
        throw err;
      }
    }
  }))
);
