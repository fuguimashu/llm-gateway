import type { Metadata } from "next";
import "./globals.css";
import { Nav } from "@/components/nav";
import { AuthGate } from "@/components/auth-gate";

export const metadata: Metadata = {
  title: "LLM Gateway",
  description: "Minimal, auditable LLM proxy dashboard",
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en" suppressHydrationWarning>
      <body className="min-h-screen bg-ink-900 text-cream antialiased">
        <AuthGate>
          <div className="flex h-screen overflow-hidden">
            <Nav />
            <main className="flex-1 overflow-y-auto bg-ink-900">
              <div className="p-6 md:p-8 max-w-7xl mx-auto">
                {children}
              </div>
            </main>
          </div>
        </AuthGate>
      </body>
    </html>
  );
}
