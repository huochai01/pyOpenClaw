"use client";

import { AlertTriangle } from "lucide-react";
import { useEffect } from "react";

type ConfirmDialogProps = {
  open: boolean;
  title: string;
  description: string;
  confirmLabel: string;
  cancelLabel?: string;
  tone?: "danger" | "primary";
  busy?: boolean;
  onCancel: () => void;
  onConfirm: () => void;
};

export function ConfirmDialog({
  open,
  title,
  description,
  confirmLabel,
  cancelLabel = "取消",
  tone = "primary",
  busy = false,
  onCancel,
  onConfirm
}: ConfirmDialogProps) {
  useEffect(() => {
    if (!open) {
      return;
    }

    const handleKeyDown = (event: KeyboardEvent) => {
      if (event.key === "Escape" && !busy) {
        onCancel();
      }
    };

    window.addEventListener("keydown", handleKeyDown);
    return () => window.removeEventListener("keydown", handleKeyDown);
  }, [busy, onCancel, open]);

  if (!open) {
    return null;
  }

  const confirmClassName =
    tone === "danger"
      ? "bg-rose-500 text-white shadow-[0_16px_32px_rgba(244,63,94,0.24)] hover:bg-rose-600"
      : "bg-[var(--accent-strong)] text-white shadow-[0_16px_32px_rgba(101,116,247,0.28)] hover:bg-[var(--accent)]";

  return (
    <div className="fixed inset-0 z-[80] flex items-center justify-center bg-slate-950/38 px-4">
      <div className="w-full max-w-md rounded-[28px] border border-slate-200 bg-white p-6 shadow-[0_28px_80px_rgba(15,23,42,0.2)]">
        <div className="flex items-start gap-4">
          <div className="flex h-11 w-11 shrink-0 items-center justify-center rounded-2xl bg-slate-100 text-slate-700">
            <AlertTriangle size={20} />
          </div>
          <div className="min-w-0">
            <h2 className="text-lg font-semibold text-slate-900">{title}</h2>
            <p className="mt-2 text-sm leading-6 text-slate-500">{description}</p>
          </div>
        </div>

        <div className="mt-6 flex items-center justify-end gap-3">
          <button
            className="rounded-xl border border-slate-200 bg-white px-4 py-2.5 text-sm font-medium text-slate-600 transition hover:border-slate-300 hover:text-slate-900 disabled:cursor-not-allowed disabled:opacity-60"
            disabled={busy}
            onClick={onCancel}
          >
            {cancelLabel}
          </button>
          <button
            className={`rounded-xl px-4 py-2.5 text-sm font-medium transition disabled:cursor-wait disabled:opacity-70 ${confirmClassName}`}
            disabled={busy}
            onClick={onConfirm}
          >
            {busy ? "处理中..." : confirmLabel}
          </button>
        </div>
      </div>
    </div>
  );
}
