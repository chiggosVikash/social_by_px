"use client";

import { useState, useEffect } from "react";
import { Card, CardContent, CardFooter, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Check, X, RefreshCw, Loader2, XCircle } from "lucide-react";
import { useApprovals, ApprovalItem } from "@/hooks/useApprovals";
import { Progress } from "@/components/ui/progress";

function ApprovalCard({ 
  item, 
  handleApprove, 
  handleReject, 
  handleRegenerate 
}: { 
  item: ApprovalItem; 
  handleApprove: (id: number) => void; 
  handleReject: (id: number) => void; 
  handleRegenerate: (id: number) => void; 
}) {
  const [status, setStatus] = useState<string>("pending");
  const [progressValue, setProgressValue] = useState<number>(0);
  const [isFailed, setIsFailed] = useState<boolean>(false);

  useEffect(() => {
    let ws: WebSocket | null = null;
    let reconnectTimeout: NodeJS.Timeout;
    let isMounted = true;

    const connect = () => {
      // Connect to the project websocket to get progress updates
      const baseUrl = (process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000').replace(/\/api\/v1\/?$/, '');
      const wsUrl = `${baseUrl}/api/v1/ws/projects/${item.project_id}/progress`.replace(/^http/, "ws");
      ws = new WebSocket(wsUrl);

      ws.onmessage = (event) => {
        try {
          const data = JSON.parse(event.data);
          // Only process updates if we clicked regenerate on this card
          if (status !== "pending") {
            setStatus(data.status);
            setProgressValue(data.progress);
            setIsFailed(data.is_failed);
            if (data.status === "Completed") {
              // Wait a bit to show 100%, then reload the page to fetch the newly generated slides
              setTimeout(() => {
                window.location.reload();
              }, 1000);
            }
          }
        } catch (e) {
          console.error("Failed to parse websocket message", e);
        }
      };

      ws.onclose = () => {
        if (isMounted) {
          reconnectTimeout = setTimeout(connect, 3000);
        }
      };

      ws.onerror = (err) => {
        ws?.close();
      };
    };

    connect();

    return () => {
      isMounted = false;
      clearTimeout(reconnectTimeout);
      ws?.close();
    };
  }, [item.project_id, status]);

  const onRegenerate = async () => {
    setStatus("Regenerating article...");
    setProgressValue(5);
    setIsFailed(false);
    await handleRegenerate(item.id);
  };

  const isWorking = status !== "pending" && status !== "Completed" && !isFailed;

  return (
    <Card className="overflow-hidden relative">
      {/* Visual cue that it's regenerating */}
      {isWorking && (
        <div className="absolute top-0 left-0 w-full h-1 bg-gradient-to-r from-amber-400 to-orange-500 animate-pulse" />
      )}
      
      <CardHeader className="bg-muted/50">
        <CardTitle>{item.article_title}</CardTitle>
        <div className="text-sm text-muted-foreground">Project: {item.project_name}</div>
      </CardHeader>
      <CardContent className="p-6">
        <div className={`flex gap-4 overflow-x-auto pb-4 transition-opacity duration-300 ${isWorking ? 'opacity-30' : 'opacity-100'}`}>
          {item.slides.map((slide, idx) => (
            <div key={idx} className="flex-shrink-0 w-64 h-64 bg-muted rounded-md flex flex-col items-center justify-center p-4 text-center border border-dashed relative">
              <span className="absolute top-2 left-2 text-xs text-muted-foreground font-mono bg-background/80 px-2 rounded-full">
                Slide {idx + 1}
              </span>
              <p className="line-clamp-6">{slide}</p>
            </div>
          ))}
        </div>
        
        {status !== "pending" && (
          <div className="space-y-2 mt-4 pt-4 border-t animate-in fade-in slide-in-from-bottom-2">
             <div className="flex justify-between text-xs text-muted-foreground">
               <span className="flex items-center font-medium text-foreground">
                 {isFailed && <XCircle className="w-3 h-3 mr-1 text-destructive" />}
                 {isWorking && <Loader2 className="w-3 h-3 mr-1 animate-spin text-primary" />}
                 {status}
               </span>
               <span className={isFailed ? "text-destructive font-medium" : "font-medium"}>{progressValue}%</span>
             </div>
             <Progress value={progressValue} className="h-2" indicatorClassName={isFailed ? "bg-destructive" : "bg-primary"} />
          </div>
        )}
      </CardContent>
      <CardFooter className="flex justify-end gap-2 bg-muted/20">
        <Button variant="outline" onClick={onRegenerate} disabled={isWorking}>
          {isWorking ? <Loader2 className="mr-2 h-4 w-4 animate-spin" /> : <RefreshCw className="mr-2 h-4 w-4" />}
          Regenerate
        </Button>
        <Button variant="destructive" onClick={() => handleReject(item.id)} disabled={isWorking}>
          <X className="mr-2 h-4 w-4" /> Reject
        </Button>
        <Button className="bg-emerald-600 hover:bg-emerald-700 text-white shadow-sm transition-all duration-200 hover:shadow-md hover:-translate-y-0.5" onClick={() => handleApprove(item.id)} disabled={isWorking}>
          <Check className="mr-2 h-4 w-4" /> Approve & Publish
        </Button>
      </CardFooter>
    </Card>
  );
}

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
      <div className="p-8 text-center border rounded-lg border-dashed bg-muted/10">
        <h3 className="text-lg font-medium mb-2">All caught up!</h3>
        <p className="text-sm text-muted-foreground">There are no pending carousels to review.</p>
      </div>
    );
  }

  return (
    <div className="grid gap-6">
      {items.map((item) => (
        <ApprovalCard 
          key={item.id} 
          item={item} 
          handleApprove={handleApprove} 
          handleReject={handleReject} 
          handleRegenerate={handleRegenerate} 
        />
      ))}
    </div>
  );
}
