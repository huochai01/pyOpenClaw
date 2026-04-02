"use client";

import Editor from "@monaco-editor/react";
import { FileText, Save } from "lucide-react";
import { useMemo, useState } from "react";

import { useAppStore } from "@/lib/store";

type FileTab = "prompt" | "skills" | "memory";

export function InspectorPanel() {
  const { selectedFile, fileContent, setFileContent, persistFile, selectFile, skills, isFileDirty } = useAppStore();
  const [activeTab, setActiveTab] = useState<FileTab>("skills");

  const files = useMemo(() => {
    if (activeTab === "prompt") {
      return ["workspace/SOUL.md", "workspace/IDENTITY.md", "workspace/USER.md", "workspace/AGENTS.md"];
    }
    if (activeTab === "memory") {
      return ["memory/MEMORY.md"];
    }
    return skills.map((skill) => skill.path);
  }, [activeTab, skills]);

  return (
    <div className="flex h-full flex-col bg-white/82">
      <div className="border-b border-slate-200/80 px-4 py-3">
        <div className="flex gap-2">
          <TabButton label="Prompt" active={activeTab === "prompt"} onClick={() => setActiveTab("prompt")} />
          <TabButton label="Skills" active={activeTab === "skills"} onClick={() => setActiveTab("skills")} />
          <TabButton label="Memory" active={activeTab === "memory"} onClick={() => setActiveTab("memory")} />
        </div>
      </div>

      <div className="scrollbar-thin overflow-y-auto border-b border-slate-200/80 bg-white/70 px-3 py-3 text-[15px]">
        <div className="space-y-1">
          {files.map((file) => (
            <button
              key={file}
              className={`flex w-full items-center gap-2 rounded-lg px-2 py-2 text-left ${
                selectedFile === file ? "bg-[#eef2ff] text-[var(--accent-strong)]" : "hover:bg-slate-50"
              }`}
              onClick={() => void selectFile(file)}
            >
              <FileText size={15} />
              <span className="truncate">{file}</span>
            </button>
          ))}
        </div>
      </div>

      <div className="flex items-center justify-between border-b border-slate-200/80 px-4 py-3 text-sm text-slate-600">
        <div className="truncate">{selectedFile}</div>
        <button
          className={`inline-flex items-center gap-1 rounded-lg px-3 py-1.5 font-medium text-white transition ${
            isFileDirty ? "bg-[var(--accent-strong)] shadow-[0_8px_24px_rgba(101,116,247,0.26)]" : "bg-[#b7befd]"
          }`}
          onClick={() => void persistFile()}
        >
          <Save size={14} />
          保存
        </button>
      </div>

      <div className="min-h-0 flex-1 bg-white">
        <Editor
          theme="vs"
          language={selectedFile.endsWith(".json") ? "json" : "markdown"}
          value={fileContent}
          onChange={(value) => setFileContent(value ?? "")}
          options={{
            minimap: { enabled: false },
            fontSize: 13,
            wordWrap: "on",
            scrollBeyondLastLine: false,
            automaticLayout: true
          }}
        />
      </div>
    </div>
  );
}

type TabButtonProps = {
  label: string;
  active: boolean;
  onClick: () => void;
};

function TabButton({ label, active, onClick }: TabButtonProps) {
  return (
    <button
      className={`rounded-lg px-3 py-1.5 text-sm font-medium transition ${
        active ? "bg-[var(--accent-strong)] text-white" : "bg-slate-100 text-slate-600 hover:bg-slate-200"
      }`}
      onClick={onClick}
    >
      {label}
    </button>
  );
}
