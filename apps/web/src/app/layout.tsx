import type { Metadata } from "next";
import { DM_Sans, Space_Grotesk } from "next/font/google";
import "./globals.css";
import { Toaster } from "@/components/ui/sonner";
import { SidebarProvider, SidebarTrigger } from "@/components/ui/sidebar";
import { AppSidebar } from "@/components/app-sidebar";
import { TooltipProvider } from "@/components/ui/tooltip";
import { AuthProvider } from "@/contexts/AuthContext";
import ProtectedRoute from "@/components/ProtectedRoute";

const fontSans = DM_Sans({
  subsets: ["latin"],
  variable: "--font-sans",
});

const fontHeading = Space_Grotesk({
  subsets: ["latin"],
  variable: "--font-heading",
});

export const metadata: Metadata = {
  title: "AI Content Studio",
  description: "News-to-Carousel Automation",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en" className="dark">
      <body className={`${fontSans.variable} ${fontHeading.variable} font-sans antialiased`}>
        <AuthProvider>
          <TooltipProvider>
            <ProtectedRoute>
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
            </ProtectedRoute>
            <Toaster />
          </TooltipProvider>
        </AuthProvider>
      </body>
    </html>
  );
}
