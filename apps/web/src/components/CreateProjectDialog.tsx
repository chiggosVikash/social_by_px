"use client";

import { useState } from "react";
import { Dialog, DialogContent, DialogDescription, DialogFooter, DialogHeader, DialogTitle, DialogTrigger } from "@/components/ui/dialog";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { useProjectStore } from "@/store/projectStore";

interface CreateProjectDialogProps {
  children: React.ReactElement;
}

const STYLE_PRESETS = [
  { id: "general_soft", label: "General (Soft & Warm)" },
  { id: "tech_editorial", label: "Tech & Editorial" },
  { id: "health_warm", label: "Health & Wellness" },
  { id: "finance_paper", label: "Finance & Markets" },
  { id: "education_warm", label: "Education & Learning" },
  { id: "marketing_bold", label: "Marketing & Brand" },
];

export function CreateProjectDialog({ children }: CreateProjectDialogProps) {
  const [open, setOpen] = useState(false);
  const [name, setName] = useState("");
  const [industry, setIndustry] = useState("");
  const [keywords, setKeywords] = useState("");
  const [avoidImageGeneration, setAvoidImageGeneration] = useState(false);
  const [stylePreset, setStylePreset] = useState("general_soft");
  const [isSubmitting, setIsSubmitting] = useState(false);

  const createProject = useProjectStore((state) => state.createProject);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!name.trim()) return;

    setIsSubmitting(true);
    try {
      const keywordList = keywords
        .split(",")
        .map((k) => k.trim())
        .filter((k) => k.length > 0);

      await createProject({
        name: name.trim(),
        industry: industry.trim(),
        keywords: keywordList,
        avoid_image_generation: avoidImageGeneration,
        style_preset: stylePreset,
      });

      // Reset and close
      setName("");
      setIndustry("");
      setKeywords("");
      setAvoidImageGeneration(false);
      setStylePreset("general_soft");
      setOpen(false);
    } catch (error) {
      console.error("Failed to create project", error);
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <Dialog open={open} onOpenChange={setOpen}>
      <DialogTrigger render={children} />
      <DialogContent className="sm:max-w-[425px]">
        <DialogHeader>
          <DialogTitle>Create New Project</DialogTitle>
          <DialogDescription>
            Enter the details for your new automated content workflow project.
          </DialogDescription>
        </DialogHeader>
        <form onSubmit={handleSubmit} className="grid gap-4 py-4">
          <div className="grid grid-cols-4 items-center gap-4">
            <Label htmlFor="name" className="text-right">
              Name
            </Label>
            <Input
              id="name"
              value={name}
              onChange={(e) => setName(e.target.value)}
              className="col-span-3"
              placeholder="e.g. AI Startup News"
              required
            />
          </div>
          <div className="grid grid-cols-4 items-center gap-4">
            <Label htmlFor="industry" className="text-right">
              Industry
            </Label>
            <Input
              id="industry"
              value={industry}
              onChange={(e) => setIndustry(e.target.value)}
              className="col-span-3"
              placeholder="e.g. Technology"
            />
          </div>
          <div className="grid grid-cols-4 items-center gap-4">
            <Label htmlFor="keywords" className="text-right">
              Keywords
            </Label>
            <Input
              id="keywords"
              value={keywords}
              onChange={(e) => setKeywords(e.target.value)}
              className="col-span-3"
              placeholder="e.g. AI, Machine Learning, Tech"
            />
          </div>
          <div className="grid grid-cols-4 items-center gap-4">
            <Label htmlFor="avoidImageGeneration" className="text-right text-xs leading-tight">
              Avoid AI Images
            </Label>
            <div className="col-span-3 flex items-center gap-2">
              <input
                type="checkbox"
                id="avoidImageGeneration"
                checked={avoidImageGeneration}
                onChange={(e) => setAvoidImageGeneration(e.target.checked)}
                className="h-4 w-4 rounded border-gray-300 text-primary focus:ring-primary cursor-pointer"
              />
              <span className="text-xs text-muted-foreground">Skip DALL-E, upload your own background template instead.</span>
            </div>
          </div>
          <div className="grid grid-cols-4 items-center gap-4">
            <Label htmlFor="stylePreset" className="text-right text-xs leading-tight">
              Visual Style
            </Label>
            <select
              id="stylePreset"
              value={stylePreset}
              onChange={(e) => setStylePreset(e.target.value)}
              className="col-span-3 flex h-9 w-full rounded-md border border-input bg-transparent px-3 py-1 text-sm shadow-sm focus:outline-none focus:ring-1 focus:ring-ring cursor-pointer"
            >
              {STYLE_PRESETS.map((p) => (
                <option key={p.id} value={p.id}>
                  {p.label}
                </option>
              ))}
            </select>
          </div>
          <DialogFooter>
            <Button type="button" variant="outline" onClick={() => setOpen(false)}>
              Cancel
            </Button>
            <Button type="submit" disabled={isSubmitting || !name.trim()}>
              {isSubmitting ? "Creating..." : "Create Project"}
            </Button>
          </DialogFooter>
        </form>
      </DialogContent>
    </Dialog>
  );
}
