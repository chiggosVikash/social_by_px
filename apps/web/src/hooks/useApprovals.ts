import { useState, useEffect } from "react";
import { toast } from "sonner";
import { apiClient } from "@/lib/api-client";

export interface SlideOut {
  id: number;
  text_content: string;
  image_url: string | null;
  caption: string | null;
  emoji: string | null;
}

export interface ApprovalItem {
  id: number;
  project_id: number;
  project_name: string;
  article_title: string;
  slides: SlideOut[];
  avoid_image_generation?: boolean;
  background_image_url?: string | null;
}

export function useApprovals() {
  const [items, setItems] = useState<ApprovalItem[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const fetchApprovals = async () => {
      try {
        const response = await apiClient.get<ApprovalItem[]>("/approvals/pending");
        setItems(response.data);
      } catch (error) {
        console.error("Failed to fetch approvals:", error);
        toast.error("Failed to load pending approvals.");
      } finally {
        setLoading(false);
      }
    };
    fetchApprovals();
  }, []);

  const handleApprove = async (id: number) => {
    try {
      await apiClient.post(`/approvals/${id}/approve`);
      setItems(items.filter(item => item.id !== id));
      toast.success("Carousel approved for publishing!");
    } catch (error) {
      console.error("Approval failed:", error);
      toast.error("Failed to approve carousel.");
    }
  };

  const handleReject = async (id: number) => {
    try {
      await apiClient.post(`/approvals/${id}/reject`);
      setItems(items.filter(item => item.id !== id));
      toast.error("Carousel rejected.");
    } catch (error) {
      console.error("Rejection failed:", error);
      toast.error("Failed to reject carousel.");
    }
  };

  const handleRegenerate = async (id: number) => {
    try {
      await apiClient.post(`/approvals/${id}/regenerate`);
      toast.success("Carousel regeneration started!");
    } catch (error) {
      console.error("Regeneration failed:", error);
      toast.error("Failed to start regeneration.");
      throw error;
    }
  };

  const handleUpdateSlides = async (articleId: number, slides: {id: number, text_content: string}[]) => {
    try {
      await apiClient.put(`/approvals/${articleId}/slides`, { slides });
      toast.success("Slides updated successfully!");
    } catch (error) {
      console.error("Failed to update slides:", error);
      toast.error("Failed to save slide edits.");
      throw error;
    }
  };

  const handleGenerateImages = async (articleId: number) => {
    try {
      await apiClient.post(`/approvals/${articleId}/generate-images`);
      toast.success("Image generation started!");
    } catch (error) {
      console.error("Failed to start image generation:", error);
      toast.error("Failed to start image generation.");
      throw error;
    }
  };

  return {
    items,
    loading,
    handleApprove,
    handleReject,
    handleRegenerate,
    handleUpdateSlides,
    handleGenerateImages
  };
}
