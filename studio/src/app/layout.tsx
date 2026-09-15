import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "FitGround — 下一版样衣该改什么？",
  description: "技术设计师下一版修正工作台。中文 / English 一键切换。What should change in the next sample?",
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="zh">
      <body className="antialiased">{children}</body>
    </html>
  );
}
