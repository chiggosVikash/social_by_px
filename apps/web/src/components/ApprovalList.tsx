"use client";

import { Card, CardContent, CardFooter, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Check, X, RefreshCw } from "lucide-react";
import { useState } from "react";
import { toast } from "sonner";

export interface ApprovalItem {
  id: number;
  project_name: string;
  article_title: string;
  slides: string[];
}

export function ApprovalList({ initialItems }: { initialItems: ApprovalItem[] }) {
  const [items, setItems] = useState<ApprovalItem[]>(initialItems);

  const handleApprove = async (id: number) => {
    // In a real app, call a Server Action or API route here
    setItems(items.filter(item => item.id !== id));
    toast.success("Carousel approved for publishing!");
  };

  const handleReject = async (id: number) => {
    // Call backend API to reject
    setItems(items.filter(item => item.id !== id));
    toast.error("Carousel rejected.");
  };

  const handleRegenerate = async (id: number) => {
    // Call backend API to regenerate
    toast.info("Regeneration queued.");
  };

  if (items.length === 0) {
    return (
      <div className="p-8 text-center border rounded-lg border-dashed">
        <h3 className="text-lg font-medium mb-2">All caught up!</h3>
        <p className="text-sm text-muted-foreground">There are no pending carousels to review.</p>
      </div>
    );
  }

  return (
    <div className="grid gap-6">
      {items.map((item) => (
        <Card key={item.id} className="overflow-hidden">
          <CardHeader className="bg-muted/50">
            <CardTitle>{item.article_title}</CardTitle>
            <div className="text-sm text-muted-foreground">Project: {item.project_name}</div>
          </CardHeader>
          <CardContent className="p-6">
            <div className="flex gap-4 overflow-x-auto pb-4">
              {item.slides.map((slide, idx) => (
                <div key={idx} className="flex-shrink-0 w-64 h-64 bg-muted rounded-md flex items-center justify-center p-4 text-center border border-dashed">
                  {slide}
                </div>
              ))}
            </div>
          </CardContent>
          <CardFooter className="flex justify-end gap-2 bg-muted/20">
            <Button variant="outline" onClick={() => handleRegenerate(item.id)}>
              <RefreshCw className="mr-2 h-4 w-4" /> Regenerate
            </Button>
            <Button variant="destructive" onClick={() => handleReject(item.id)}>
              <X className="mr-2 h-4 w-4" /> Reject
            </Button>
            <Button className="bg-emerald-600 hover:bg-emerald-700 text-white shadow-sm transition-all duration-200 hover:shadow-md hover:-translate-y-0.5" onClick={() => handleApprove(item.id)}>
              <Check className="mr-2 h-4 w-4" /> Approve & Publish
            </Button>
          </CardFooter>
        </Card>
      ))}
    </div>
  );
}
