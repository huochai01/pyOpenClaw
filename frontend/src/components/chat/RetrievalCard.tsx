import type { RetrievalItem } from "@/lib/store";

type RetrievalCardProps = {
  items: RetrievalItem[];
};

export function RetrievalCard({ items }: RetrievalCardProps) {
  if (!items.length) return null;

  return (
    <details className="rounded-2xl border border-[var(--accent)]/20 bg-[var(--accent)]/5 p-3">
      <summary className="cursor-pointer text-sm font-medium text-[var(--accent-strong)]">记忆检索结果</summary>
      <div className="mt-3 space-y-3 text-sm text-slate-700">
        {items.map((item, index) => (
          <div key={`${item.source}-${index}`} className="rounded-xl bg-white/70 p-3">
            <div className="mb-1 text-xs text-slate-500">
              {item.source} · score {item.score.toFixed(3)}
            </div>
            <div className="whitespace-pre-wrap">{item.text}</div>
          </div>
        ))}
      </div>
    </details>
  );
}
