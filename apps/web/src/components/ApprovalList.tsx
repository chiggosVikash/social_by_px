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

  // Preview state hooks
  const [showPreview, setShowPreview] = useState(false);
  const [previewPlatform, setPreviewPlatform] = useState<"linkedin" | "instagram">("linkedin");
  const [currentMockupSlideIndex, setCurrentMockupSlideIndex] = useState(0);

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
          <div className={showPreview ? "grid grid-cols-1 lg:grid-cols-12 gap-6" : ""}>
            {/* Left Column: Slide List / Edit Mode */}
            <div className={showPreview ? "lg:col-span-6 space-y-4" : ""}>
              <div className={`flex gap-4 overflow-x-auto pb-4 transition-opacity duration-300 ${isWorking ? 'opacity-30' : 'opacity-100'}`}>
                {item.slides.map((slide, idx) => {
                  const editSlide = editedSlides.find(s => s.id === slide.id);
                  // [SOLID: SRP] - Determine if overlay text should be displayed based on template compositing and editing state
                  const showListText = !slide.image_url || !item.avoid_image_generation || isEditing;
                  const showListDarkOverlay = slide.image_url && (!item.avoid_image_generation || (isEditing && editSlide && editSlide.text_content !== slide.text_content));
                  
                  return (
                    <div 
                      key={slide.id} 
                      className="flex-shrink-0 w-64 h-64 bg-muted rounded-md flex flex-col items-center justify-center p-4 text-center border border-dashed relative overflow-hidden"
                      style={slide.image_url ? { backgroundImage: `url(${slide.image_url})`, backgroundSize: 'cover', backgroundPosition: 'center', color: 'white', textShadow: '0 1px 3px rgba(0,0,0,0.8)' } : {}}
                    >
                      <span className={`absolute top-2 left-2 text-xs font-mono px-2 rounded-full z-10 ${slide.image_url ? 'bg-black/60 text-white' : 'bg-background/80 text-muted-foreground'}`}>
                        Slide {idx + 1}
                      </span>
                      
                      {showListDarkOverlay && <div className="absolute inset-0 bg-black/40 z-0"></div>}

                      {showListText && (
                        <div className="z-10 w-full h-full flex items-center justify-center pt-6">
                          {isEditing ? (
                            <textarea 
                              className="w-full h-full bg-background/90 text-foreground text-sm p-2 rounded border focus:outline-none focus:ring-2 focus:ring-primary resize-none font-sans"
                              value={editSlide?.text_content || ""}
                              onChange={(e) => {
                                setEditedSlides(prev => prev.map(s => s.id === slide.id ? { ...s, text_content: e.target.value } : s));
                              }}
                            />
                          ) : (
                            <p className="line-clamp-6">{slide.text_content}</p>
                          )}
                        </div>
                      )}
                    </div>
                  );
                })}
              </div>
            </div>

            {/* Right Column: Social Preview Mockup */}
            {showPreview && (
              <div className="lg:col-span-6 border border-border rounded-xl p-4 bg-muted/20 flex flex-col space-y-4">
                {/* Platform Toggle Tabs */}
                <div className="flex bg-muted rounded-lg p-1 w-fit">
                  <button 
                    onClick={() => setPreviewPlatform("linkedin")}
                    className={`px-3 py-1.5 text-xs font-medium rounded-md transition-all duration-200 ${previewPlatform === "linkedin" ? 'bg-background text-foreground shadow-sm' : 'text-muted-foreground hover:text-foreground'}`}
                  >
                    LinkedIn
                  </button>
                  <button 
                    onClick={() => setPreviewPlatform("instagram")}
                    className={`px-3 py-1.5 text-xs font-medium rounded-md transition-all duration-200 ${previewPlatform === "instagram" ? 'bg-background text-foreground shadow-sm' : 'text-muted-foreground hover:text-foreground'}`}
                  >
                    Instagram
                  </button>
                </div>

                {/* [SOLID: SRP] - Visual feedback warning for unsaved/unrendered text edits */}
                {isEditing && editedSlides.some((es, idx) => es.text_content !== item.slides[idx].text_content) && (
                  <div className="text-xs text-amber-500 bg-amber-500/10 border border-amber-500/20 px-3 py-2 rounded-lg font-medium">
                    Draft Edits - Click &quot;Save Changes&quot; and then &quot;{item.avoid_image_generation ? "Render Slides" : "Generate Images"}&quot; to update the image.
                  </div>
                )}

                {/* LinkedIn Desktop Document Feed Card Mockup */}
                {previewPlatform === "linkedin" && (
                  <div className="bg-[#1b1f23] text-foreground rounded-lg border border-border/80 shadow-md p-4 max-w-md mx-auto w-full text-left font-sans animate-in fade-in zoom-in-95 duration-200">
                    {/* Header profile info */}
                    <div className="flex items-center space-x-2.5 mb-3">
                      <div className="w-10 h-10 rounded-full bg-primary/20 flex items-center justify-center font-heading text-sm font-bold text-primary">
                        {item.project_name.slice(0, 2).toUpperCase()}
                      </div>
                      <div>
                        <div className="font-semibold text-[13px] hover:underline cursor-pointer">{item.project_name}</div>
                        <div className="text-[11px] text-muted-foreground leading-tight">Content Studio Platform</div>
                        <div className="text-[11px] text-muted-foreground flex items-center gap-1">
                          <span>1h •</span>
                          <svg className="w-3.5 h-3.5 fill-muted-foreground" viewBox="0 0 16 16"><path d="M8 1a7 7 0 100 14A7 7 0 008 1zm0 13a6 6 0 110-12 6 6 0 010 12zm0-9.5A.5.5 0 007.5 5v3.5a.5.5 0 00.146.354l2.5 2.5a.5.5 0 00.708-.708L8.5 8.293V5a.5.5 0 00-.5-.5z"/></svg>
                        </div>
                      </div>
                    </div>
                    
                    {/* Post Caption Body */}
                    <div className="text-[13px] leading-relaxed mb-3 break-words">
                      {item.article_title}
                      <span className="text-primary hover:underline block mt-1">#automation #contentcreation</span>
                    </div>

                    {/* PDF Viewer Simulation */}
                    <div className="border border-border/60 rounded overflow-hidden bg-[#24292e]">
                      {/* Document Banner */}
                      <div className="bg-[#2f363d] px-3 py-1.5 flex justify-between items-center text-[11px] border-b border-border/60">
                        <span className="font-medium truncate max-w-[200px]">{item.article_title.toLowerCase().replace(/\s+/g, "_")}.pdf</span>
                        <span className="text-muted-foreground text-[10px]">{item.slides.length} pages</span>
                      </div>
                      
                      {/* Active Slide Viewer Aspect-4/3 */}
                      <div className="relative aspect-[4/3] bg-muted/20 flex items-center justify-center overflow-hidden">
                        {/* Slide Flip Navigation */}
                        <button 
                          onClick={() => setCurrentMockupSlideIndex(p => Math.max(0, p - 1))}
                          disabled={currentMockupSlideIndex === 0}
                          className="absolute left-2 top-1/2 -translate-y-1/2 w-8 h-8 rounded-full bg-black/50 hover:bg-black/70 flex items-center justify-center text-white disabled:opacity-30 z-10 transition-colors"
                        >
                          &lt;
                        </button>
                        <button 
                          onClick={() => setCurrentMockupSlideIndex(p => Math.min(item.slides.length - 1, p + 1))}
                          disabled={currentMockupSlideIndex === item.slides.length - 1}
                          className="absolute right-2 top-1/2 -translate-y-1/2 w-8 h-8 rounded-full bg-black/50 hover:bg-black/70 flex items-center justify-center text-white disabled:opacity-30 z-10 transition-colors"
                        >
                          &gt;
                        </button>

                        {/* Rendering logic bound to live editing or static slide content */}
                        {(() => {
                          const slide = item.slides[currentMockupSlideIndex];
                          const editSlide = editedSlides[currentMockupSlideIndex];
                          const textToShow = isEditing && editSlide 
                            ? editSlide.text_content 
                            : slide.text_content;
                          
                          const hasEdits = isEditing && editSlide && editSlide.text_content !== slide.text_content;
                          // [SOLID: SRP] - Do not overlay text HTML elements if it is already baked into the image
                          const shouldShowOverlay = !item.avoid_image_generation || hasEdits;

                          if (slide.image_url) {
                            if (!shouldShowOverlay) {
                              return (
                                <div 
                                  className="w-full h-full bg-cover bg-center"
                                  style={{ backgroundImage: `url(${slide.image_url})` }}
                                />
                              );
                            }
                            return (
                              <div 
                                className="w-full h-full flex flex-col items-center justify-center p-6 text-center bg-cover bg-center relative"
                                style={{ backgroundImage: `url(${slide.image_url})` }}
                              >
                                <div className="absolute inset-0 bg-black/40 z-0"></div>
                                <div className="z-10 text-white drop-shadow-md flex flex-col items-center space-y-2">
                                  {slide.emoji && <span className="text-2xl">{slide.emoji}</span>}
                                  <p className="text-xs md:text-sm font-semibold leading-snug max-w-xs">{textToShow}</p>
                                  {slide.caption && <p className="text-[10px] opacity-80 italic">{slide.caption}</p>}
                                </div>
                              </div>
                            );
                          } else if (item.background_image_url) {
                            return (
                              <div 
                                className="w-full h-full flex flex-col items-center justify-center p-6 text-center bg-cover bg-center relative"
                                style={{ backgroundImage: `url(${item.background_image_url})` }}
                              >
                                <div className="absolute inset-0 bg-black/30 z-0"></div>
                                <div className="z-10 text-white drop-shadow-md flex flex-col items-center space-y-2">
                                  {slide.emoji && <span className="text-2xl">{slide.emoji}</span>}
                                  <p className="text-xs md:text-sm font-semibold leading-snug max-w-xs">{textToShow}</p>
                                  {slide.caption && <p className="text-[10px] opacity-80 italic">{slide.caption}</p>}
                                </div>
                              </div>
                            );
                          } else {
                            return (
                              <div className="w-full h-full flex flex-col items-center justify-center p-6 text-center bg-gradient-to-br from-indigo-950 to-slate-900 text-white space-y-2">
                                {slide.emoji && <span className="text-2xl">{slide.emoji}</span>}
                                <p className="text-[11px] md:text-xs font-medium leading-relaxed max-w-xs">{textToShow}</p>
                                {slide.caption && <p className="text-[9px] opacity-80 italic">{slide.caption}</p>}
                              </div>
                            );
                          }
                        })()}

                        {/* Page Indicators */}
                        <span className="absolute bottom-2.5 right-2.5 text-[10px] bg-black/60 text-white px-2 py-0.5 rounded font-mono">
                          {currentMockupSlideIndex + 1} / {item.slides.length}
                        </span>
                      </div>
                    </div>
                    
                    {/* Social Feed Actions Footer */}
                    <div className="mt-3 border-t border-border/60 pt-2 flex items-center justify-between text-muted-foreground text-[11px] px-1">
                      <span className="flex items-center gap-1 cursor-pointer hover:text-primary">
                        Like
                      </span>
                      <span className="flex items-center gap-1 cursor-pointer hover:text-primary">
                        Comment
                      </span>
                      <span className="flex items-center gap-1 cursor-pointer hover:text-primary">
                        Repost
                      </span>
                      <span className="flex items-center gap-1 cursor-pointer hover:text-primary">
                        Send
                      </span>
                    </div>
                  </div>
                )}

                {/* Instagram Mobile Feed Card Mockup */}
                {previewPlatform === "instagram" && (
                  <div className="bg-[#0b0c10] text-white rounded-lg border border-border/80 shadow-md p-0 max-w-md mx-auto w-full text-left font-sans overflow-hidden animate-in fade-in zoom-in-95 duration-200">
                    {/* circular avatar user header */}
                    <div className="flex items-center justify-between p-3 border-b border-border/10">
                      <div className="flex items-center space-x-2">
                        <div className="w-8 h-8 rounded-full bg-gradient-to-tr from-yellow-500 via-red-500 to-purple-600 p-[1.5px]">
                          <div className="w-full h-full rounded-full bg-black flex items-center justify-center font-heading text-[10px] font-bold text-white">
                            {item.project_name.slice(0, 2).toUpperCase()}
                          </div>
                        </div>
                        <div>
                          <div className="font-semibold text-[12px] hover:underline cursor-pointer">{item.project_name.toLowerCase().replace(/\s+/g, "_")}</div>
                          <div className="text-[9px] text-muted-foreground leading-tight">Sponsored</div>
                        </div>
                      </div>
                      <button className="text-white font-bold text-[13px] opacity-70">•••</button>
                    </div>

                    {/* square viewport area */}
                    <div className="relative aspect-square bg-muted/20 flex items-center justify-center overflow-hidden">
                      {/* Swipe overlay controls */}
                      <button 
                        onClick={() => setCurrentMockupSlideIndex(p => Math.max(0, p - 1))}
                        disabled={currentMockupSlideIndex === 0}
                        className="absolute left-2 top-1/2 -translate-y-1/2 w-8 h-8 rounded-full bg-black/40 hover:bg-black/60 flex items-center justify-center text-white disabled:opacity-0 transition-opacity duration-200 z-10"
                      >
                        &lt;
                      </button>
                      <button 
                        onClick={() => setCurrentMockupSlideIndex(p => Math.min(item.slides.length - 1, p + 1))}
                        disabled={currentMockupSlideIndex === item.slides.length - 1}
                        className="absolute right-2 top-1/2 -translate-y-1/2 w-8 h-8 rounded-full bg-black/40 hover:bg-black/60 flex items-center justify-center text-white disabled:opacity-0 transition-opacity duration-200 z-10"
                      >
                        &gt;
                      </button>

                      {/* Displaying bound state */}
                      {(() => {
                        const slide = item.slides[currentMockupSlideIndex];
                        const editSlide = editedSlides[currentMockupSlideIndex];
                        const textToShow = isEditing && editSlide 
                          ? editSlide.text_content 
                          : slide.text_content;

                        const hasEdits = isEditing && editSlide && editSlide.text_content !== slide.text_content;
                        // [SOLID: SRP] - Do not overlay text HTML elements if it is already baked into the image
                        const shouldShowOverlay = !item.avoid_image_generation || hasEdits;

                        if (slide.image_url) {
                          if (!shouldShowOverlay) {
                            return (
                              <div 
                                className="w-full h-full bg-cover bg-center"
                                style={{ backgroundImage: `url(${slide.image_url})` }}
                              />
                            );
                          }
                          return (
                            <div 
                              className="w-full h-full flex flex-col items-center justify-center p-8 text-center bg-cover bg-center relative"
                              style={{ backgroundImage: `url(${slide.image_url})` }}
                            >
                              <div className="absolute inset-0 bg-black/45 z-0"></div>
                              <div className="z-10 text-white drop-shadow-md flex flex-col items-center space-y-2">
                                {slide.emoji && <span className="text-2xl">{slide.emoji}</span>}
                                <p className="text-xs md:text-sm font-semibold leading-relaxed max-w-[200px]">{textToShow}</p>
                                {slide.caption && <p className="text-[9px] opacity-75 italic">{slide.caption}</p>}
                              </div>
                            </div>
                          );
                        } else if (item.background_image_url) {
                          return (
                            <div 
                              className="w-full h-full flex flex-col items-center justify-center p-8 text-center bg-cover bg-center relative"
                              style={{ backgroundImage: `url(${item.background_image_url})` }}
                            >
                              <div className="absolute inset-0 bg-black/35 z-0"></div>
                              <div className="z-10 text-white drop-shadow-md flex flex-col items-center space-y-2">
                                {slide.emoji && <span className="text-2xl">{slide.emoji}</span>}
                                <p className="text-xs md:text-sm font-semibold leading-relaxed max-w-[200px]">{textToShow}</p>
                                {slide.caption && <p className="text-[9px] opacity-75 italic">{slide.caption}</p>}
                              </div>
                            </div>
                          );
                        } else {
                          return (
                            <div className="w-full h-full flex flex-col items-center justify-center p-8 text-center bg-gradient-to-br from-purple-900 to-indigo-950 text-white space-y-2">
                              {slide.emoji && <span className="text-2xl">{slide.emoji}</span>}
                              <p className="text-[10px] md:text-xs font-medium leading-relaxed max-w-[200px]">{textToShow}</p>
                              {slide.caption && <p className="text-[9px] opacity-75 italic">{slide.caption}</p>}
                            </div>
                          );
                        }
                      })()}
                    </div>

                    {/* Instagram actions bar & paginator dots */}
                    <div className="p-3 space-y-2">
                      <div className="flex items-center justify-between">
                        <div className="flex items-center space-x-3.5">
                          <svg className="w-5.5 h-5.5 stroke-white fill-none cursor-pointer" viewBox="0 0 24 24"><path strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" d="M4.318 6.318a4.5 4.5 0 000 6.364L12 20.364l7.682-7.682a4.5 4.5 0 00-6.364-6.364L12 7.636l-1.318-1.318a4.5 4.5 0 00-6.364 0z"/></svg>
                          <svg className="w-5.5 h-5.5 stroke-white fill-none cursor-pointer" viewBox="0 0 24 24"><path strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" d="M8 12h.01M12 12h.01M16 12h.01M21 12c0 4.418-4.03 8-9 8a9.863 9.863 0 01-4.255-.949L3 20l1.395-3.72C3.512 15.042 3 13.574 3 12c0-4.418 4.03-8 9-8s9 3.582 9 8z"/></svg>
                          <svg className="w-5.5 h-5.5 stroke-white fill-none cursor-pointer" viewBox="0 0 24 24"><path strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" d="M8.684 10.742l1.636 1.636 6.136-9.136H8.684V10.742zm0 0L5 14.398v-3.656h3.684z"/></svg>
                        </div>
                        
                        {/* Dots pagination */}
                        <div className="flex space-x-1.5">
                          {item.slides.map((_, idx) => (
                            <div 
                              key={idx} 
                              className={`w-1.5 h-1.5 rounded-full transition-all duration-200 ${idx === currentMockupSlideIndex ? 'bg-blue-500 scale-125' : 'bg-gray-600'}`}
                            />
                          ))}
                        </div>
                        
                        <svg className="w-5.5 h-5.5 stroke-white fill-none cursor-pointer" viewBox="0 0 24 24"><path strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" d="M5 5a2 2 0 012-2h10a2 2 0 012 2v16l-7-3.5L5 21V5z"/></svg>
                      </div>
                      
                      {/* Caption text */}
                      <div className="text-[12px] leading-tight break-words">
                        <span className="font-semibold mr-1.5">{item.project_name.toLowerCase().replace(/\s+/g, "_")}</span>
                        {item.article_title.slice(0, 95)}...
                      </div>
                    </div>
                  </div>
                )}
              </div>
            )}
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
            {/* Platform Mockup Preview Button */}
            <Button 
              variant={showPreview ? "secondary" : "outline"} 
              onClick={() => {
                setShowPreview(!showPreview);
                setCurrentMockupSlideIndex(0);
              }}
              disabled={isWorking}
              className="rounded-lg shadow-sm transition-all"
            >
              <ImageIcon className="mr-2 h-4 w-4" />
              {showPreview ? "Hide Mockup" : "Feed Preview"}
            </Button>

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
