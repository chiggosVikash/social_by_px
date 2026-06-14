"use client";

import { useState, useEffect, useRef } from "react";
import { Card, CardContent, CardFooter, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Check, X, RefreshCw, Loader2, XCircle, Edit, Save, ImageIcon, Upload } from "lucide-react";
import { useApprovals, ApprovalItem } from "@/hooks/useApprovals";
import { Progress } from "@/components/ui/progress";
import { toast } from "sonner";
import { apiClient } from "@/lib/api-client";

function ApprovalCard({ 
  item, 
  handleApprove, 
  handleReject, 
  handleRegenerate,
  handleUpdateSlides,
  handleGenerateImages
}: { 
  item: ApprovalItem; 
  handleApprove: (id: number) => void; 
  handleReject: (id: number) => void; 
  handleRegenerate: (id: number) => void; 
  handleUpdateSlides: (id: number, slides: {id: number, text_content: string}[]) => Promise<void>;
  handleGenerateImages: (id: number) => Promise<void>;
}) {
  const [status, setStatus] = useState<string>("pending");
  const [progressValue, setProgressValue] = useState<number>(0);
  const [isFailed, setIsFailed] = useState<boolean>(false);

  const [shouldConnect, setShouldConnect] = useState(false);
  const [isEditing, setIsEditing] = useState(false);
  const [editedSlides, setEditedSlides] = useState<{id: number, text_content: string}[]>([]);
  const [isSaving, setIsSaving] = useState(false);
  const [isCardUploading, setIsCardUploading] = useState(false);
  const cardFileInputRef = useRef<HTMLInputElement>(null);

  const handleCardFileChange = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;

    if (file.size > 5 * 1024 * 1024) {
      toast.error("File is too large. Max size is 5MB.");
      return;
    }

    const allowedTypes = ["image/jpeg", "image/png", "image/webp"];
    if (!allowedTypes.includes(file.type)) {
      toast.error("Invalid file type. Allowed: JPEG, PNG, WebP.");
      return;
    }

    setIsCardUploading(true);
    const formData = new FormData();
    formData.append("file", file);

    try {
      const response = await apiClient.post(`/projects/${item.project_id}/background`, formData, {
        headers: {
          "Content-Type": "multipart/form-data",
        },
      });
      
      item.background_image_url = response.data.background_image_url;
      toast.success("Background uploaded! Rendering slides...");
      
      setStatus("Compositing text onto template...");
      setProgressValue(15);
      setIsFailed(false);
      setShouldConnect(true);
    } catch (err) {
      console.error("Failed to upload background template:", err);
      toast.error("Failed to upload background template.");
    } finally {
      setIsCardUploading(false);
    }
  };

  const handleEditToggle = () => {
    if (!isEditing) {
      setEditedSlides(item.slides.map(s => ({ id: s.id, text_content: s.text_content })));
    }
    setIsEditing(!isEditing);
  };

  const handleSave = async () => {
    setIsSaving(true);
    try {
      await handleUpdateSlides(item.id, editedSlides);
      // Update local item slides for immediate reflection
      item.slides = item.slides.map(s => {
        const edited = editedSlides.find(es => es.id === s.id);
        return edited ? { ...s, text_content: edited.text_content } : s;
      });
      setIsEditing(false);
    } finally {
      setIsSaving(false);
    }
  };

  useEffect(() => {
    if (!shouldConnect) return;

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
            const failed = data.is_failed || data.status === "Failed" || data.status.toLowerCase().includes("fail");
            setIsFailed(failed);
            
            if (data.status === "Completed" || failed) {
              setShouldConnect(false); // [SOLID: SRP] Auto-cleanup WebSocket when done
              
              if (!failed) {
                // Wait a bit to show 100%, then reload the page to fetch the newly generated slides
                setTimeout(() => {
                  window.location.reload();
                }, 1000);
              }
            }
          }
        } catch (e) {
          console.error("Failed to parse websocket message", e);
        }
      };

      ws.onclose = () => {
        if (isMounted && shouldConnect) {
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
  }, [item.project_id, status, shouldConnect]);

  const onRegenerate = async () => {
    setStatus("Regenerating article...");
    setProgressValue(5);
    setIsFailed(false);
    setShouldConnect(true);
    await handleRegenerate(item.id);
  };

  const onGenerateImages = async () => {
    setStatus("Generating images...");
    setProgressValue(5);
    setIsFailed(false);
    setShouldConnect(true);
    await handleGenerateImages(item.id);
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
        {item.avoid_image_generation && !item.background_image_url ? (
          <div className="flex flex-col items-center justify-center p-8 border border-dashed rounded-lg bg-amber-500/5 border-amber-500/20 text-center space-y-4 my-2">
            <div className="w-12 h-12 rounded-full bg-amber-500/10 flex items-center justify-center text-amber-600">
              <Upload className="h-5 w-5" />
            </div>
            <div className="space-y-1">
              <h4 className="text-sm font-semibold font-heading text-amber-800 dark:text-amber-300">Background Template Required</h4>
              <p className="text-xs text-muted-foreground max-w-sm">
                This project avoids AI image generation. Please upload a background image template to render the slide content.
              </p>
            </div>
            <Button onClick={() => cardFileInputRef.current?.click()} disabled={isCardUploading} size="sm" className="rounded-lg shadow-sm">
              {isCardUploading ? <Loader2 className="mr-2 h-3.5 w-3.5 animate-spin" /> : <Upload className="mr-2 h-3.5 w-3.5" />}
              Upload Background Template
            </Button>
            <input 
              type="file" 
              ref={cardFileInputRef} 
              onChange={handleCardFileChange} 
              className="hidden" 
              accept="image/png, image/jpeg, image/webp"
            />
          </div>
        ) : (
          <div className={`flex gap-4 overflow-x-auto pb-4 transition-opacity duration-300 ${isWorking ? 'opacity-30' : 'opacity-100'}`}>
            {item.slides.map((slide, idx) => {
              const editSlide = editedSlides.find(s => s.id === slide.id);
              return (
                <div 
                  key={slide.id} 
                  className="flex-shrink-0 w-64 h-64 bg-muted rounded-md flex flex-col items-center justify-center p-4 text-center border border-dashed relative overflow-hidden"
                  style={slide.image_url ? { backgroundImage: `url(${slide.image_url})`, backgroundSize: 'cover', backgroundPosition: 'center', color: 'white', textShadow: '0 1px 3px rgba(0,0,0,0.8)' } : {}}
                >
                  <span className={`absolute top-2 left-2 text-xs font-mono px-2 rounded-full z-10 ${slide.image_url ? 'bg-black/60 text-white' : 'bg-background/80 text-muted-foreground'}`}>
                    Slide {idx + 1}
                  </span>
                  
                  {slide.image_url && <div className="absolute inset-0 bg-black/40 z-0"></div>}

                  <div className="z-10 w-full h-full flex items-center justify-center pt-6">
                    {isEditing ? (
                      <textarea 
                        className="w-full h-full bg-background/90 text-foreground text-sm p-2 rounded border focus:outline-none focus:ring-2 focus:ring-primary resize-none"
                        value={editSlide?.text_content || ""}
                        onChange={(e) => {
                          setEditedSlides(prev => prev.map(s => s.id === slide.id ? { ...s, text_content: e.target.value } : s));
                        }}
                      />
                    ) : (
                      <p className="line-clamp-6">{isEditing && editSlide ? editSlide.text_content : slide.text_content}</p>
                    )}
                  </div>
                </div>
              );
            })}
          </div>
        )}
        
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
        {isEditing ? (
          <>
            <Button variant="ghost" onClick={handleEditToggle} disabled={isSaving}>Cancel</Button>
            <Button onClick={handleSave} disabled={isSaving}>
              {isSaving ? <Loader2 className="mr-2 h-4 w-4 animate-spin" /> : <Save className="mr-2 h-4 w-4" />}
              Save Changes
            </Button>
          </>
        ) : (
          <>
            <Button variant="outline" onClick={handleEditToggle} disabled={isWorking}>
              <Edit className="mr-2 h-4 w-4" /> Edit
            </Button>
            <Button 
              variant="outline" 
              onClick={onGenerateImages} 
              disabled={isWorking || (item.avoid_image_generation && !item.background_image_url)}
            >
              {isWorking ? <Loader2 className="mr-2 h-4 w-4 animate-spin" /> : <ImageIcon className="mr-2 h-4 w-4" />}
              {item.avoid_image_generation ? "Render Slides" : "Generate Images"}
            </Button>
            <Button variant="outline" onClick={onRegenerate} disabled={isWorking}>
              {isWorking ? <Loader2 className="mr-2 h-4 w-4 animate-spin" /> : <RefreshCw className="mr-2 h-4 w-4" />}
              Regenerate Text
            </Button>
            <Button variant="destructive" onClick={() => handleReject(item.id)} disabled={isWorking}>
              <X className="mr-2 h-4 w-4" /> Reject
            </Button>
            <Button 
              className="bg-emerald-600 hover:bg-emerald-700 text-white shadow-sm transition-all duration-200 hover:shadow-md hover:-translate-y-0.5" 
              onClick={() => handleApprove(item.id)} 
              disabled={isWorking || (item.avoid_image_generation && !item.background_image_url)}
            >
              <Check className="mr-2 h-4 w-4" /> Approve
            </Button>
          </>
        )}
      </CardFooter>
    </Card>
  );
}

export function ApprovalList() {
  const { items, loading, handleApprove, handleReject, handleRegenerate, handleUpdateSlides, handleGenerateImages } = useApprovals();

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
          handleUpdateSlides={handleUpdateSlides}
          handleGenerateImages={handleGenerateImages}
        />
      ))}
    </div>
  );
}
