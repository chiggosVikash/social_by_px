import type { Metadata } from "next";
import { DM_Sans, Space_Grotesk } from "next/font/google";
import "./globals.css";
import Link from "next/link";
import { Toaster } from "@/components/ui/sonner";
import { LayoutDashboard, CheckSquare, Settings } from "lucide-react";

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
        <div className="flex h-screen w-full bg-background">
          <aside className="w-64 border-r border-border/40 bg-card/50 flex flex-col p-6 gap-6 shadow-sm z-10 backdrop-blur-sm">
            <div className="flex items-center gap-3 mb-4">
              <div className="w-8 h-8 rounded-lg bg-primary flex items-center justify-center">
                <span className="text-primary-foreground font-heading font-bold text-lg">AI</span>
              </div>
              <h1 className="text-xl font-heading font-bold tracking-tight text-foreground">Content Studio</h1>
            </div>
            <nav className="flex flex-col gap-2 flex-1">
              <Link href="/" className="flex items-center gap-3 px-3 py-2.5 hover:bg-accent hover:text-accent-foreground rounded-lg transition-all duration-200 font-medium group">
                <LayoutDashboard className="w-5 h-5 text-muted-foreground group-hover:text-primary transition-colors" />
                Projects
              </Link>
              <Link href="/approvals" className="flex items-center gap-3 px-3 py-2.5 hover:bg-accent hover:text-accent-foreground rounded-lg transition-all duration-200 font-medium group">
                <CheckSquare className="w-5 h-5 text-muted-foreground group-hover:text-primary transition-colors" />
                Approvals
              </Link>
              <Link href="/settings" className="flex items-center gap-3 px-3 py-2.5 hover:bg-accent hover:text-accent-foreground rounded-lg transition-all duration-200 font-medium group mt-auto">
                <Settings className="w-5 h-5 text-muted-foreground group-hover:text-primary transition-colors" />
                Settings
              </Link>
            </nav>
          </aside>
          <main className="flex-1 overflow-y-auto bg-background/95 relative">
            {children}
          </main>
        </div>
        <Toaster />
      </body>
    </html>
  );
}
