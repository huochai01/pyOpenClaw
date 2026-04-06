import { Github } from "lucide-react";

export function Navbar() {
  return (
    <header className="sticky top-0 z-20 border-b border-slate-200/80 bg-white/85 backdrop-blur">
      <div className="flex h-14 items-center justify-between px-5">
        <div className="text-[18px] font-semibold tracking-tight text-slate-950">
          mini OpenClaw <span className="ml-1 text-sm">🦀</span>
        </div>
        <a
          className="inline-flex items-center gap-2 rounded-full px-3 py-2 text-sm text-slate-600 transition hover:bg-slate-100 hover:text-slate-900"
          href="https://github.com/huochai01/pyOpenClaw"
          target="_blank"
          rel="noreferrer"
        >
          <Github size={16} />
          代码仓库
        </a>
      </div>
    </header>
  );
}
