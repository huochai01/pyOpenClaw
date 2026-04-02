"use client";

import { Brain, Database, MessageSquarePlus, MessageSquareText, Trash2, Wrench } from "lucide-react";

import { useAppStore } from "@/lib/store";

export function Sidebar() {
  const {
    sessions,
    currentSessionId,
    loadSession,
    createNewSession,
    ragEnabled,
    toggleRagMode,
    compressCurrentSession,
    tokenStats,
    deleteExistingSession
  } = useAppStore();

  return (
    <div className="flex h-full flex-col bg-white/82">
      <div className="p-4">
        <button
          className="flex h-11 w-full items-center justify-center gap-2 rounded-xl bg-[var(--accent-strong)] px-4 text-base font-medium text-white shadow-[0_8px_30px_rgba(101,116,247,0.28)]"
          onClick={() => void createNewSession()}
        >
          <MessageSquarePlus size={16} />
          新会话
        </button>

        <div className="mt-4 flex items-center justify-center gap-10 border-b border-slate-200/80 pb-4 text-sm text-slate-600">
          <button className="flex items-center gap-2 hover:text-slate-900" onClick={() => void compressCurrentSession()}>
            <Wrench size={15} />
            压缩
          </button>
          <label className="flex cursor-pointer items-center gap-2 hover:text-slate-900">
            <Database size={15} />
            RAG
            <input type="checkbox" checked={ragEnabled} onChange={(event) => void toggleRagMode(event.target.checked)} />
          </label>
        </div>
      </div>

      <div className="scrollbar-thin flex-1 overflow-y-auto px-2 pb-4">
        <div className="space-y-1 px-2">
          {sessions.map((session) => (
            <div
              key={session.id}
              className={`group flex items-start gap-2 rounded-xl px-3 py-3 transition ${
                currentSessionId === session.id ? "bg-[#eef2ff] text-[var(--accent-strong)]" : "hover:bg-slate-50"
              }`}
            >
              <button className="flex min-w-0 flex-1 items-start gap-3 text-left" onClick={() => void loadSession(session.id)}>
                <MessageSquareText size={16} className="mt-0.5 shrink-0" />
                <div className="min-w-0">
                  <div className="truncate text-base font-medium">{session.title}</div>
                  <div className="mt-1 text-sm text-slate-400">
                    {new Date((session.updated_at || session.created_at) * 1000).toLocaleString("zh-CN", {
                      month: "2-digit",
                      day: "2-digit",
                      hour: "2-digit",
                      minute: "2-digit"
                    })}
                  </div>
                </div>
              </button>
              <button
                className="mt-0.5 rounded-md p-1.5 text-slate-400 opacity-0 transition hover:bg-white hover:text-rose-500 group-hover:opacity-100"
                onClick={() => void deleteExistingSession(session.id)}
                title="删除会话"
              >
                <Trash2 size={14} />
              </button>
            </div>
          ))}
        </div>
      </div>

      <div className="border-t border-slate-200/80 px-4 py-4 text-sm text-slate-500">
        <div className="mb-3 flex items-center gap-2 font-medium text-slate-700">
          <Brain size={16} />
          系统统计
        </div>
        <div className="space-y-2">
          <div className="flex items-center justify-between">
            <span>System</span>
            <span>{tokenStats?.system_tokens ?? "-"}</span>
          </div>
          <div className="flex items-center justify-between">
            <span>Messages</span>
            <span>{tokenStats?.message_tokens ?? "-"}</span>
          </div>
          <div className="flex items-center justify-between font-medium text-slate-700">
            <span>Total</span>
            <span>{tokenStats?.total_tokens ?? "-"}</span>
          </div>
        </div>
      </div>
    </div>
  );
}
