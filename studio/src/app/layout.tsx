import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "FitGround — Technical Designer Workspace",
  description: "What should change in the next sample?",
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en">
      <body className="antialiased">{children}</body>
    </html>
  );
}
