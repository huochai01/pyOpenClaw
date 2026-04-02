"use client";

import { LoaderCircle, SendHorizontal } from "lucide-react";
import { useLayoutEffect, useRef, useState } from "react";

type ChatInputProps = {
  disabled?: boolean;
  onSubmit: (value: string) => Promise<void>;
};

export function ChatInput({ disabled, onSubmit }: ChatInputProps) {
  const [value, setValue] = useState("");
  const textareaRef = useRef<HTMLTextAreaElement | null>(null);

  useLayoutEffect(() => {
    const textarea = textareaRef.current;
    if (!textarea) return;
    textarea.style.height = "48px";
    const nextHeight = Math.min(textarea.scrollHeight, 48 * 3);
    textarea.style.height = `${Math.max(48, nextHeight)}px`;
    textarea.style.overflowY = textarea.scrollHeight > 48 * 3 ? "auto" : "hidden";
  }, [value]);

  return (
    <form
      className="border-t border-slate-200/80 bg-white/78 px-7 py-4"
      onSubmit={async (event) => {
        event.preventDefault();
        const next = value.trim();
        if (!next || disabled) return;
        setValue("");
        await onSubmit(next);
      }}
    >
      <div className="flex items-end gap-3">
        <textarea
          ref={textareaRef}
          className="scrollbar-thin h-[48px] min-h-[48px] max-h-[144px] flex-1 resize-none overflow-y-hidden rounded-[16px] border border-slate-200 bg-[#f7f8fd] px-5 py-[11px] pr-5 text-[15px] leading-6 outline-none focus:border-[var(--accent-strong)] focus:bg-white"
          placeholder="输入消息，Shift+Enter 换行..."
          value={value}
          onChange={(event) => setValue(event.target.value)}
        />
        <button
          className="flex h-[48px] w-[48px] items-center justify-center rounded-[14px] bg-[var(--accent-strong)] text-lg font-medium text-white shadow-[0_10px_30px_rgba(101,116,247,0.3)] disabled:cursor-not-allowed disabled:opacity-50"
          type="submit"
          disabled={disabled}
        >
          {disabled ? <LoaderCircle size={18} className="animate-spin" /> : <SendHorizontal size={18} />}
        </button>
      </div>
    </form>
  );
}
