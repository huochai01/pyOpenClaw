import { Bot, UserRound } from "lucide-react";
import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";

import type { ChatMessage as ChatMessageType } from "@/lib/store";

import { RetrievalCard } from "./RetrievalCard";
import { ThoughtChain } from "./ThoughtChain";

type ChatMessageProps = {
  message: ChatMessageType;
};

export function ChatMessage({ message }: ChatMessageProps) {
  const isUser = message.role === "user";

  return (
    <div className={`flex ${isUser ? "justify-end" : "justify-start"}`}>
      <div className={`flex max-w-4xl items-start gap-4 ${isUser ? "flex-row-reverse" : ""}`}>
        <div
          className={`mt-1 flex h-10 w-10 shrink-0 items-center justify-center rounded-full ${
            isUser ? "bg-[var(--accent-strong)] text-white" : "bg-slate-100 text-slate-600"
          }`}
        >
          {isUser ? <UserRound size={18} /> : <Bot size={18} />}
        </div>
        <div className="space-y-3">
          {!isUser && <RetrievalCard items={message.retrievals} />}
          {!isUser && <ThoughtChain toolCalls={message.toolCalls} />}
          <div
            className={`rounded-[22px] px-5 py-4 shadow-sm ${
              isUser ? "bg-[var(--accent-strong)] text-white" : "border border-slate-200 bg-[#f3f5fb] text-slate-800"
            }`}
          >
            {message.content ? (
              <div className={`prose prose-sm max-w-none ${isUser ? "prose-invert" : "prose-slate"}`}>
                <ReactMarkdown remarkPlugins={[remarkGfm]}>{message.content}</ReactMarkdown>
              </div>
            ) : (
              <div className="text-sm text-slate-400">...</div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}
