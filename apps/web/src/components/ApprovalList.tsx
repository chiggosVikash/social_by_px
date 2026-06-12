"use client";

import { Card, CardContent, CardFooter, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Check, X, RefreshCw, Loader2 } from "lucide-react";
import { useApprovals } from "@/hooks/useApprovals";

export function ApprovalList() {
  const { items, loading, handleApprove, handleReject, handleRegenerate } = useApprovals();

  if (loading) {
    return (
      <div className="flex items-center justify-center p-12">
        <Loader2 className="w-8 h-8 animate-spin text-muted-foreground" />
      </div>
    );
  }

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
