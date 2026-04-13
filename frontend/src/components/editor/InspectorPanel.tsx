"use client";

import Editor from "@monaco-editor/react";
import { FileText, Save, Trash2, Upload } from "lucide-react";
import { useMemo, useRef, useState, type ChangeEvent } from "react";

import { useAppStore } from "@/lib/store";

type FileTab = "prompt" | "skills" | "memory" | "knowledge";

export function InspectorPanel() {
  const {
    selectedFile,
    fileContent,
    setFileContent,
    persistFile,
    selectFile,
    skills,
    knowledgeFiles,
    isFileDirty,
    uploadKnowledge,
    removeKnowledge
  } = useAppStore();
  const [activeTab, setActiveTab] = useState<FileTab>("skills");
  const [isUploading, setIsUploading] = useState(false);
  const fileInputRef = useRef<HTMLInputElement | null>(null);

  const files = useMemo(() => {
    if (activeTab === "prompt") {
      return ["workspace/SOUL.md", "workspace/IDENTITY.md", "workspace/USER.md", "workspace/AGENTS.md"];
    }
    if (activeTab === "memory") {
      return ["memory/MEMORY.md"];
    }
    if (activeTab === "knowledge") {
      return knowledgeFiles.map((file) => file.path);
    }
    return skills.map((skill) => skill.path);
  }, [activeTab, knowledgeFiles, skills]);

  const handleUpload = async (event: ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0];
    if (!file) {
      return;
    }

    setIsUploading(true);
    try {
      await uploadKnowledge(file);
      setActiveTab("knowledge");
    } finally {
      setIsUploading(false);
      event.target.value = "";
    }
  };

  return (
    <div className="flex h-full flex-col bg-white/82">
      <div className="border-b border-slate-200/80 px-4 py-3">
        <div className="flex flex-col gap-3">
          <div className="flex gap-2">
            <TabButton label="Prompt" active={activeTab === "prompt"} onClick={() => setActiveTab("prompt")} />
            <TabButton label="Skills" active={activeTab === "skills"} onClick={() => setActiveTab("skills")} />
            <TabButton label="Memory" active={activeTab === "memory"} onClick={() => setActiveTab("memory")} />
            <TabButton label="Knowledge" active={activeTab === "knowledge"} onClick={() => setActiveTab("knowledge")} />
          </div>
          {activeTab === "knowledge" ? (
            <div className="flex">
              <input
                ref={fileInputRef}
                type="file"
                accept=".md,.txt,.json"
                className="hidden"
                onChange={(event) => void handleUpload(event)}
              />
              <button
                className="inline-flex w-full items-center justify-center gap-2 rounded-xl border border-dashed border-slate-300 bg-slate-50 px-3 py-2.5 text-sm font-medium text-slate-600 transition hover:border-[var(--accent-strong)] hover:bg-white hover:text-slate-900 disabled:cursor-not-allowed disabled:opacity-60"
                disabled={isUploading}
                onClick={() => fileInputRef.current?.click()}
              >
                <Upload size={14} />
                {isUploading ? "上传中..." : "上传知识"}
              </button>
            </div>
          ) : null}
        </div>
      </div>

      <div className="scrollbar-thin overflow-y-auto border-b border-slate-200/80 bg-white/70 px-3 py-3 text-[15px]">
        <div className="space-y-1">
          {activeTab === "knowledge" && files.length === 0 ? (
            <div className="rounded-lg border border-dashed border-slate-200 bg-white/70 px-3 py-4 text-sm text-slate-500">
              还没有知识文件。支持上传 `.md`、`.txt`、`.json`，上传后会立即重建知识索引。
            </div>
          ) : null}
          {files.map((file) => (
            <div
              key={file}
              className={`group flex items-center gap-2 rounded-lg px-2 py-2 ${
                selectedFile === file ? "bg-[#eef2ff] text-[var(--accent-strong)]" : "hover:bg-slate-50"
              }`}
            >
              <button className="flex min-w-0 flex-1 items-center gap-2 text-left" onClick={() => void selectFile(file)}>
                <FileText size={15} />
                <span className="truncate">{file}</span>
              </button>
              {activeTab === "knowledge" ? (
                <button
                  className="rounded-md p-1 text-slate-400 opacity-0 transition hover:bg-white hover:text-rose-500 group-hover:opacity-100"
                  title="删除知识文件"
                  onClick={(event) => {
                    event.stopPropagation();
                    void removeKnowledge(file);
                  }}
                >
                  <Trash2 size={14} />
                </button>
              ) : null}
            </div>
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
          language={selectedFile.endsWith(".json") ? "json" : selectedFile.endsWith(".txt") ? "plaintext" : "markdown"}
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
