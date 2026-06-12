"use client";

import { useEffect } from "react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Plus, Settings, Play, LayoutGrid, ArrowRight, MoreVertical, Edit, Copy, Trash2 } from "lucide-react";
import Link from "next/link";
import { useProjectStore } from "@/store/projectStore";
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

export default function DashboardPage() {
  const projects = useProjectStore((state) => state.projects);
  const isLoading = useProjectStore((state) => state.isLoading);
  const fetchProjects = useProjectStore((state) => state.fetchProjects);

  useEffect(() => {
    fetchProjects();
  }, [fetchProjects]);

  return (
    <div className="space-y-8 animate-in fade-in duration-500 max-w-7xl mx-auto">
      {/* Block-Based Header */}
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

      {isLoading ? (
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
        /* Projects Grid */
        <div className="grid gap-6 md:grid-cols-2 lg:grid-cols-3">
          {projects.map((project) => (
            <Card key={project.id} className="group overflow-hidden border border-border/50 bg-card hover:bg-accent/5 transition-all duration-300 hover:-translate-y-1 hover:shadow-xl hover:border-primary/30 relative">
              {/* Top accent line on hover */}
              <div className="absolute top-0 left-0 w-full h-1 bg-gradient-to-r from-primary to-destructive opacity-0 group-hover:opacity-100 transition-opacity duration-300" />
              
              <CardHeader className="flex flex-row items-start justify-between space-y-0 pb-4">
                <div className="flex items-center gap-4">
                  <Avatar className="h-12 w-12 border-2 border-primary/20 shadow-sm">
                    <AvatarFallback className="bg-primary/10 text-primary font-bold font-heading">
                      {project.name.substring(0, 2).toUpperCase()}
                    </AvatarFallback>
                  </Avatar>
                  <div className="space-y-1">
                    <CardTitle className="text-xl font-heading font-bold tracking-tight group-hover:text-primary transition-colors line-clamp-1">
                      {project.name}
                    </CardTitle>
                    <Badge variant="secondary" className="font-medium">
                      {project.industry}
                    </Badge>
                  </div>
                </div>
                <DropdownMenu>
                  <DropdownMenuTrigger render={<Button variant="ghost" size="icon" className="text-muted-foreground hover:text-foreground hover:bg-accent rounded-full h-8 w-8 -mr-2" />}>
                    <MoreVertical className="h-4 w-4" />
                    <span className="sr-only">Open menu</span>
                  </DropdownMenuTrigger>
                  <DropdownMenuContent align="end" className="w-[160px]">
                    <DropdownMenuItem render={<Link href={`/projects/${project.id}/settings`} className="cursor-pointer" />}>
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
              <CardContent>
                <div className="pt-4 mt-2 border-t border-border/40">
                  <Button className="w-full justify-between rounded-lg font-medium bg-secondary text-secondary-foreground hover:bg-primary hover:text-primary-foreground group/btn transition-colors">
                    <span className="flex items-center">
                      <Play className="mr-2 h-4 w-4" /> Run Workflow
                    </span>
                    <ArrowRight className="h-4 w-4 opacity-50 group-hover/btn:opacity-100 group-hover/btn:translate-x-1 transition-all" />
                  </Button>
                </div>
              </CardContent>
            </Card>
          ))}
          
          {/* Empty State */}
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
