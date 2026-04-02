import type { ToolCall } from "@/lib/store";

type ThoughtChainProps = {
  toolCalls: ToolCall[];
};

export function ThoughtChain({ toolCalls }: ThoughtChainProps) {
  if (!toolCalls.length) return null;

  return (
    <details className="rounded-2xl border border-slate-200 bg-white/88 p-3">
      <summary className="cursor-pointer text-sm font-medium text-slate-700">工具调用链</summary>
      <div className="mt-3 space-y-3">
        {toolCalls.map((tool, index) => (
          <div key={`${tool.tool}-${index}`} className="rounded-xl bg-slate-50 p-3 text-sm">
            <div className="font-medium text-slate-900">{tool.tool}</div>
            <pre className="mt-2 overflow-x-auto whitespace-pre-wrap text-xs text-slate-600">
              {JSON.stringify(tool.input, null, 2)}
            </pre>
            {tool.output !== undefined ? (
              <pre className="mt-2 overflow-x-auto whitespace-pre-wrap text-xs text-slate-700">
                {typeof tool.output === "string" ? tool.output : JSON.stringify(tool.output, null, 2)}
              </pre>
            ) : null}
          </div>
        ))}
      </div>
    </details>
  );
}
