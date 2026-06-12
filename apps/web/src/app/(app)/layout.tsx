import { SidebarProvider, SidebarTrigger } from "@/components/ui/sidebar";
import { AppSidebar } from "@/components/app-sidebar";

export default function AppLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <SidebarProvider>
      <AppSidebar />
      <main className="flex-1 w-full flex flex-col bg-background/95 relative min-h-screen">
        <header className="sticky top-0 z-10 flex h-14 shrink-0 items-center gap-2 border-b border-border/40 bg-background/80 backdrop-blur-sm px-4 md:px-6">
          <SidebarTrigger className="-ml-2 text-muted-foreground hover:text-foreground" />
        </header>
        <div className="flex-1 p-6 md:p-8">
          {children}
        </div>
      </main>
    </SidebarProvider>
  );
}
