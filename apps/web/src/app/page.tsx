import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Plus, Settings, Play, LayoutGrid, ArrowRight } from "lucide-react";
import Link from "next/link";

interface Project {
  id: number;
  name: string;
  industry: string;
}

async function getProjects(): Promise<Project[]> {
  try {
    const res = await fetch("http://127.0.0.1:8000/projects", { cache: "no-store" });
    if (!res.ok) return [];
    return await res.json();
  } catch (e) {
    // Return empty if backend is down during MVP
    return [];
  }
}

export default async function DashboardPage() {
  const projects = await getProjects();

  return (
    <div className="space-y-10 animate-in fade-in duration-500">
      {/* Block-Based Header */}
      <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4 bg-card/80 border border-border/40 p-6 md:p-8 rounded-2xl shadow-sm backdrop-blur-xl">
        <div className="space-y-2">
          <div className="inline-flex items-center rounded-full border border-primary/20 bg-primary/10 px-2.5 py-0.5 text-xs font-semibold text-primary mb-2 transition-colors focus:outline-none focus:ring-2 focus:ring-ring focus:ring-offset-2">
            Workspace
          </div>
          <h1 className="text-3xl md:text-4xl font-heading font-bold tracking-tight text-foreground">
            Projects
          </h1>
          <p className="text-muted-foreground font-medium">Manage your automated content workflows.</p>
        </div>
        <Button size="lg" className="shrink-0 rounded-xl font-medium shadow-md hover:shadow-lg transition-all duration-200">
          <Plus className="mr-2 h-5 w-5" /> New Project
        </Button>
      </div>

      {/* Projects Grid */}
      <div className="grid gap-6 md:grid-cols-2 lg:grid-cols-3">
        {projects.map((project) => (
          <Card key={project.id} className="group overflow-hidden border border-border/50 bg-card hover:bg-accent/5 transition-all duration-300 hover:-translate-y-1 hover:shadow-xl hover:border-primary/30 relative">
            {/* Top accent line on hover */}
            <div className="absolute top-0 left-0 w-full h-1 bg-gradient-to-r from-primary to-destructive opacity-0 group-hover:opacity-100 transition-opacity duration-300" />
            
            <CardHeader className="flex flex-row items-start justify-between space-y-0 pb-4">
              <div className="space-y-1.5">
                <CardTitle className="text-2xl font-heading font-bold tracking-tight group-hover:text-primary transition-colors">
                  {project.name}
                </CardTitle>
                <div className="inline-flex items-center rounded-full bg-secondary px-2.5 py-0.5 text-xs font-medium text-secondary-foreground">
                  {project.industry}
                </div>
              </div>
              <Link href={`/projects/${project.id}/settings`}>
                <Button variant="ghost" size="icon" className="text-muted-foreground hover:text-primary hover:bg-primary/10 rounded-full h-9 w-9">
                  <Settings className="h-4 w-4" />
                </Button>
              </Link>
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
          <div className="col-span-full flex flex-col items-center justify-center p-12 text-center border-2 rounded-2xl border-dashed border-border/60 bg-card/30 hover:bg-card/50 transition-colors">
            <div className="w-16 h-16 rounded-full bg-primary/10 flex items-center justify-center mb-6">
              <LayoutGrid className="h-8 w-8 text-primary" />
            </div>
            <h3 className="text-2xl font-heading font-bold mb-3 tracking-tight">No projects yet</h3>
            <p className="text-muted-foreground mb-8 max-w-md font-medium">
              Create your first project to start generating carousels. Automated social content is just a few clicks away.
            </p>
            <Button size="lg" className="rounded-xl shadow-md hover:shadow-lg transition-all hover:-translate-y-0.5">
              <Plus className="mr-2 h-5 w-5" /> Create First Project
            </Button>
          </div>
        )}
      </div>
    </div>
  );
}
