"use client";

import { useState, useEffect } from "react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Plus, Settings, Play, LayoutGrid, ArrowRight, MoreVertical, Edit, Copy, Trash2, Eye } from "lucide-react";
import Link from "next/link";
import { useProjectStore, Project } from "@/store/projectStore";
import { useAuth } from "@/contexts/AuthContext";
import { Skeleton } from "@/components/ui/skeleton";
import { Avatar, AvatarFallback } from "@/components/ui/avatar";
import { Badge } from "@/components/ui/badge";
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu";
import { CreateProjectDialog } from "@/components/CreateProjectDialog";
import { toast } from "sonner";
import { PreviewModal } from "@/components/PreviewModal";

import { Progress } from "@/components/ui/progress";

function getProgressValue(status: string): number {
  if (status === "Not started") return 0;
  if (status.includes("Starting")) return 5;
  if (status.includes("research")) return 20;
  if (status.includes("verify") && !status.includes("verify_slides")) return 40;
  if (status.includes("refine")) return 45;
  if (status.includes("generate")) return 60;
  if (status.includes("verify_slides")) return 80;
  if (status.includes("publish")) return 95;
  if (status === "Completed") return 100;
  return 10;
}

function ProjectCard({ project }: { project: Project }) {
  const [status, setStatus] = useState<string>("Not started");
  const [isPolling, setIsPolling] = useState(false);
  const fetchProjectStatus = useProjectStore((state) => state.fetchProjectStatus);
  const runWorkflow = useProjectStore((state) => state.runWorkflow);

  useEffect(() => {
    // Initial fetch
    fetchProjectStatus(project.id).then(s => setStatus(s));
  }, [project.id, fetchProjectStatus]);

  useEffect(() => {
    let interval: NodeJS.Timeout;
    if (isPolling || status.includes("working") || status.includes("Starting")) {
      interval = setInterval(async () => {
        const s = await fetchProjectStatus(project.id);
        setStatus(s);
        if (s === "Completed") setIsPolling(false);
      }, 2000);
    }
    return () => clearInterval(interval);
  }, [project.id, isPolling, status, fetchProjectStatus]);

  const handleRunWorkflow = async () => {
    try {
      await runWorkflow(project.id);
      setIsPolling(true);
      setStatus("Starting workflow...");
      toast.success("Workflow queued successfully!");
    } catch (err) {
      toast.error("Failed to queue workflow");
    }
  };

  const isCompleted = status === "Completed";
  const isWorking = status.includes("working") || status.includes("Starting");
  const hasStarted = status !== "Not started";
  const progressValue = getProgressValue(status);

  return (
    <Card className="group overflow-hidden border border-border/50 bg-card hover:bg-accent/5 transition-all duration-300 hover:-translate-y-1 hover:shadow-xl hover:border-primary/30 relative flex flex-col h-full">
      <div className="absolute top-0 left-0 w-full h-1 bg-gradient-to-r from-primary to-destructive opacity-0 group-hover:opacity-100 transition-opacity duration-300" />

      <CardHeader className="flex flex-row items-start justify-between space-y-0 pb-4">
        <div className="flex items-center gap-4">
          <Avatar className="h-12 w-12 border-2 border-primary/20 shadow-sm">
            <AvatarFallback className="bg-primary/10 text-primary font-bold font-heading">
              {project.name.substring(0, 2).toUpperCase()}
            </AvatarFallback>
          </Avatar>
          <div className="space-y-1 w-full max-w-[200px]">
            <CardTitle className="text-xl font-heading font-bold tracking-tight group-hover:text-primary transition-colors line-clamp-1">
              {project.name}
            </CardTitle>
            <div className="flex items-center gap-2">
              <Badge variant="secondary" className="font-medium whitespace-nowrap">
                {project.industry}
              </Badge>
              {hasStarted && (
                <Badge variant={isCompleted ? "default" : "outline"} className={isWorking ? "animate-pulse truncate" : "truncate"}>
                  {status}
                </Badge>
              )}
            </div>
          </div>
        </div>
        <DropdownMenu>
          <DropdownMenuTrigger render={<Button variant="ghost" size="icon" className="text-muted-foreground hover:text-foreground hover:bg-accent rounded-full h-8 w-8 shrink-0 -mr-2" />}>
            <MoreVertical className="h-4 w-4" />
            <span className="sr-only">Open menu</span>
          </DropdownMenuTrigger>
          <DropdownMenuContent align="end" className="w-[160px]">
            <DropdownMenuItem render={<Link href={`/projects/${project.id}/settings`} className="cursor-pointer flex items-center w-full" />}>
              <Settings className="mr-2 h-4 w-4" />
              Settings
            </DropdownMenuItem>
            <DropdownMenuItem>
              <Edit className="mr-2 h-4 w-4" />
              Edit Details
            </DropdownMenuItem>
            <DropdownMenuItem>
              <Copy className="mr-2 h-4 w-4" />
              Duplicate
            </DropdownMenuItem>
            <DropdownMenuSeparator />
            <DropdownMenuItem className="text-destructive focus:text-destructive">
              <Trash2 className="mr-2 h-4 w-4" />
              Delete Project
            </DropdownMenuItem>
          </DropdownMenuContent>
        </DropdownMenu>
      </CardHeader>
      
      <CardContent className="mt-auto">
        {hasStarted && (
          <div className="space-y-2 mb-4">
             <div className="flex justify-between text-xs text-muted-foreground">
               <span>Progress</span>
               <span>{progressValue}%</span>
             </div>
             <Progress value={progressValue} className="h-2" />
          </div>
        )}
        
        <div className="pt-4 border-t border-border/40 space-y-2">
          {!isCompleted && (
            <Button
              className="w-full justify-between rounded-lg font-medium bg-secondary text-secondary-foreground hover:bg-primary hover:text-primary-foreground group/btn transition-colors"
              onClick={handleRunWorkflow}
              disabled={isWorking}
            >
              <span className="flex items-center">
                <Play className="mr-2 h-4 w-4" /> {isWorking ? "Workflow Running..." : "Run Workflow"}
              </span>
              {!isWorking && <ArrowRight className="h-4 w-4 opacity-50 group-hover/btn:opacity-100 group-hover/btn:translate-x-1 transition-all" />}
            </Button>
          )}

          {hasStarted && (
            <PreviewModal projectId={project.id}>
              <Button className="w-full justify-between rounded-lg font-medium" variant={isCompleted ? "default" : "outline"}>
                <span className="flex items-center">
                  <Eye className="mr-2 h-4 w-4" /> {isCompleted ? "View Final Results" : "Live Preview"}
                </span>
                <ArrowRight className="h-4 w-4 opacity-50" />
              </Button>
            </PreviewModal>
          )}
        </div>
      </CardContent>
    </Card>
  );
}

export default function DashboardPage() {
  const projects = useProjectStore((state) => state.projects);
  const isLoading = useProjectStore((state) => state.isLoading);
  const fetchProjects = useProjectStore((state) => state.fetchProjects);
  const { user, loading: authLoading } = useAuth();

  useEffect(() => {
    if (!authLoading && user) {
      fetchProjects();
    }
  }, [fetchProjects, authLoading, user]);

  return (
    <div className="space-y-8 animate-in fade-in duration-500 max-w-7xl mx-auto">
      <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4">
        <div className="space-y-1">
          <h1 className="text-3xl md:text-4xl font-heading font-bold tracking-tight text-foreground">
            Projects
          </h1>
          <p className="text-muted-foreground font-medium">Manage your automated content workflows.</p>
        </div>
        <CreateProjectDialog>
          <Button size="lg" className="shrink-0 rounded-xl font-medium shadow-md hover:shadow-lg transition-all duration-200">
            <Plus className="mr-2 h-5 w-5" /> New Project
          </Button>
        </CreateProjectDialog>
      </div>

      {isLoading || authLoading ? (
        <div className="grid gap-6 md:grid-cols-2 lg:grid-cols-3">
          {[1, 2, 3].map((i) => (
            <Card key={i} className="overflow-hidden border border-border/50 bg-card">
              <CardHeader className="flex flex-row items-start justify-between space-y-0 pb-4">
                <div className="flex items-center gap-4">
                  <Skeleton className="h-12 w-12 rounded-full" />
                  <div className="space-y-2">
                    <Skeleton className="h-5 w-32" />
                    <Skeleton className="h-4 w-20" />
                  </div>
                </div>
                <Skeleton className="h-8 w-8 rounded-full" />
              </CardHeader>
              <CardContent>
                <div className="pt-4 mt-2 border-t border-border/40">
                  <Skeleton className="h-10 w-full rounded-lg" />
                </div>
              </CardContent>
            </Card>
          ))}
        </div>
      ) : (
        <div className="grid gap-6 md:grid-cols-2 lg:grid-cols-3">
          {projects.map((project) => (
            <ProjectCard key={project.id} project={project} />
          ))}

          {projects.length === 0 && (
            <div className="col-span-full flex flex-col items-center justify-center py-20 px-4 text-center border border-dashed border-border/60 bg-card/30 hover:bg-card/50 transition-colors rounded-2xl">
              <div className="w-16 h-16 rounded-2xl bg-primary/10 flex items-center justify-center mb-6 shadow-inner">
                <LayoutGrid className="h-8 w-8 text-primary" />
              </div>
              <h3 className="text-2xl font-heading font-bold mb-2 tracking-tight">No projects found</h3>
              <p className="text-muted-foreground mb-8 max-w-md font-medium">
                Create your first project to start generating automated social content workflows.
              </p>
              <CreateProjectDialog>
                <Button size="lg" className="rounded-xl shadow-md hover:shadow-lg transition-all hover:-translate-y-0.5">
                  <Plus className="mr-2 h-5 w-5" /> Create First Project
                </Button>
              </CreateProjectDialog>
            </div>
          )}
        </div>
      )}
    </div>
  );
}
