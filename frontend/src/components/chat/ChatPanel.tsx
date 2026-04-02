"use client";

import { useAppStore } from "@/lib/store";

import { ChatInput } from "./ChatInput";
import { ChatMessage } from "./ChatMessage";

export function ChatPanel() {
  const { messages, sendMessage, isStreaming } = useAppStore();

  return (
    <div className="flex h-full flex-col bg-transparent">
      <div className="flex-1 overflow-hidden">
        <div className="scrollbar-thin flex h-full flex-col gap-6 overflow-y-auto px-8 py-8">
          {messages.length === 0 ? (
            <div className="mx-auto mt-20 max-w-2xl rounded-[24px] border border-dashed border-slate-200 bg-white/70 p-10 text-center text-slate-500">
              从左侧选择一个会话，或者直接在底部输入消息开始。
            </div>
          ) : (
            messages.map((message) => <ChatMessage key={message.id} message={message} />)
          )}
        </div>
      </div>
      <ChatInput disabled={isStreaming} onSubmit={sendMessage} />
    </div>
  );
}
