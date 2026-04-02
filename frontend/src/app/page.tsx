"use client";

import { ChatPanel } from "@/components/chat/ChatPanel";
import { InspectorPanel } from "@/components/editor/InspectorPanel";
import { Navbar } from "@/components/layout/Navbar";
import { ResizeHandle } from "@/components/layout/ResizeHandle";
import { Sidebar } from "@/components/layout/Sidebar";
import { AppProvider, useAppStore } from "@/lib/store";

function Shell() {
  const { sidebarWidth, inspectorWidth, setSidebarWidth, setInspectorWidth } = useAppStore();

  return (
    <div className="app-shell bg-transparent text-slate-900">
      <Navbar />
      <main className="flex h-[calc(100vh-56px)] gap-0">
        <div className="flex shrink-0 flex-col overflow-hidden border-r border-slate-200/90 bg-white/70" style={{ width: sidebarWidth }}>
          <Sidebar />
        </div>
        <ResizeHandle onResize={setSidebarWidth} side="left" />
        <div className="min-w-0 flex-1 overflow-hidden bg-white/35">
          <ChatPanel />
        </div>
        <ResizeHandle onResize={setInspectorWidth} side="right" />
        <div className="flex shrink-0 flex-col overflow-hidden border-l border-slate-200/90 bg-white/78" style={{ width: inspectorWidth }}>
          <InspectorPanel />
        </div>
      </main>
    </div>
  );
}

export default function HomePage() {
  return (
    <AppProvider>
      <Shell />
    </AppProvider>
  );
}
