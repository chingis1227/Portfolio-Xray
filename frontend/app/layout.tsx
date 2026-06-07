import type { Metadata } from "next";
import type { ReactNode } from "react";
import "../styles/globals.css";
import { AppShell } from "@/components/layout/AppShell";

export const metadata: Metadata = {
  title: "Portfolio MRI Decision Room",
  description: "Diagnosis-first portfolio decision-support room."
};

export default function RootLayout({ children }: { children: ReactNode }) {
  return (
    <html lang="en">
      <body>
        <AppShell>{children}</AppShell>
      </body>
    </html>
  );
}
