import type { Metadata } from "next";

import "./globals.css";

export const metadata: Metadata = {
  title: "mini OpenClaw",
  description: "Transparent file-first local AI agent"
};

export default function RootLayout({
  children
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="zh-CN">
      <body>{children}</body>
    </html>
  );
}
