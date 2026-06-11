import type { Metadata } from "next";
import { Inter } from "next/font/google";
import "./globals.css";
import Link from "next/link";
import { Toaster } from "@/components/ui/sonner";

const inter = Inter({ subsets: ["latin"] });

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
    <html lang="en">
      <body className={inter.className}>
        <div className="flex h-screen w-full">
          <aside className="w-64 border-r bg-muted/20 flex flex-col p-4 gap-4">
            <h1 className="text-xl font-bold mb-8">AI Content Studio</h1>
            <nav className="flex flex-col gap-2">
              <Link href="/" className="px-3 py-2 hover:bg-muted rounded-md transition-colors font-medium">
                Projects
              </Link>
              <Link href="/approvals" className="px-3 py-2 hover:bg-muted rounded-md transition-colors font-medium">
                Approvals
              </Link>
              <Link href="/settings" className="px-3 py-2 hover:bg-muted rounded-md transition-colors font-medium">
                Settings
              </Link>
            </nav>
          </aside>
          <main className="flex-1 overflow-y-auto p-8">
            {children}
          </main>
        </div>
        <Toaster />
      </body>
    </html>
  );
}
