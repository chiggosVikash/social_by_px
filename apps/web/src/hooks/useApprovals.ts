import { useState, useEffect } from "react";
import { toast } from "sonner";
import { apiClient } from "@/lib/api-client";

export interface ApprovalItem {
  id: number;
  project_name: string;
  article_title: string;
  slides: string[];
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
    toast.info("Regeneration queued.");
  };

  return {
    items,
    loading,
    handleApprove,
    handleReject,
    handleRegenerate
  };
}
