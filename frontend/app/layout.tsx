import type { Metadata } from "next";
import type { ReactNode } from "react";
import { DM_Sans, IBM_Plex_Mono } from "next/font/google";
import "../styles/globals.css";
import { AppShell } from "@/components/layout/AppShell";
import { ReviewStateProvider } from "@/lib/reviewState";
import { SupabaseAuthProvider } from "@/lib/supabase/auth";
import { SupabasePersistenceProvider } from "@/lib/supabase/persistence";

const dmSans = DM_Sans({
  subsets: ["latin"],
  display: "swap",
  weight: ["400"],
  variable: "--font-pmri-sans"
});

const plexMono = IBM_Plex_Mono({
  subsets: ["latin"],
  display: "swap",
  weight: ["400"],
  variable: "--font-pmri-mono"
});

export const metadata: Metadata = {
  title: "Portfolio MRI Decision Room",
  description: "Diagnosis-first portfolio decision-support room."
};

export default function RootLayout({ children }: { children: ReactNode }) {
  return (
    <html lang="en" className={`${dmSans.variable} ${plexMono.variable}`}>
      <body>
        <SupabaseAuthProvider>
          <SupabasePersistenceProvider>
            <ReviewStateProvider>
              <AppShell>{children}</AppShell>
            </ReviewStateProvider>
          </SupabasePersistenceProvider>
        </SupabaseAuthProvider>
      </body>
    </html>
  );
}

