"use client";

import { useState, useRef } from "react";
import { Dialog, DialogContent, DialogDescription, DialogFooter, DialogHeader, DialogTitle } from "@/components/ui/dialog";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { useProjectStore, Project } from "@/store/projectStore";
import { toast } from "sonner";
import { Loader2, Upload, Check, ImageIcon } from "lucide-react";
import { apiClient } from "@/lib/api-client";

interface ProjectSettingsDialogProps {
  project: Project;
  open: boolean;
  onOpenChange: (open: boolean) => void;
}

export function ProjectSettingsDialog({ project, open, onOpenChange }: ProjectSettingsDialogProps) {
  const [name, setName] = useState(project.name);
  const [industry, setIndustry] = useState(project.industry || "");
  const [avoidImageGeneration, setAvoidImageGeneration] = useState(project.avoid_image_generation || false);
  const [backgroundUrl, setBackgroundUrl] = useState<string | null>(project.background_image_url || null);
  const [isSaving, setIsSaving] = useState(false);
  const [isUploading, setIsUploading] = useState(false);
  const fileInputRef = useRef<HTMLInputElement>(null);
  
  const updateProjectSettings = useProjectStore((state) => state.updateProjectSettings);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!name.trim()) return;

    setIsSaving(true);
    try {
      await updateProjectSettings(project.id, {
        name: name.trim(),
        industry: industry.trim(),
        avoid_image_generation: avoidImageGeneration,
      });
      toast.success("Project settings updated!");
      onOpenChange(false);
    } catch (error) {
      console.error("Failed to update project settings", error);
      toast.error("Failed to update project settings.");
    } finally {
      setIsSaving(false);
    }
  };

  const handleFileChange = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;

    // Validate size (< 5MB)
    if (file.size > 5 * 1024 * 1024) {
      toast.error("File is too large. Max size is 5MB.");
      return;
    }

    // Validate format
    const allowedTypes = ["image/jpeg", "image/png", "image/webp"];
    if (!allowedTypes.includes(file.type)) {
      toast.error("Invalid file type. Allowed: JPEG, PNG, WebP.");
      return;
    }

    setIsUploading(true);
    const formData = new FormData();
    formData.append("file", file);

    try {
      const response = await apiClient.post<Project>(`/projects/${project.id}/background`, formData, {
        headers: {
          "Content-Type": "multipart/form-data",
        },
      });
      
      setBackgroundUrl(response.data.background_image_url);
      toast.success("Background image uploaded successfully!");
      
      // Auto-update avoid_image_generation if uploaded
      if (!avoidImageGeneration) {
        setAvoidImageGeneration(true);
      }
    } catch (error) {
      console.error("Failed to upload background image", error);
      toast.error("Failed to upload background image.");
    } finally {
      setIsUploading(false);
    }
  };

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="sm:max-w-[450px]">
        <DialogHeader>
          <DialogTitle>Project Settings</DialogTitle>
          <DialogDescription>
            Modify settings and configure branding template for "{project.name}".
          </DialogDescription>
        </DialogHeader>
        <form onSubmit={handleSubmit} className="grid gap-5 py-4">
          <div className="grid grid-cols-4 items-center gap-4">
            <Label htmlFor="edit-name" className="text-right font-medium">
              Name
            </Label>
            <Input
              id="edit-name"
              value={name}
              onChange={(e) => setName(e.target.value)}
              className="col-span-3"
              required
            />
          </div>
          
          <div className="grid grid-cols-4 items-center gap-4">
            <Label htmlFor="edit-industry" className="text-right font-medium">
              Industry
            </Label>
            <Input
              id="edit-industry"
              value={industry}
              onChange={(e) => setIndustry(e.target.value)}
              className="col-span-3"
            />
          </div>
          
          <div className="grid grid-cols-4 items-start gap-4">
            <Label htmlFor="edit-avoid" className="text-right text-xs leading-tight font-medium pt-1">
              Avoid AI Images
            </Label>
            <div className="col-span-3 flex items-center gap-2">
              <input
                type="checkbox"
                id="edit-avoid"
                checked={avoidImageGeneration}
                onChange={(e) => setAvoidImageGeneration(e.target.checked)}
                className="h-4 w-4 rounded border-gray-300 text-primary focus:ring-primary cursor-pointer"
              />
              <span className="text-xs text-muted-foreground">Skip DALL-E, upload your own background template instead.</span>
            </div>
          </div>

          <div className="border-t pt-4 grid grid-cols-4 items-start gap-4">
            <Label className="text-right font-medium pt-1 text-xs sm:text-sm">
              Background Template
            </Label>
            <div className="col-span-3 space-y-3">
              {backgroundUrl ? (
                <div className="relative rounded-lg overflow-hidden border border-border aspect-square w-full max-w-[150px] bg-muted group">
                  <img 
                    src={backgroundUrl} 
                    alt="Background template" 
                    className="object-cover w-full h-full"
                  />
                  <div className="absolute inset-0 bg-black/40 flex items-center justify-center opacity-0 group-hover:opacity-100 transition-opacity">
                    <Button 
                      type="button" 
                      variant="destructive" 
                      size="sm"
                      className="h-8 text-xs"
                      onClick={() => setBackgroundUrl(null)}
                    >
                      Remove
                    </Button>
                  </div>
                </div>
              ) : (
                <div 
                  className="border-2 border-dashed border-muted-foreground/30 hover:border-primary/50 transition-colors rounded-lg flex flex-col items-center justify-center p-6 bg-muted/20 cursor-pointer"
                  onClick={() => fileInputRef.current?.click()}
                >
                  <Upload className="h-6 w-6 text-muted-foreground mb-2" />
                  <span className="text-xs font-medium text-muted-foreground">Upload background template image</span>
                  <span className="text-[10px] text-muted-foreground/60 mt-1">PNG, JPG or WebP (max 5MB, recommended 1080x1080)</span>
                </div>
              )}
              
              <input 
                type="file" 
                ref={fileInputRef} 
                onChange={handleFileChange} 
                className="hidden" 
                accept="image/png, image/jpeg, image/webp"
              />
              
              {isUploading && (
                <div className="flex items-center text-xs text-muted-foreground gap-2">
                  <Loader2 className="h-3.5 w-3.5 animate-spin text-primary" />
                  Uploading background image...
                </div>
              )}
            </div>
          </div>

          <DialogFooter>
            <Button type="button" variant="outline" onClick={() => onOpenChange(false)} disabled={isSaving}>
              Cancel
            </Button>
            <Button type="submit" disabled={isSaving || isUploading || !name.trim()}>
              {isSaving ? <Loader2 className="h-4 w-4 animate-spin mr-2" /> : null}
              Save Settings
            </Button>
          </DialogFooter>
        </form>
      </DialogContent>
    </Dialog>
  );
}
