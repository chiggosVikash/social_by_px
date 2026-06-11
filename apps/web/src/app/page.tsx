import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Plus, Settings, Play } from "lucide-react";
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
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <h1 className="text-3xl font-bold tracking-tight">Projects</h1>
        <Button>
          <Plus className="mr-2 h-4 w-4" /> New Project
        </Button>
      </div>

      <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
        {projects.map((project) => (
          <Card key={project.id}>
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
              <CardTitle className="text-xl font-bold">{project.name}</CardTitle>
              <Link href={`/projects/${project.id}/settings`}>
                <Button variant="ghost" size="icon">
                  <Settings className="h-4 w-4" />
                </Button>
              </Link>
            </CardHeader>
            <CardContent>
              <div className="text-sm text-muted-foreground mb-4">Industry: {project.industry}</div>
              <div className="flex gap-2">
                <Button size="sm" className="w-full">
                  <Play className="mr-2 h-4 w-4" /> Run Workflow
                </Button>
              </div>
            </CardContent>
          </Card>
        ))}
        {projects.length === 0 && (
          <div className="col-span-full p-8 text-center border rounded-lg border-dashed">
            <h3 className="text-lg font-medium mb-2">No projects found</h3>
            <p className="text-sm text-muted-foreground mb-4">Create your first project to start generating carousels. (Or ensure API is running on port 8000)</p>
            <Button variant="outline">
              <Plus className="mr-2 h-4 w-4" /> Create Project
            </Button>
          </div>
        )}
      </div>
    </div>
  );
}
